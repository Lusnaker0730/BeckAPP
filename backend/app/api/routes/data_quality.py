"""
Data Quality Monitoring API Routes
数据质量监控 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, cast, Float
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.fhir_resources import Patient, Condition, Encounter, Observation
from app.models.etl_job import ETLJob

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Schemas
# ============================================================================

class DataQualityOverview(BaseModel):
    """数据质量概览"""
    overall_score: float
    total_records: int
    quality_issues: int
    last_updated: datetime
    metrics: Dict[str, Any]


class DataCompletenessMetric(BaseModel):
    """数据完整性指标"""
    table_name: str
    total_records: int
    completeness_score: float
    missing_fields: Dict[str, int]


class DataConsistencyMetric(BaseModel):
    """数据一致性指标"""
    duplicate_patients: int
    duplicate_conditions: int
    orphaned_records: int
    consistency_score: float


class DataAccuracyMetric(BaseModel):
    """数据准确性指标"""
    invalid_dates: int
    invalid_codes: int
    outliers: int
    accuracy_score: float


class DataTimelinessMetric(BaseModel):
    """数据及时性指标"""
    avg_ingestion_delay_hours: float
    last_update: Optional[datetime]
    stale_records_count: int
    timeliness_score: float


class QualityIssue(BaseModel):
    """数据质量问题"""
    id: int
    severity: str
    issue_type: str
    table_name: str
    record_id: Optional[str]
    description: str
    detected_at: datetime


# ============================================================================
# Data Quality Endpoints
# ============================================================================

@router.get("/overview", response_model=DataQualityOverview)
async def get_quality_overview(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取数据质量概览
    
    返回整体数据质量评分和关键指标
    """
    try:
        # Count total records
        total_patients = db.query(func.count(Patient.id)).scalar() or 0
        total_conditions = db.query(func.count(Condition.id)).scalar() or 0
        total_encounters = db.query(func.count(Encounter.id)).scalar() or 0
        total_observations = db.query(func.count(Observation.id)).scalar() or 0
        total_records = total_patients + total_conditions + total_encounters + total_observations
        
        # Calculate quality scores
        completeness = await _calculate_completeness_score(db)
        consistency = await _calculate_consistency_score(db)
        accuracy = await _calculate_accuracy_score(db)
        timeliness = await _calculate_timeliness_score(db)
        
        # Overall score (weighted average)
        overall_score = (
            completeness * 0.3 +
            consistency * 0.3 +
            accuracy * 0.2 +
            timeliness * 0.2
        )
        
        # Count quality issues
        quality_issues = 0
        if completeness < 0.8:
            quality_issues += 1
        if consistency < 0.8:
            quality_issues += 1
        if accuracy < 0.8:
            quality_issues += 1
        if timeliness < 0.8:
            quality_issues += 1
        
        return DataQualityOverview(
            overall_score=round(overall_score, 2),
            total_records=total_records,
            quality_issues=quality_issues,
            last_updated=datetime.now(timezone.utc),
            metrics={
                "completeness": round(completeness, 2),
                "consistency": round(consistency, 2),
                "accuracy": round(accuracy, 2),
                "timeliness": round(timeliness, 2)
            }
        )
        
    except Exception as e:
        logger.error(f"Error calculating quality overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate quality overview: {str(e)}"
        )


