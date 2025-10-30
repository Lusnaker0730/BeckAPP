"""
Cohort Analysis API Routes
患者群组分析 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.cohort import Cohort, CohortComparison
from app.models.fhir_resources import Patient, Condition, Encounter, Observation

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Schemas
# ============================================================================

class CohortCriteria(BaseModel):
    """群组筛选条件"""
    age_min: Optional[int] = Field(None, ge=0, le=120, description="最小年龄")
    age_max: Optional[int] = Field(None, ge=0, le=120, description="最大年龄")
    gender: Optional[str] = Field(None, description="性别: male, female, other")
    conditions: Optional[List[str]] = Field(None, description="诊断列表")
    date_range_start: Optional[str] = Field(None, description="开始日期 YYYY-MM-DD")
    date_range_end: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")
    job_id: Optional[str] = Field(None, description="ETL Job ID")


class CohortCreate(BaseModel):
    """创建群组请求"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    criteria: CohortCriteria


class CohortUpdate(BaseModel):
    """更新群组请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    criteria: Optional[CohortCriteria] = None
    is_active: Optional[bool] = None


class CohortResponse(BaseModel):
    """群组响应"""
    id: int
    name: str
    description: Optional[str]
    criteria: Dict[str, Any]
    patient_count: int
    created_by: str
    last_calculated: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CohortStats(BaseModel):
    """群组统计数据"""
    total_patients: int
    gender_distribution: Dict[str, int]
    age_distribution: Dict[str, int]
    top_conditions: List[Dict[str, Any]]
    encounters_count: int
    avg_encounters_per_patient: float


class ComparisonCreate(BaseModel):
    """创建对比分析请求"""
    name: str
    description: Optional[str] = None
    cohort_ids: List[int]
    analysis_type: str = Field(..., pattern="^(outcomes|demographics|trends|costs)$")
    
    @field_validator('cohort_ids')
    @classmethod
    def validate_cohort_ids_length(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 cohorts are required for comparison")
        if len(v) > 5:
            raise ValueError("Maximum 5 cohorts can be compared at once")
        return v


# ============================================================================
# Cohort CRUD Operations
# ============================================================================

@router.post("/cohorts", response_model=CohortResponse, status_code=status.HTTP_201_CREATED)
async def create_cohort(
    cohort_data: CohortCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新的患者群组
    
    根据指定的筛选条件创建患者群组，并自动计算患者数量。
    """
    try:
        # Create cohort
        new_cohort = Cohort(
            name=cohort_data.name,
            description=cohort_data.description,
            criteria=cohort_data.criteria.dict(exclude_none=True),
            created_by=current_user.get("username", "unknown"),
            is_active=True
        )
        
        db.add(new_cohort)
        db.flush()  # Get the ID
        
        # Calculate patient count
        patient_count = await _calculate_cohort_size(
            db, cohort_data.criteria
        )
        new_cohort.patient_count = patient_count
        new_cohort.last_calculated = datetime.now()
        
        db.commit()
        db.refresh(new_cohort)
        
        logger.info(f"Created cohort: {new_cohort.name} (ID: {new_cohort.id}) with {patient_count} patients")
        
        return new_cohort
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating cohort: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create cohort: {str(e)}"
        )


@router.get("/cohorts", response_model=List[CohortResponse])
async def list_cohorts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = Query(True),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有群组列表
    """
    query = db.query(Cohort)
    
    if active_only:
        query = query.filter(Cohort.is_active == True)
    
    cohorts = query.order_by(Cohort.created_at.desc()).offset(skip).limit(limit).all()
    
    return cohorts


@router.get("/cohorts/{cohort_id}", response_model=CohortResponse)
async def get_cohort(
    cohort_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定群组详情
    """
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    
    if not cohort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cohort {cohort_id} not found"
        )
    
    return cohort


