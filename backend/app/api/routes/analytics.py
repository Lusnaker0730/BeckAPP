from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import Optional
import calendar
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.cache import cache_result  # Redis caching support
from app.models.fhir_resources import Patient, Condition, Encounter, Observation
from app.models.etl_job import ETLJob

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/etl-jobs-list")
async def get_etl_jobs_list(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of completed ETL jobs for filtering"""
    jobs = db.query(ETLJob).filter(
        ETLJob.status == "completed"
    ).order_by(ETLJob.created_at.desc()).limit(50).all()
    
    job_list = []
    for job in jobs:
        job_list.append({
            "job_id": job.job_id,
            "resource_type": job.resource_type,
            "start_time": job.start_time.isoformat() if job.start_time else None,
            "records_processed": job.records_processed or 0
        })
    
    return job_list

@router.get("/available-diagnoses")
@cache_result(expire_seconds=600, key_prefix="available_diagnoses")  # Cache for 10 minutes
async def get_available_diagnoses(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of diagnoses to return")
):
    """Get list of unique diagnoses available in the database (cached for 10 minutes)"""
    
    # Query unique condition codes and descriptions
    results = db.query(
        Condition.code_text,
        func.count(Condition.id).label('count')
    ).filter(
        Condition.code_text.isnot(None)
    ).group_by(Condition.code_text).order_by(
        func.count(Condition.id).desc()
    ).limit(limit).all()
    
    diagnoses = []
    for row in results:
        if row.code_text:
            diagnoses.append({
                "code_text": row.code_text,
                "count": row.count
            })
    
    return diagnoses

@router.get("/diagnosis-by-code")
async def get_diagnosis_by_code(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    code: str = Query(..., description="SNOMED-CT or ICD-10 code to search for"),
    timeRange: str = Query("yearly", description="Time range: monthly, quarterly, yearly"),
    periods: int = Query(None, ge=1, le=20, description="Number of periods"),
    startYear: int = Query(None, ge=1900, le=2100, description="Start year for analysis"),
    endYear: int = Query(None, ge=1900, le=2100, description="End year for analysis")
):
    """Get diagnosis analysis by specific code (SNOMED-CT or ICD-10)"""
    
    from sqlalchemy import or_, cast, String
    
    # Build query to search for specific code in JSON structure
    # FHIR code structure: {"coding": [{"system": "...", "code": "...", "display": "..."}], "text": "..."}
    # IMPORTANT: Code matching should be EXACT, not fuzzy
    query = db.query(Condition).filter(
        # Search for exact code match in JSON using pattern: "code":"38341003"
        # This ensures we match the exact code value, not partial matches
        cast(Condition.code, String).ilike(f'%"code": "{code}"%')
    )
    
    # Determine time grouping
    if timeRange == "monthly":
        trunc_format = 'month'
        default_periods = 12
        delta_days = 30
    elif timeRange == "quarterly":
        trunc_format = 'quarter'
        default_periods = 8
        delta_days = 90
    else:  # yearly
        trunc_format = 'year'
        default_periods = 5
        delta_days = 365
    
    # Use custom year range if provided, otherwise use periods
    if startYear is not None and endYear is not None:
        start_date = datetime(startYear, 1, 1)
        end_date = datetime(endYear, 12, 31, 23, 59, 59)
        # Calculate number of periods based on year range
        if timeRange == "monthly":
            num_periods = (endYear - startYear + 1) * 12
        elif timeRange == "quarterly":
            num_periods = (endYear - startYear + 1) * 4
        else:  # yearly
            num_periods = endYear - startYear + 1
    else:
        end_date = datetime.now()
        num_periods = periods if periods is not None else default_periods
        start_date = end_date - timedelta(days=delta_days * num_periods)
    
    # Query actual data
    results = query.filter(
        Condition.onset_datetime >= start_date,
        Condition.onset_datetime <= end_date
    ).with_entities(
        func.date_trunc(trunc_format, Condition.onset_datetime).label('period'),
        func.count(Condition.id).label('count')
    ).group_by('period').order_by('period').all()
    
    # Format results
    period_counts = {}
    for row in results:
        if row.period:
            if timeRange == "monthly":
                key = row.period.strftime('%Y-%m')
            elif timeRange == "quarterly":
                key = f"Q{((row.period.month-1)//3) + 1} {row.period.year}"
            else:  # yearly
                key = str(row.period.year)
            period_counts[key] = row.count
    
    # Generate all periods
    labels = []
    counts = []
    
    for i in range(num_periods):
        date = end_date - timedelta(days=delta_days * i)
        if timeRange == "monthly":
            label = date.strftime('%Y-%m')
        elif timeRange == "quarterly":
            label = f"Q{((date.month-1)//3) + 1} {date.year}"
        else:  # yearly
            label = str(date.year)
        labels.insert(0, label)
        counts.insert(0, period_counts.get(label, 0))
    
    # Calculate statistics
    total_count = sum(counts)
    average_count = total_count // len(counts) if counts else 0
    peak_count = max(counts) if counts else 0
    growth_rate = ((counts[-1] - counts[0]) / counts[0] * 100) if counts and counts[0] > 0 else 0
    
    # Generate detailed data
    details = []
    for i, (period, count) in enumerate(zip(labels, counts)):
        change = ((count - counts[i-1]) / counts[i-1] * 100) if i > 0 and counts[i-1] > 0 else 0
        percentage = (count / total_count * 100) if total_count > 0 else 0
        details.append({
            "period": period,
            "count": count,
            "change": round(change, 2),
            "percentage": round(percentage, 2)
        })
    
    # Get the actual diagnosis name from the first matched record
    diagnosis_name = code  # Default to the code itself
    if total_count > 0:
        # Use raw SQL to avoid ORM issues with missing columns
        try:
            from sqlalchemy import text as sql_text
            # Use exact code matching to get diagnosis name
            sql = sql_text("""
                SELECT code_text 
                FROM conditions 
                WHERE CAST(code AS VARCHAR) ILIKE :json_pattern
                AND onset_datetime >= :start_date 
                AND onset_datetime <= :end_date
                LIMIT 1
            """)
            result = db.execute(sql, {
                'json_pattern': f'%"code": "{code}"%',
                'start_date': start_date,
                'end_date': end_date
            })
            row = result.fetchone()
            if row and row[0]:
                diagnosis_name = row[0]
        except Exception as e:
            logger.warning(f"Could not fetch diagnosis name: {e}")
            # Continue with default diagnosis name (code itself)
    
    return {
        "code": code,
        "diagnosisName": diagnosis_name,  # Add the actual diagnosis name
        "labels": labels,
        "counts": counts,
        "totalCount": total_count,
        "averageCount": average_count,
        "peakCount": peak_count,
        "growthRate": round(growth_rate, 2),
        "details": details
    }

@router.get("/stats")
async def get_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    job_id: Optional[str] = Query(None, description="Filter by specific ETL job ID")
):
    """Get overall statistics with optional job filtering"""
    
    # Base queries
    patient_query = db.query(func.count(Patient.id))
    condition_query = db.query(func.count(Condition.id))
    encounter_query = db.query(func.count(Encounter.id))
    observation_query = db.query(func.count(Observation.id))
    
    # Apply job filter if specified
    if job_id:
        etl_job = db.query(ETLJob).filter(ETLJob.job_id == job_id).first()
        if not etl_job:
            # Invalid job_id, return empty results
            patient_query = patient_query.filter(Patient.id == None)
            condition_query = condition_query.filter(Condition.id == None)
            encounter_query = encounter_query.filter(Encounter.id == None)
            observation_query = observation_query.filter(Observation.id == None)
        else:
            # Filter by job_id
            patient_query = patient_query.filter(Patient.job_id == job_id)
            condition_query = condition_query.filter(Condition.job_id == job_id)
            encounter_query = encounter_query.filter(Encounter.job_id == job_id)
            observation_query = observation_query.filter(Observation.job_id == job_id)
    
    total_patients = patient_query.scalar() or 0
    total_conditions = condition_query.scalar() or 0
    total_encounters = encounter_query.scalar() or 0
    total_observations = observation_query.scalar() or 0
    
    return {
        "totalPatients": total_patients,
        "totalConditions": total_conditions,
        "totalEncounters": total_encounters,
        "totalObservations": total_observations
    }

@router.get("/trends")
async def get_trends(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    months: int = Query(None, ge=1, le=120, description="Number of months to show (deprecated, use start_year/end_year)"),
    start_year: int = Query(None, ge=2000, le=2100, description="Start year for trend analysis"),
    end_year: int = Query(None, ge=2000, le=2100, description="End year for trend analysis"),
    job_id: Optional[str] = Query(None, description="Filter by specific ETL job ID")
):
    """Get trend data for specified year range or last N months"""
    
    # Determine date range
    if start_year and end_year:
        # Use year range
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31, 23, 59, 59)
    elif months:
        # Use months (backward compatibility)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)
    else:
        # Default: last 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
    
    # Build query
    query = db.query(
        func.date_trunc('month', Condition.onset_datetime).label('month'),
        func.count(Condition.id).label('count')
    ).filter(
        Condition.onset_datetime >= start_date,
        Condition.onset_datetime <= end_date
    )
    
    # Apply job filter if specified
    if job_id:
        query = query.filter(Condition.job_id == job_id)
    
    results = query.group_by('month').order_by('month').all()
    
    # Format results
    labels = []
    values = []
    for row in results:
        if row.month:
            labels.append(row.month.strftime('%Y-%m'))
            values.append(row.count)
    
    # If no data, return empty (don't generate fake data for medical software)
    if not labels:
        labels = []
        values = []
    
    return {
        "labels": labels,
        "values": values
    }

@router.get("/top-conditions")
@cache_result(expire_seconds=600, key_prefix="top_conditions")  # Cache for 10 minutes
async def get_top_conditions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(5, ge=1, le=20),
    job_id: Optional[str] = Query(None, description="Filter by specific ETL job ID"),
    start_year: int = Query(None, ge=2000, le=2100, description="Start year for filtering"),
    end_year: int = Query(None, ge=2000, le=2100, description="End year for filtering")
):
    """Get top N conditions by frequency with optional year range filtering (cached for 10 minutes)"""
    query = db.query(
        Condition.code_text,
        func.count(Condition.id).label('count')
    ).filter(
        Condition.code_text.isnot(None)
    )
    
    # Apply year range filter if specified
    if start_year and end_year:
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31, 23, 59, 59)
        query = query.filter(
            Condition.onset_datetime >= start_date,
            Condition.onset_datetime <= end_date
        )
    
    # Apply job filter if specified
    if job_id:
        etl_job = db.query(ETLJob).filter(ETLJob.job_id == job_id).first()
        if not etl_job:
            # Invalid job_id, return empty results
            query = query.filter(Condition.id == None)
        else:
            # Filter by job_id
            query = query.filter(Condition.job_id == job_id)
    
    results = query.group_by(Condition.code_text).order_by(
        func.count(Condition.id).desc()
    ).limit(limit).all()
    
    # Return empty lists if no data (no fake data!)
    if not results:
        return {
            "labels": [],
            "values": []
        }
    
    labels = [row.code_text for row in results]
    values = [row.count for row in results]
    
    return {
        "labels": labels,
        "values": values
    }

@router.get("/diagnosis")
@cache_result(expire_seconds=1800, key_prefix="diagnosis_analysis")  # Cache for 30 minutes
async def get_diagnosis_analysis(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    diagnosis: str = Query(..., description="Diagnosis type"),
    timeRange: str = Query("yearly", description="Time range: monthly, quarterly, yearly"),
    periods: int = Query(None, ge=1, le=20, description="Number of periods to display (default: 12 for monthly, 8 for quarterly, 5 for yearly, max 20)"),
    job_id: Optional[str] = Query(None, description="Filter by specific ETL job ID"),
    startYear: int = Query(None, ge=1900, le=2100, description="Start year for analysis"),
    endYear: int = Query(None, ge=1900, le=2100, description="End year for analysis")
):
    """Get diagnosis analysis data - REAL DATA from database (cached for 30 minutes)"""
    
    # Map diagnosis types to search terms (支持 ICD-10 和 SNOMED-CT)
    diagnosis_search_terms = {
        "influenza": [
            "influenza", "flu",  # Text search
            "J09", "J10", "J11",  # ICD-10
            "6142004", "442438000", "195878008"  # SNOMED-CT codes
        ],
        "myocardial_infarction": [
            "myocardial infarction", "heart attack", 
            "I21", "I22",  # ICD-10
            "22298006", "57054005"  # SNOMED-CT codes
        ],
        "lung_adenocarcinoma": [
            "lung adenocarcinoma", "lung cancer", 
            "C34",  # ICD-10
            "254637007", "93880001"  # SNOMED-CT codes
        ],
        "diabetes": [
            "diabetes", "diabetes mellitus",
            "E10", "E11", "E12", "E13", "E14",  # ICD-10
            "73211009", "44054006", "46635009"  # SNOMED-CT codes
        ],
        "hypertension": [
            "hypertension", "high blood pressure", 
            "I10", "I11", "I12", "I13", "I15",  # ICD-10
            "59621000", "38341003"  # SNOMED-CT codes (59621000=Hypertension, 38341003=Essential hypertension)
        ],
        "copd": [
            "copd", "chronic obstructive", 
            "J44",  # ICD-10
            "13645005", "413846005"  # SNOMED-CT codes
        ]
    }
    
    search_terms = diagnosis_search_terms.get(diagnosis, [])
    
    # Build query to search for conditions matching the diagnosis
    query = db.query(Condition).filter(Condition.code_text.isnot(None))
    
    # Add filters for diagnosis search terms (search in both code_text and code)
    from sqlalchemy import or_, cast, String
    if search_terms:
        # Predefined diagnosis with multiple search terms
        filters = []
        for term in search_terms:
            # For code-like terms (alphanumeric), do exact code matching
            # For text terms, do fuzzy text matching
            if term.replace('-', '').replace('.', '').isalnum():
                # Looks like a code (e.g., "I10", "38341003", "J09")
                filters.append(cast(Condition.code, String).ilike(f'%"code": "{term}"%'))
            else:
                # Text description search (e.g., "influenza", "diabetes")
                filters.append(Condition.code_text.ilike(f"%{term}%"))
                filters.append(cast(Condition.code, String).ilike(f'%"display": "{term}"%'))
        query = query.filter(or_(*filters))
    else:
        # Database diagnosis - search by diagnosis name (fuzzy match for text)
        query = query.filter(
            Condition.code_text.ilike(f"%{diagnosis}%")
        )
    
    # Filter by ETL job if specified
    if job_id:
        etl_job = db.query(ETLJob).filter(ETLJob.job_id == job_id).first()
        if not etl_job:
            # Invalid job_id, return empty results
            query = query.filter(Condition.id == None)
        else:
            # Filter by job_id
            query = query.filter(Condition.job_id == job_id)
    
    # Determine time grouping - with flexible periods
    if timeRange == "monthly":
        trunc_format = 'month'
        default_periods = 12
        delta_days = 30
    elif timeRange == "quarterly":
        trunc_format = 'quarter'
        default_periods = 8
        delta_days = 90
    else:  # yearly
        trunc_format = 'year'
        default_periods = 5
        delta_days = 365
    
    # Use custom year range if provided, otherwise use periods
    if startYear is not None and endYear is not None:
        start_date = datetime(startYear, 1, 1)
        end_date = datetime(endYear, 12, 31, 23, 59, 59)
        # Calculate number of periods based on year range
        if timeRange == "monthly":
            num_periods = (endYear - startYear + 1) * 12
        elif timeRange == "quarterly":
            num_periods = (endYear - startYear + 1) * 4
        else:  # yearly
            num_periods = endYear - startYear + 1
    else:
        end_date = datetime.now()
        num_periods = periods if periods is not None else default_periods
        start_date = end_date - timedelta(days=delta_days * num_periods)
    
    # Query actual data from database
    results = query.filter(
        Condition.onset_datetime >= start_date,
        Condition.onset_datetime <= end_date
    ).with_entities(
        func.date_trunc(trunc_format, Condition.onset_datetime).label('period'),
        func.count(Condition.id).label('count')
    ).group_by('period').order_by('period').all()
    
    # Format results
    period_counts = {}
    for row in results:
        if row.period:
            if timeRange == "monthly":
                key = row.period.strftime('%Y-%m')
            elif timeRange == "quarterly":
                key = f"Q{((row.period.month-1)//3) + 1} {row.period.year}"
            else:  # yearly
                key = str(row.period.year)
            period_counts[key] = row.count
    
    # Generate all periods and fill with actual data or 0
    labels = []
    counts = []
    
    for i in range(num_periods):
        date = end_date - timedelta(days=delta_days * i)
        if timeRange == "monthly":
            label = date.strftime('%Y-%m')
        elif timeRange == "quarterly":
            label = f"Q{((date.month-1)//3) + 1} {date.year}"
        else:  # yearly
            label = str(date.year)
        labels.insert(0, label)
        counts.insert(0, period_counts.get(label, 0))
    
    # Calculate statistics
    total_count = sum(counts)
    average_count = total_count // len(counts) if counts else 0
    peak_count = max(counts) if counts else 0
    growth_rate = ((counts[-1] - counts[0]) / counts[0] * 100) if counts and counts[0] > 0 else 0
    
    # Generate detailed data
    details = []
    for i, (period, count) in enumerate(zip(labels, counts)):
        change = ((count - counts[i-1]) / counts[i-1] * 100) if i > 0 and counts[i-1] > 0 else 0
        percentage = (count / total_count * 100) if total_count > 0 else 0
        details.append({
            "period": period,
            "count": count,
            "change": round(change, 2),
            "percentage": round(percentage, 2)
        })
    
    # Get the actual diagnosis name from the first matched record (for code search mode)
    diagnosis_name = diagnosis  # Default to the input diagnosis
    if total_count > 0 and not search_terms:
        # For database diagnosis mode, get the actual name using raw SQL
        try:
            from sqlalchemy import text as sql_text
            # For database diagnosis mode, use fuzzy text matching
            sql = sql_text("""
                SELECT code_text 
                FROM conditions 
                WHERE code_text ILIKE :diag_pattern
                AND onset_datetime >= :start_date 
                AND onset_datetime <= :end_date
                LIMIT 1
            """)
            result = db.execute(sql, {
                'diag_pattern': f'%{diagnosis}%',
                'start_date': start_date,
                'end_date': end_date
            })
            row = result.fetchone()
            if row and row[0]:
                diagnosis_name = row[0]
        except Exception as e:
            logger.warning(f"Could not fetch diagnosis name: {e}")
            # Continue with default diagnosis name
    
    return {
        "diagnosis": diagnosis,
        "diagnosisName": diagnosis_name,  # Add the actual diagnosis name
        "labels": labels,
        "counts": counts,
        "totalCount": total_count,
        "averageCount": average_count,
        "peakCount": peak_count,
        "growthRate": round(growth_rate, 2),
        "details": details
    }

@router.get("/patient-demographics")
@cache_result(expire_seconds=900, key_prefix="patient_demographics")  # Cache for 15 minutes
async def get_patient_demographics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get patient demographics breakdown - REAL DATA from database"""
    # Gender distribution
    gender_results = db.query(
        Patient.gender,
        func.count(Patient.id).label('count')
    ).filter(
        Patient.gender.isnot(None)
    ).group_by(Patient.gender).all()
    
    gender_labels = []
    gender_values = []
    for row in gender_results:
        gender_labels.append(row.gender.capitalize() if row.gender else "Unknown")
        gender_values.append(row.count)
    
    # Age distribution - calculate from birth_date
    current_year = datetime.now().year
    age_groups = {
        "0-18": 0,
        "19-35": 0,
        "36-50": 0,
        "51-65": 0,
        "65+": 0
    }
    
    patients_with_birthdate = db.query(Patient.birth_date).filter(
        Patient.birth_date.isnot(None)
    ).all()
    
    for patient in patients_with_birthdate:
        if patient.birth_date:
            age = current_year - patient.birth_date.year
            if age <= 18:
                age_groups["0-18"] += 1
            elif age <= 35:
                age_groups["19-35"] += 1
            elif age <= 50:
                age_groups["36-50"] += 1
            elif age <= 65:
                age_groups["51-65"] += 1
            else:
                age_groups["65+"] += 1
    
    return {
        "gender": {
            "labels": gender_labels if gender_labels else [],
            "values": gender_values if gender_values else []
        },
        "ageGroups": {
            "labels": list(age_groups.keys()),
            "values": list(age_groups.values())
        }
    }

@router.get("/recent-activities")
async def get_recent_activities(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50, description="Number of recent activities to return")
):
    """Get recent ETL activities - REAL DATA from database"""
    
    # Query recent ETL jobs
    recent_jobs = db.query(ETLJob).order_by(
        ETLJob.created_at.desc()
    ).limit(limit).all()
    
    activities = []
    for job in recent_jobs:
        # Format time
        time_str = job.start_time.strftime('%Y-%m-%d %H:%M') if job.start_time else job.created_at.strftime('%Y-%m-%d %H:%M')
        
        # Determine activity type and description
        if job.status == "completed":
            activity_type = "ETL"
            description = f"BULK DATA 載入完成 ({job.records_processed or 0} 筆記錄)"
            status_badge = "success"
            status_text = "成功"
        elif job.status == "in-progress":
            activity_type = "ETL"
            description = f"BULK DATA 處理中 ({job.resource_type})"
            status_badge = "info"
            status_text = "進行中"
        elif job.status == "failed":
            activity_type = "ETL"
            description = f"BULK DATA 處理失敗 ({job.resource_type})"
            status_badge = "error"
            status_text = "失敗"
        else:
            activity_type = "ETL"
            description = f"BULK DATA 任務 ({job.resource_type})"
            status_badge = "warning"
            status_text = job.status
        
        activities.append({
            "time": time_str,
            "type": activity_type,
            "description": description,
            "status": status_text,
            "statusBadge": status_badge,
            "jobId": job.job_id
        })
    
    return activities