@router.get("/completeness", response_model=List[DataCompletenessMetric])
async def get_completeness_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取数据完整性指标
    
    检查每个表的必填字段缺失情况
    """
    metrics = []
    
    # Patients completeness
    total_patients = db.query(func.count(Patient.id)).scalar() or 0
    if total_patients > 0:
        missing_name = db.query(func.count(Patient.id)).filter(
            Patient.name.is_(None)
        ).scalar() or 0
        missing_gender = db.query(func.count(Patient.id)).filter(
            Patient.gender.is_(None)
        ).scalar() or 0
        missing_birth_date = db.query(func.count(Patient.id)).filter(
            Patient.birth_date.is_(None)
        ).scalar() or 0
        
        total_missing = missing_name + missing_gender + missing_birth_date
        completeness_score = 1 - (total_missing / (total_patients * 3))
        
        metrics.append(DataCompletenessMetric(
            table_name="patients",
            total_records=total_patients,
            completeness_score=round(completeness_score, 2),
            missing_fields={
                "name": missing_name,
                "gender": missing_gender,
                "birth_date": missing_birth_date
            }
        ))
    
    # Conditions completeness
    total_conditions = db.query(func.count(Condition.id)).scalar() or 0
    if total_conditions > 0:
        missing_patient_id = db.query(func.count(Condition.id)).filter(
            Condition.patient_id.is_(None)
        ).scalar() or 0
        missing_code = db.query(func.count(Condition.id)).filter(
            and_(Condition.code.is_(None), Condition.code_text.is_(None))
        ).scalar() or 0
        missing_onset = db.query(func.count(Condition.id)).filter(
            Condition.onset_datetime.is_(None)
        ).scalar() or 0
        
        total_missing = missing_patient_id + missing_code + missing_onset
        completeness_score = 1 - (total_missing / (total_conditions * 3))
        
        metrics.append(DataCompletenessMetric(
            table_name="conditions",
            total_records=total_conditions,
            completeness_score=round(completeness_score, 2),
            missing_fields={
                "patient_id": missing_patient_id,
                "code": missing_code,
                "onset_datetime": missing_onset
            }
        ))
    
    # Encounters completeness
    total_encounters = db.query(func.count(Encounter.id)).scalar() or 0
    if total_encounters > 0:
        missing_patient_id = db.query(func.count(Encounter.id)).filter(
            Encounter.patient_id.is_(None)
        ).scalar() or 0
        missing_class = db.query(func.count(Encounter.id)).filter(
            Encounter.encounter_class.is_(None)
        ).scalar() or 0
        missing_start_time = db.query(func.count(Encounter.id)).filter(
            Encounter.period_start.is_(None)
        ).scalar() or 0
        
        total_missing = missing_patient_id + missing_class + missing_start_time
        completeness_score = 1 - (total_missing / (total_encounters * 3))
        
        metrics.append(DataCompletenessMetric(
            table_name="encounters",
            total_records=total_encounters,
            completeness_score=round(completeness_score, 2),
            missing_fields={
                "patient_id": missing_patient_id,
                "encounter_class": missing_class,
                "start_time": missing_start_time
            }
        ))
    
    return metrics


@router.get("/consistency")
async def get_consistency_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取数据一致性指标
    
    检查重复记录、孤立记录等问题
    """
    # Check for duplicate patients (same name and birth date)
    duplicate_patients = db.query(
        Patient.name,
        Patient.birth_date,
        func.count(Patient.id).label('count')
    ).filter(
        Patient.name.isnot(None),
        Patient.birth_date.isnot(None)
    ).group_by(
        Patient.name, Patient.birth_date
    ).having(
        func.count(Patient.id) > 1
    ).count()
    
    # Check for orphaned conditions (patient doesn't exist)
    total_conditions = db.query(func.count(Condition.id)).scalar() or 0
    valid_patient_ids = db.query(Patient.fhir_id).all()
    valid_patient_ids_set = {pid[0] for pid in valid_patient_ids}
    
    orphaned_conditions = db.query(func.count(Condition.id)).filter(
        Condition.patient_id.isnot(None),
        ~Condition.patient_id.in_(valid_patient_ids_set) if valid_patient_ids_set else False
    ).scalar() or 0
    
    # Calculate consistency score
    total_records = db.query(func.count(Patient.id)).scalar() or 0
    total_records += total_conditions
    
    issues = duplicate_patients + orphaned_conditions
    consistency_score = 1 - (issues / total_records) if total_records > 0 else 1.0
    
    return {
        "duplicate_patients": duplicate_patients,
        "duplicate_conditions": 0,  # TODO: Implement
        "orphaned_records": orphaned_conditions,
        "consistency_score": round(consistency_score, 2),
        "total_issues": issues
    }


