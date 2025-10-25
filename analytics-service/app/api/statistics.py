from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from scipy import stats
from sqlalchemy import create_engine
import logging

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/descriptive")
async def get_descriptive_statistics(
    resource_type: str = Query("conditions", description="Resource type to analyze")
):
    """
    Get descriptive statistics for a resource type
    """
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        if resource_type == "conditions":
            query = """
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(DISTINCT patient_id) as unique_patients,
                    COUNT(DISTINCT code_text) as unique_conditions,
                    MIN(onset_datetime) as earliest_date,
                    MAX(onset_datetime) as latest_date
                FROM conditions
                WHERE onset_datetime IS NOT NULL
            """
        elif resource_type == "patients":
            query = """
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(DISTINCT gender) as unique_genders,
                    AVG(EXTRACT(YEAR FROM AGE(birth_date))) as avg_age,
                    MIN(birth_date) as earliest_birth,
                    MAX(birth_date) as latest_birth
                FROM patients
                WHERE birth_date IS NOT NULL
            """
        elif resource_type == "encounters":
            query = """
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(DISTINCT patient_id) as unique_patients,
                    COUNT(DISTINCT encounter_class) as unique_classes,
                    MIN(period_start) as earliest_date,
                    MAX(period_start) as latest_date
                FROM encounters
                WHERE period_start IS NOT NULL
            """
        else:
            query = "SELECT COUNT(*) as total_count FROM observations"
        
        df = pd.read_sql(query, engine)
        engine.dispose()
        
        result = df.to_dict('records')[0]
        
        # Convert datetime to string
        for key, value in result.items():
            if pd.isna(value):
                result[key] = None
            elif hasattr(value, 'isoformat'):
                result[key] = value.isoformat()
        
        return result
    
    except Exception as e:
        logger.error(f"Error calculating descriptive statistics: {e}")
        return {
            "total_count": 0,
            "error": str(e)
        }

@router.get("/correlation")
async def get_correlation_analysis(
    variable1: str = Query(..., description="First variable"),
    variable2: str = Query(..., description="Second variable")
):
    """
    Analyze correlation between two variables
    """
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        # Example: Correlation between age and number of conditions
        query = """
            SELECT 
                p.fhir_id,
                EXTRACT(YEAR FROM AGE(p.birth_date)) as age,
                COUNT(c.id) as condition_count
            FROM patients p
            LEFT JOIN conditions c ON p.fhir_id = c.patient_id
            WHERE p.birth_date IS NOT NULL
            GROUP BY p.fhir_id, p.birth_date
            HAVING COUNT(c.id) > 0
        """
        
        df = pd.read_sql(query, engine)
        engine.dispose()
        
        if len(df) < 2:
            return {
                "correlation": 0,
                "p_value": 1.0,
                "sample_size": len(df),
                "message": "Insufficient data for correlation analysis"
            }
        
        # Calculate Pearson correlation
        correlation, p_value = stats.pearsonr(df['age'], df['condition_count'])
        
        return {
            "correlation": float(correlation),
            "p_value": float(p_value),
            "sample_size": len(df),
            "interpretation": interpret_correlation(correlation, p_value)
        }
    
    except Exception as e:
        logger.error(f"Error calculating correlation: {e}")
        return {
            "error": str(e)
        }

@router.get("/trend-analysis")
async def get_trend_analysis(
    metric: str = Query("condition_count", description="Metric to analyze"),
    time_period: str = Query("monthly", description="Time aggregation: daily, weekly, monthly, yearly")
):
    """
    Perform trend analysis over time
    """
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        # Time truncation based on period
        time_trunc = {
            "daily": "day",
            "weekly": "week",
            "monthly": "month",
            "yearly": "year"
        }.get(time_period, "month")
        
        query = f"""
            SELECT 
                DATE_TRUNC('{time_trunc}', onset_datetime) as period,
                COUNT(*) as count
            FROM conditions
            WHERE onset_datetime IS NOT NULL
            GROUP BY period
            ORDER BY period
        """
        
        df = pd.read_sql(query, engine)
        engine.dispose()
        
        if len(df) < 3:
            return {
                "trend": "insufficient_data",
                "message": "Not enough data points for trend analysis"
            }
        
        # Calculate trend using linear regression
        x = np.arange(len(df))
        y = df['count'].values
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Determine trend direction
        if p_value < 0.05:
            if slope > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "slope": float(slope),
            "r_squared": float(r_value ** 2),
            "p_value": float(p_value),
            "data_points": len(df),
            "interpretation": f"The trend is {trend} with R² = {r_value**2:.3f}"
        }
    
    except Exception as e:
        logger.error(f"Error performing trend analysis: {e}")
        return {
            "error": str(e)
        }

def interpret_correlation(correlation: float, p_value: float) -> str:
    """Interpret correlation coefficient"""
    
    if p_value > 0.05:
        return "No significant correlation (p > 0.05)"
    
    abs_corr = abs(correlation)
    
    if abs_corr < 0.3:
        strength = "weak"
    elif abs_corr < 0.7:
        strength = "moderate"
    else:
        strength = "strong"
    
    direction = "positive" if correlation > 0 else "negative"
    
    return f"Statistically significant {strength} {direction} correlation (p < 0.05)"

