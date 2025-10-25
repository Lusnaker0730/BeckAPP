from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
from sqlalchemy import create_engine
import logging

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class CohortDefinition(BaseModel):
    name: str
    inclusion_criteria: Dict[str, Any]
    exclusion_criteria: Optional[Dict[str, Any]] = None

@router.post("/define")
async def define_cohort(cohort: CohortDefinition):
    """
    Define a patient cohort based on criteria
    """
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        # Build WHERE clause from inclusion criteria
        where_clauses = []
        
        if "condition" in cohort.inclusion_criteria:
            condition = cohort.inclusion_criteria["condition"]
            where_clauses.append(f"c.code_text ILIKE '%{condition}%'")
        
        if "age_min" in cohort.inclusion_criteria:
            age_min = cohort.inclusion_criteria["age_min"]
            where_clauses.append(f"EXTRACT(YEAR FROM AGE(p.birth_date)) >= {age_min}")
        
        if "age_max" in cohort.inclusion_criteria:
            age_max = cohort.inclusion_criteria["age_max"]
            where_clauses.append(f"EXTRACT(YEAR FROM AGE(p.birth_date)) <= {age_max}")
        
        if "gender" in cohort.inclusion_criteria:
            gender = cohort.inclusion_criteria["gender"]
            where_clauses.append(f"p.gender = '{gender}'")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Query patients matching criteria
        query = f"""
            SELECT DISTINCT
                p.fhir_id,
                p.gender,
                p.birth_date,
                EXTRACT(YEAR FROM AGE(p.birth_date)) as age
            FROM patients p
            LEFT JOIN conditions c ON p.fhir_id = c.patient_id
            WHERE {where_sql}
        """
        
        df = pd.read_sql(query, engine)
        engine.dispose()
        
        cohort_size = len(df)
        
        # Calculate cohort statistics
        if cohort_size > 0:
            avg_age = df['age'].mean()
            gender_dist = df['gender'].value_counts().to_dict()
        else:
            avg_age = 0
            gender_dist = {}
        
        return {
            "cohort_name": cohort.name,
            "cohort_size": cohort_size,
            "average_age": float(avg_age) if not pd.isna(avg_age) else 0,
            "gender_distribution": gender_dist,
            "status": "created"
        }
    
    except Exception as e:
        logger.error(f"Error defining cohort: {e}")
        return {
            "error": str(e)
        }

@router.get("/compare")
async def compare_cohorts(
    cohort1_criteria: str = Query(..., description="Criteria for cohort 1"),
    cohort2_criteria: str = Query(..., description="Criteria for cohort 2")
):
    """
    Compare two cohorts
    """
    
    # This would implement cohort comparison logic
    # For now, return a placeholder
    
    return {
        "cohort1_size": 1250,
        "cohort2_size": 980,
        "overlap": 150,
        "cohort1_only": 1100,
        "cohort2_only": 830,
        "relative_risk": 1.28,
        "p_value": 0.023
    }

@router.get("/survival-analysis")
async def survival_analysis(
    cohort_criteria: str = Query(..., description="Cohort criteria"),
    event: str = Query(..., description="Event to track"),
    follow_up_months: int = Query(12, description="Follow-up period in months")
):
    """
    Perform survival analysis on a cohort
    """
    
    # Placeholder for Kaplan-Meier survival analysis
    
    return {
        "cohort_size": 500,
        "events": 85,
        "censored": 415,
        "median_survival_months": 18.5,
        "survival_rates": {
            "6_months": 0.92,
            "12_months": 0.85,
            "24_months": 0.78
        }
    }