@router.get("/accuracy")
async def get_accuracy_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取数据准确性指标
    
    检查无效日期、无效代码等
    """
    # Check for invalid dates (future birth dates)
    current_date = datetime.now().date()
    invalid_birth_dates = db.query(func.count(Patient.id)).filter(
        Patient.birth_date > current_date
    ).scalar() or 0
    
    # Check for invalid encounter dates (end before start)
    invalid_encounter_dates = db.query(func.count(Encounter.id)).filter(
        and_(
            Encounter.period_start.isnot(None),
            Encounter.period_end.isnot(None),
            Encounter.period_end < Encounter.period_start
        )
    ).scalar() or 0
    
    # Check for missing/invalid condition codes
    invalid_codes = db.query(func.count(Condition.id)).filter(
        and_(
            Condition.code.is_(None),
            Condition.code_text.is_(None)
        )
    ).scalar() or 0
    
    # Calculate accuracy score
    total_records = db.query(func.count(Patient.id)).scalar() or 0
    total_records += db.query(func.count(Condition.id)).scalar() or 0
    total_records += db.query(func.count(Encounter.id)).scalar() or 0
    
    issues = invalid_birth_dates + invalid_encounter_dates + invalid_codes
    accuracy_score = 1 - (issues / total_records) if total_records > 0 else 1.0
    
    return {
        "invalid_dates": invalid_birth_dates + invalid_encounter_dates,
        "invalid_codes": invalid_codes,
        "outliers": 0,  # TODO: Implement outlier detection
        "accuracy_score": round(accuracy_score, 2),
        "details": {
            "invalid_birth_dates": invalid_birth_dates,
            "invalid_encounter_dates": invalid_encounter_dates,
            "invalid_condition_codes": invalid_codes
        }
    }


@router.get("/timeliness")
async def get_timeliness_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取数据及时性指标
    
    检查数据更新延迟、过期数据等
    """
    # Get last ETL job
    last_job = db.query(ETLJob).order_by(ETLJob.created_at.desc()).first()
    
    if last_job:
        last_update = last_job.created_at
        # Calculate delay (assuming data should be ingested within 24 hours)
        now = datetime.now(timezone.utc)
        if last_job.end_time:
            delay_hours = (now - last_job.end_time).total_seconds() / 3600
        else:
            delay_hours = (now - last_job.created_at).total_seconds() / 3600
    else:
        last_update = None
        delay_hours = 0
    
    # Count records older than 90 days without updates
    stale_threshold = datetime.now(timezone.utc) - timedelta(days=90)
    stale_conditions = db.query(func.count(Condition.id)).filter(
        Condition.onset_datetime < stale_threshold
    ).scalar() or 0
    
    # Calculate timeliness score
    # Score decreases if data is too old or ingestion is delayed
    score = 1.0
    if delay_hours > 24:
        score -= min(0.3, (delay_hours - 24) / 240)  # Penalty for delay
    if stale_conditions > 100:
        score -= min(0.2, stale_conditions / 10000)  # Penalty for stale records
    
    timeliness_score = max(0, score)
    
    return {
        "avg_ingestion_delay_hours": round(delay_hours, 2),
        "last_update": last_update.isoformat() if last_update else None,
        "stale_records_count": stale_conditions,
        "timeliness_score": round(timeliness_score, 2)
    }