@router.put("/cohorts/{cohort_id}", response_model=CohortResponse)
async def update_cohort(
    cohort_id: int,
    cohort_update: CohortUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新群组信息
    """
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    
    if not cohort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cohort {cohort_id} not found"
        )
    
    # Update fields
    update_data = cohort_update.dict(exclude_none=True)
    
    for field, value in update_data.items():
        if field == "criteria" and value:
            setattr(cohort, field, value.dict(exclude_none=True))
        else:
            setattr(cohort, field, value)
    
    # Recalculate if criteria changed
    if cohort_update.criteria:
        patient_count = await _calculate_cohort_size(db, cohort_update.criteria)
        cohort.patient_count = patient_count
        cohort.last_calculated = datetime.now()
    
    try:
        db.commit()
        db.refresh(cohort)
        return cohort
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cohort: {str(e)}"
        )


@router.delete("/cohorts/{cohort_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cohort(
    cohort_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除群组（软删除）
    """
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    
    if not cohort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cohort {cohort_id} not found"
        )
    
    # Soft delete
    cohort.is_active = False
    
    try:
        db.commit()
        logger.info(f"Deleted cohort {cohort_id}")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cohort: {str(e)}"
        )


# ============================================================================
# Cohort Analysis
# ============================================================================

@router.get("/cohorts/{cohort_id}/stats", response_model=CohortStats)
async def get_cohort_statistics(
    cohort_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取群组统计数据
    
    返回群组的详细统计信息，包括：
    - 患者总数
    - 性别分布
    - 年龄分布
    - 前五大诊断
    - 就诊次数
    """
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    
    if not cohort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cohort {cohort_id} not found"
        )
    
    # Build patient query based on criteria
    criteria = CohortCriteria(**cohort.criteria)
    patient_query = await _build_patient_query(db, criteria)
    
    # Get patient FH IR IDs
    patient_fhir_ids = [p.fhir_id for p in patient_query.all()]
    
    if not patient_fhir_ids:
        return CohortStats(
            total_patients=0,
            gender_distribution={},
            age_distribution={},
            top_conditions=[],
            encounters_count=0,
            avg_encounters_per_patient=0.0
        )
    
    # Gender distribution
    gender_dist = db.query(
        Patient.gender,
        func.count(Patient.id).label('count')
    ).filter(
        Patient.fhir_id.in_(patient_fhir_ids)
    ).group_by(Patient.gender).all()
    
    gender_distribution = {row.gender or "unknown": row.count for row in gender_dist}
    
    # Age distribution
    current_year = datetime.now().year
    age_groups = {"0-18": 0, "19-35": 0, "36-50": 0, "51-65": 0, "65+": 0}
    
    patients = db.query(Patient.birth_date).filter(
        Patient.fhir_id.in_(patient_fhir_ids),
        Patient.birth_date.isnot(None)
    ).all()
    
    for patient in patients:
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
    
    # Top conditions
    top_conditions_query = db.query(
        Condition.code_text,
        func.count(Condition.id).label('count')
    ).filter(
        Condition.patient_id.in_(patient_fhir_ids),
        Condition.code_text.isnot(None)
    ).group_by(Condition.code_text).order_by(
        func.count(Condition.id).desc()
    ).limit(5).all()
    
    top_conditions = [
        {"condition": row.code_text, "count": row.count}
        for row in top_conditions_query
    ]
    
    # Encounters
    encounters_count = db.query(func.count(Encounter.id)).filter(
        Encounter.patient_id.in_(patient_fhir_ids)
    ).scalar() or 0
    
    total_patients = len(patient_fhir_ids)
    avg_encounters = encounters_count / total_patients if total_patients > 0 else 0
    
    return CohortStats(
        total_patients=total_patients,
        gender_distribution=gender_distribution,
        age_distribution=age_groups,
        top_conditions=top_conditions,
        encounters_count=encounters_count,
        avg_encounters_per_patient=round(avg_encounters, 2)
    )


@router.get("/cohorts/{cohort_id}/patients")
async def get_cohort_patients(
    cohort_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取群组中的患者列表
    """
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    
    if not cohort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cohort {cohort_id} not found"
        )
    
    criteria = CohortCriteria(**cohort.criteria)
    patient_query = await _build_patient_query(db, criteria)
    
    patients = patient_query.offset(skip).limit(limit).all()
    
    # Format response
    patient_list = []
    for patient in patients:
        patient_list.append({
            "id": patient.id,
            "fhir_id": patient.fhir_id,
            "name": patient.name,
            "gender": patient.gender,
            "birth_date": patient.birth_date.isoformat() if patient.birth_date else None
        })
    
    return {
        "total": cohort.patient_count,
        "skip": skip,
        "limit": limit,
        "patients": patient_list
    }