@router.get("/issues")
async def get_quality_issues(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[str] = Query(None, pattern="^(critical|high|medium|low)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取数据质量问题列表
    
    返回按严重程度分类的数据质量问题
    """
    issues = []
    issue_id = 1
    
    # Critical: Missing patient IDs in conditions
    orphaned_conditions = db.query(Condition).filter(
        Condition.patient_id.is_(None)
    ).limit(10).all()
    
    for cond in orphaned_conditions:
        issues.append({
            "id": issue_id,
            "severity": "critical",
            "issue_type": "missing_reference",
            "table_name": "conditions",
            "record_id": cond.fhir_id,
            "description": f"Condition {cond.fhir_id} has no patient reference",
            "detected_at": datetime.now(timezone.utc).isoformat()
        })
        issue_id += 1
    
    # High: Invalid dates
    invalid_patients = db.query(Patient).filter(
        Patient.birth_date > datetime.now().date()
    ).limit(10).all()
    
    for patient in invalid_patients:
        issues.append({
            "id": issue_id,
            "severity": "high",
            "issue_type": "invalid_date",
            "table_name": "patients",
            "record_id": patient.fhir_id,
            "description": f"Patient {patient.fhir_id} has future birth date: {patient.birth_date}",
            "detected_at": datetime.now(timezone.utc).isoformat()
        })
        issue_id += 1
    
    # Medium: Missing optional fields
    patients_missing_name = db.query(Patient).filter(
        Patient.name.is_(None)
    ).limit(10).all()
    
    for patient in patients_missing_name:
        issues.append({
            "id": issue_id,
            "severity": "medium",
            "issue_type": "missing_field",
            "table_name": "patients",
            "record_id": patient.fhir_id,
            "description": f"Patient {patient.fhir_id} has no name",
            "detected_at": datetime.now(timezone.utc).isoformat()
        })
        issue_id += 1
    
    # Filter by severity if specified
    if severity:
        issues = [i for i in issues if i["severity"] == severity]
    
    # Pagination
    total = len(issues)
    issues = issues[skip:skip+limit]
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "issues": issues
    }


@router.get("/trends")
async def get_quality_trends(
    days: int = Query(30, ge=7, le=90),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取数据质量趋势
    
    返回过去N天的数据质量变化趋势
    """
    # TODO: Implement trend tracking with historical data
    # For now, return mock data
    
    trends = []
    current_score = await _calculate_overall_quality_score(db)
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i-1)
        # Simulate slight variations
        score = current_score + ((-1) ** i) * 0.02
        trends.append({
            "date": date.date().isoformat(),
            "overall_score": round(max(0, min(1, score)), 2),
            "completeness": round(max(0, min(1, score + 0.05)), 2),
            "consistency": round(max(0, min(1, score - 0.03)), 2),
            "accuracy": round(max(0, min(1, score + 0.02)), 2),
            "timeliness": round(max(0, min(1, score - 0.01)), 2)
        })
    
    return {
        "period_days": days,
        "trends": trends
    }


# ============================================================================
# Helper Functions
# ============================================================================

async def _calculate_completeness_score(db: Session) -> float:
    """计算完整性评分"""
    metrics = await get_completeness_metrics({"username": "system"}, db)
    if not metrics:
        return 1.0
    
    avg_score = sum(m.completeness_score for m in metrics) / len(metrics)
    return avg_score


async def _calculate_consistency_score(db: Session) -> float:
    """计算一致性评分"""
    metrics = await get_consistency_metrics({"username": "system"}, db)
    return metrics.get("consistency_score", 1.0)


async def _calculate_accuracy_score(db: Session) -> float:
    """计算准确性评分"""
    metrics = await get_accuracy_metrics({"username": "system"}, db)
    return metrics.get("accuracy_score", 1.0)


async def _calculate_timeliness_score(db: Session) -> float:
    """计算及时性评分"""
    metrics = await get_timeliness_metrics({"username": "system"}, db)
    return metrics.get("timeliness_score", 1.0)


async def _calculate_overall_quality_score(db: Session) -> float:
    """计算整体质量评分"""
    completeness = await _calculate_completeness_score(db)
    consistency = await _calculate_consistency_score(db)
    accuracy = await _calculate_accuracy_score(db)
    timeliness = await _calculate_timeliness_score(db)
    
    return (completeness * 0.3 + consistency * 0.3 + accuracy * 0.2 + timeliness * 0.2)