# ============================================================================
# Cohort Comparison
# ============================================================================

@router.post("/cohorts/compare", status_code=status.HTTP_200_OK)
async def compare_cohorts(
    comparison: ComparisonCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    对比多个群组
    
    支持的分析类型：
    - outcomes: 健康结果对比
    - demographics: 人口统计对比
    - trends: 趋势对比
    - costs: 成本对比（未来）
    """
    # Validate cohorts exist
    cohorts = db.query(Cohort).filter(
        Cohort.id.in_(comparison.cohort_ids),
        Cohort.is_active == True
    ).all()
    
    if len(cohorts) != len(comparison.cohort_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more cohorts not found"
        )
    
    # Perform comparison based on analysis type
    if comparison.analysis_type == "demographics":
        results = await _compare_demographics(db, cohorts)
    elif comparison.analysis_type == "outcomes":
        results = await _compare_outcomes(db, cohorts)
    elif comparison.analysis_type == "trends":
        results = await _compare_trends(db, cohorts)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis type '{comparison.analysis_type}' not yet implemented"
        )
    
    # Save comparison
    new_comparison = CohortComparison(
        name=comparison.name,
        description=comparison.description,
        cohort_ids=comparison.cohort_ids,
        analysis_type=comparison.analysis_type,
        results=results,
        created_by=current_user.get("username", "unknown")
    )
    
    db.add(new_comparison)
    db.commit()
    db.refresh(new_comparison)
    
    return {
        "comparison_id": new_comparison.id,
        "cohorts": [{"id": c.id, "name": c.name} for c in cohorts],
        "analysis_type": comparison.analysis_type,
        "results": results
    }


# ============================================================================
# Helper Functions
# ============================================================================

async def _calculate_cohort_size(db: Session, criteria: CohortCriteria) -> int:
    """计算符合条件的患者数量"""
    query = await _build_patient_query(db, criteria)
    return query.count()


async def _build_patient_query(db: Session, criteria: CohortCriteria):
    """根据条件构建患者查询"""
    query = db.query(Patient)
    
    # Gender filter
    if criteria.gender:
        query = query.filter(Patient.gender == criteria.gender)
    
    # Age filter
    current_year = datetime.now().year
    if criteria.age_min is not None:
        min_birth_year = current_year - criteria.age_min
        query = query.filter(extract('year', Patient.birth_date) <= min_birth_year)
    
    if criteria.age_max is not None:
        max_birth_year = current_year - criteria.age_max
        query = query.filter(extract('year', Patient.birth_date) >= max_birth_year)
    
    # Conditions filter
    if criteria.conditions and len(criteria.conditions) > 0:
        # Get patient IDs with specified conditions
        condition_query = db.query(Condition.patient_id).filter(
            or_(*[Condition.code_text.ilike(f"%{cond}%") for cond in criteria.conditions])
        )
        
        # Add date range if specified
        if criteria.date_range_start:
            condition_query = condition_query.filter(
                Condition.onset_datetime >= criteria.date_range_start
            )
        if criteria.date_range_end:
            condition_query = condition_query.filter(
                Condition.onset_datetime <= criteria.date_range_end
            )
        
        patient_ids_with_conditions = [row[0] for row in condition_query.distinct().all()]
        
        if patient_ids_with_conditions:
            query = query.filter(Patient.fhir_id.in_(patient_ids_with_conditions))
        else:
            # No patients match conditions
            query = query.filter(Patient.id == None)  # Return empty
    
    # Job ID filter
    if criteria.job_id:
        query = query.filter(Patient.job_id == criteria.job_id)
    
    return query


async def _compare_demographics(db: Session, cohorts: List[Cohort]) -> Dict[str, Any]:
    """对比群组的人口统计特征"""
    comparison_data = {}
    
    for cohort in cohorts:
        criteria = CohortCriteria(**cohort.criteria)
        patient_query = await _build_patient_query(db, criteria)
        patient_fhir_ids = [p.fhir_id for p in patient_query.all()]
        
        # Gender distribution
        gender_dist = db.query(
            Patient.gender,
            func.count(Patient.id).label('count')
        ).filter(
            Patient.fhir_id.in_(patient_fhir_ids)
        ).group_by(Patient.gender).all()
        
        # Age stats
        current_year = datetime.now().year
        ages = []
        for patient in db.query(Patient.birth_date).filter(
            Patient.fhir_id.in_(patient_fhir_ids),
            Patient.birth_date.isnot(None)
        ).all():
            if patient.birth_date:
                ages.append(current_year - patient.birth_date.year)
        
        avg_age = sum(ages) / len(ages) if ages else 0
        
        comparison_data[cohort.name] = {
            "total_patients": len(patient_fhir_ids),
            "gender_distribution": {row.gender or "unknown": row.count for row in gender_dist},
            "average_age": round(avg_age, 1),
            "age_range": {"min": min(ages) if ages else 0, "max": max(ages) if ages else 0}
        }
    
    return comparison_data


async def _compare_outcomes(db: Session, cohorts: List[Cohort]) -> Dict[str, Any]:
    """对比群组的健康结果"""
    comparison_data = {}
    
    for cohort in cohorts:
        criteria = CohortCriteria(**cohort.criteria)
        patient_query = await _build_patient_query(db, criteria)
        patient_fhir_ids = [p.fhir_id for p in patient_query.all()]
        
        if not patient_fhir_ids:
            comparison_data[cohort.name] = {
                "avg_encounters": 0,
                "total_conditions": 0,
                "unique_conditions": 0
            }
            continue
        
        # Encounters per patient
        encounters_count = db.query(func.count(Encounter.id)).filter(
            Encounter.patient_id.in_(patient_fhir_ids)
        ).scalar() or 0
        
        avg_encounters = encounters_count / len(patient_fhir_ids)
        
        # Conditions
        total_conditions = db.query(func.count(Condition.id)).filter(
            Condition.patient_id.in_(patient_fhir_ids)
        ).scalar() or 0
        
        unique_conditions = db.query(func.count(func.distinct(Condition.code_text))).filter(
            Condition.patient_id.in_(patient_fhir_ids),
            Condition.code_text.isnot(None)
        ).scalar() or 0
        
        comparison_data[cohort.name] = {
            "avg_encounters_per_patient": round(avg_encounters, 2),
            "total_conditions": total_conditions,
            "unique_conditions": unique_conditions,
            "avg_conditions_per_patient": round(total_conditions / len(patient_fhir_ids), 2)
        }
    
    return comparison_data


async def _compare_trends(db: Session, cohorts: List[Cohort]) -> Dict[str, Any]:
    """对比群组的趋势数据"""
    comparison_data = {}
    
    for cohort in cohorts:
        criteria = CohortCriteria(**cohort.criteria)
        patient_query = await _build_patient_query(db, criteria)
        patient_fhir_ids = [p.fhir_id for p in patient_query.all()]
        
        if not patient_fhir_ids:
            comparison_data[cohort.name] = {"yearly_encounters": {}}
            continue
        
        # Yearly encounter trends
        yearly_data = db.query(
            extract('year', Encounter.period_start).label('year'),
            func.count(Encounter.id).label('count')
        ).filter(
            Encounter.patient_id.in_(patient_fhir_ids),
            Encounter.period_start.isnot(None)
        ).group_by('year').order_by('year').all()
        
        comparison_data[cohort.name] = {
            "yearly_encounters": {
                int(row.year): row.count for row in yearly_data if row.year
            }
        }
    
    return comparison_data

