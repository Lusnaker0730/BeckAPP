from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import logging

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class VisualizationRequest(BaseModel):
    xAxis: str
    yAxis: str
    filter: Optional[str] = "all"

@router.get("/by-diagnosis")
async def get_visualization_by_diagnosis(
    diagnosis: str = Query(..., description="Diagnosis name or code"),
    xAxis: str = Query("gender", description="X-axis variable"),
    yAxis: str = Query("count", description="Y-axis variable"),
    filter: str = Query("all", description="Filter criteria")
):
    """
    Generate visualization data for a specific diagnosis
    Shows demographic distribution of patients with this diagnosis
    """
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        # Identify which axis is the categorical variable and which is the metric
        # Metrics: count, average, total
        # Categories: gender, age_group, condition_code, encounter_type, date
        
        metrics = ['count', 'average', 'total']
        categories = ['gender', 'age_group', 'condition_code', 'encounter_type', 'date']
        
        # Determine category and metric
        if xAxis in metrics and yAxis in categories:
            # Swap if user selected metric on X axis
            category_axis = yAxis
            metric_axis = xAxis
        elif xAxis in categories and yAxis in metrics:
            category_axis = xAxis
            metric_axis = yAxis
        elif xAxis in categories and yAxis in categories:
            # Both are categories, use xAxis as category
            category_axis = xAxis
            metric_axis = 'count'
        else:
            # Default
            category_axis = xAxis
            metric_axis = yAxis
        
        # Build query based on the category axis for specific diagnosis
        if category_axis == "gender":
            # Gender distribution for this diagnosis
            query = """
                SELECT p.gender as label, COUNT(DISTINCT p.id) as count
                FROM patients p
                JOIN conditions c ON c.patient_id = p.fhir_id
                WHERE c.code_text ILIKE %(diagnosis)s
                AND p.gender IS NOT NULL
                GROUP BY p.gender
                ORDER BY count DESC
            """
            df = pd.read_sql(query, engine, params={'diagnosis': f'%{diagnosis}%'})
            
        elif category_axis == "age_group":
            # Age group distribution for this diagnosis
            query = """
                SELECT 
                    CASE 
                        WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) < 18 THEN '0-18'
                        WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 18 AND 35 THEN '19-35'
                        WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 36 AND 50 THEN '36-50'
                        WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 51 AND 65 THEN '51-65'
                        ELSE '65+'
                    END as label,
                    COUNT(DISTINCT p.id) as count
                FROM patients p
                JOIN conditions c ON c.patient_id = p.fhir_id
                WHERE c.code_text ILIKE %(diagnosis)s
                AND p.birth_date IS NOT NULL
                GROUP BY CASE 
                    WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) < 18 THEN '0-18'
                    WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 18 AND 35 THEN '19-35'
                    WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 36 AND 50 THEN '36-50'
                    WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 51 AND 65 THEN '51-65'
                    ELSE '65+'
                END
                ORDER BY label
            """
            df = pd.read_sql(query, engine, params={'diagnosis': f'%{diagnosis}%'})
            
        elif category_axis == "date":
            # Time series for this diagnosis
            query = """
                SELECT 
                    TO_CHAR(DATE_TRUNC('month', c.onset_datetime), 'YYYY-MM') as label,
                    COUNT(*) as count
                FROM conditions c
                WHERE c.code_text ILIKE %(diagnosis)s
                AND c.onset_datetime IS NOT NULL
                GROUP BY DATE_TRUNC('month', c.onset_datetime)
                ORDER BY DATE_TRUNC('month', c.onset_datetime)
            """
            df = pd.read_sql(query, engine, params={'diagnosis': f'%{diagnosis}%'})
            
        elif category_axis == "condition_code":
            # Other diagnoses for patients with this diagnosis (comorbidities)
            query = """
                SELECT 
                    c2.code_text as label,
                    COUNT(DISTINCT c2.id) as count
                FROM conditions c1
                JOIN patients p ON c1.patient_id = p.fhir_id
                JOIN conditions c2 ON c2.patient_id = p.fhir_id
                WHERE c1.code_text ILIKE %(diagnosis)s
                AND c2.code_text IS NOT NULL
                AND c2.code_text NOT ILIKE %(diagnosis)s
                GROUP BY c2.code_text
                ORDER BY count DESC
                LIMIT 10
            """
            df = pd.read_sql(query, engine, params={'diagnosis': f'%{diagnosis}%'})
            
        elif category_axis == "encounter_type":
            # Encounter types for patients with this diagnosis
            query = """
                SELECT 
                    e.encounter_class as label,
                    COUNT(DISTINCT e.id) as count
                FROM conditions c
                JOIN patients p ON c.patient_id = p.fhir_id
                JOIN encounters e ON e.patient_id = p.fhir_id
                WHERE c.code_text ILIKE %(diagnosis)s
                AND e.encounter_class IS NOT NULL
                GROUP BY e.encounter_class
                ORDER BY count DESC
            """
            df = pd.read_sql(query, engine, params={'diagnosis': f'%{diagnosis}%'})
            
        else:
            # Return empty data if no matching axis configuration
            df = pd.DataFrame({
                'label': [],
                'count': []
            })
        
        engine.dispose()
        
        # Format response
        labels = df.iloc[:, 0].tolist()
        values = df.iloc[:, 1].tolist()
        
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": f"{diagnosis} - {yAxis}",
                    "data": values,
                    "backgroundColor": [
                        'rgba(37, 99, 235, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                    ] * (len(values) // 5 + 1),
                    "borderColor": [
                        'rgb(37, 99, 235)',
                        'rgb(16, 185, 129)',
                        'rgb(245, 158, 11)',
                        'rgb(239, 68, 68)',
                        'rgb(139, 92, 246)',
                    ] * (len(values) // 5 + 1),
                    "borderWidth": 2,
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"Error generating diagnosis visualization: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return empty data on error - DO NOT return fake data for medical software
        return {
            "labels": [],
            "datasets": [
                {
                    "label": yAxis,
                    "data": [],
                    "backgroundColor": [],
                }
            ],
            "error": "查询失败，请检查诊断名称或数据库连接"
        }

@router.get("/by-demographic")
async def get_visualization_by_demographic(
    demographic: str = Query(..., description="Demographic filter (male, female, age groups)"),
    xAxis: str = Query("condition_code", description="X-axis variable"),
    yAxis: str = Query("count", description="Y-axis variable"),
    filter: str = Query("all", description="Filter criteria")
):
    """
    Generate visualization data for a specific demographic group
    Shows top diagnoses for the selected demographic
    """
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        # Build demographic filter condition
        demographic_filter = ""
        if demographic == "male":
            demographic_filter = "AND p.gender = 'male'"
        elif demographic == "female":
            demographic_filter = "AND p.gender = 'female'"
        elif demographic == "age_0_18":
            demographic_filter = "AND EXTRACT(YEAR FROM AGE(p.birth_date)) < 18"
        elif demographic == "age_19_35":
            demographic_filter = "AND EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 18 AND 35"
        elif demographic == "age_36_50":
            demographic_filter = "AND EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 36 AND 50"
        elif demographic == "age_51_65":
            demographic_filter = "AND EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 51 AND 65"
        elif demographic == "age_65_plus":
            demographic_filter = "AND EXTRACT(YEAR FROM AGE(p.birth_date)) > 65"
        
        # Identify which axis is the categorical variable and which is the metric
        metrics = ['count', 'average', 'total']
        categories = ['gender', 'age_group', 'condition_code', 'encounter_type', 'date']
        
        # Determine category and metric
        if xAxis in metrics and yAxis in categories:
            category_axis = yAxis
            metric_axis = xAxis
        elif xAxis in categories and yAxis in metrics:
            category_axis = xAxis
            metric_axis = yAxis
        elif xAxis in categories and yAxis in categories:
            category_axis = xAxis
            metric_axis = 'count'
        else:
            category_axis = xAxis
            metric_axis = yAxis
        
        # Build query for this demographic
        if category_axis == "condition_code":
            query = f"""
                SELECT c.code_text as label, COUNT(*) as count
                FROM conditions c
                JOIN patients p ON c.patient_id = p.fhir_id
                WHERE c.code_text IS NOT NULL
                {demographic_filter}
                GROUP BY c.code_text
                ORDER BY count DESC
                LIMIT 10
            """
            df = pd.read_sql(query, engine)
            
        elif category_axis == "age_group":
            # Age distribution within diagnosis (only for gender demographics)
            query = f"""
                SELECT 
                    CASE 
                        WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) < 18 THEN '0-18'
                        WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 18 AND 35 THEN '19-35'
                        WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 36 AND 50 THEN '36-50'
                        WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 51 AND 65 THEN '51-65'
                        ELSE '65+'
                    END as label,
                    COUNT(DISTINCT p.id) as count
                FROM patients p
                JOIN conditions c ON c.patient_id = p.fhir_id
                WHERE p.birth_date IS NOT NULL
                {demographic_filter}
                GROUP BY CASE 
                    WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) < 18 THEN '0-18'
                    WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 18 AND 35 THEN '19-35'
                    WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 36 AND 50 THEN '36-50'
                    WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 51 AND 65 THEN '51-65'
                    ELSE '65+'
                END
                ORDER BY label
            """
            df = pd.read_sql(query, engine)
            
        elif category_axis == "encounter_type":
            # Encounter type distribution for this demographic
            query = f"""
                SELECT e.encounter_class as label, COUNT(*) as count
                FROM encounters e
                JOIN patients p ON e.patient_id = p.fhir_id
                WHERE e.encounter_class IS NOT NULL
                {demographic_filter}
                GROUP BY e.encounter_class
                ORDER BY count DESC
            """
            df = pd.read_sql(query, engine)
            
        else:
            # Return empty data if no matching configuration
            df = pd.DataFrame({
                'label': [],
                'count': []
            })
        
        engine.dispose()
        
        # Format response
        labels = df.iloc[:, 0].tolist() if not df.empty else []
        values = df.iloc[:, 1].tolist() if not df.empty else []
        
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": f"{demographic} - {yAxis}",
                    "data": values,
                    "backgroundColor": [
                        'rgba(37, 99, 235, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                    ] * (len(values) // 5 + 1),
                    "borderColor": [
                        'rgb(37, 99, 235)',
                        'rgb(16, 185, 129)',
                        'rgb(245, 158, 11)',
                        'rgb(239, 68, 68)',
                        'rgb(139, 92, 246)',
                    ] * (len(values) // 5 + 1),
                    "borderWidth": 2,
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"Error generating demographic visualization: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return empty data on error - DO NOT return fake data
        return {
            "labels": [],
            "datasets": [
                {
                    "label": yAxis,
                    "data": [],
                    "backgroundColor": [],
                }
            ],
            "error": "查询失败，请检查筛选条件或数据库连接"
        }

@router.get("")
async def get_visualization_data(
    xAxis: str = Query(..., description="X-axis variable"),
    yAxis: str = Query(..., description="Y-axis variable"),
    filter: str = Query("all", description="Filter criteria")
):
    """
    Generate visualization data based on user-selected axes (Global analysis)
    """
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        # Identify which axis is the categorical variable and which is the metric
        metrics = ['count', 'average', 'total']
        categories = ['gender', 'age_group', 'condition_code', 'encounter_type', 'date']
        
        # Determine category and metric
        if xAxis in metrics and yAxis in categories:
            category_axis = yAxis
            metric_axis = xAxis
        elif xAxis in categories and yAxis in metrics:
            category_axis = xAxis
            metric_axis = yAxis
        elif xAxis in categories and yAxis in categories:
            category_axis = xAxis
            metric_axis = 'count'
        else:
            category_axis = xAxis
            metric_axis = yAxis
        
        # Build query based on the category axis
        if category_axis == "age_group":
            # Age group distribution
            query = """
                SELECT 
                    CASE 
                        WHEN EXTRACT(YEAR FROM AGE(birth_date)) < 18 THEN '0-18'
                        WHEN EXTRACT(YEAR FROM AGE(birth_date)) BETWEEN 18 AND 35 THEN '19-35'
                        WHEN EXTRACT(YEAR FROM AGE(birth_date)) BETWEEN 36 AND 50 THEN '36-50'
                        WHEN EXTRACT(YEAR FROM AGE(birth_date)) BETWEEN 51 AND 65 THEN '51-65'
                        ELSE '65+'
                    END as label,
                    COUNT(*) as count
                FROM patients
                WHERE birth_date IS NOT NULL
                GROUP BY CASE 
                    WHEN EXTRACT(YEAR FROM AGE(birth_date)) < 18 THEN '0-18'
                    WHEN EXTRACT(YEAR FROM AGE(birth_date)) BETWEEN 18 AND 35 THEN '19-35'
                    WHEN EXTRACT(YEAR FROM AGE(birth_date)) BETWEEN 36 AND 50 THEN '36-50'
                    WHEN EXTRACT(YEAR FROM AGE(birth_date)) BETWEEN 51 AND 65 THEN '51-65'
                    ELSE '65+'
                END
                ORDER BY label
            """
            df = pd.read_sql(query, engine)
            
        elif category_axis == "gender":
            # Gender distribution
            query = """
                SELECT gender as label, COUNT(*) as count
                FROM patients
                WHERE gender IS NOT NULL
                GROUP BY gender
            """
            df = pd.read_sql(query, engine)
            
        elif category_axis == "condition_code":
            # Top conditions
            query = """
                SELECT code_text as label, COUNT(*) as count
                FROM conditions
                WHERE code_text IS NOT NULL
                GROUP BY code_text
                ORDER BY count DESC
                LIMIT 10
            """
            df = pd.read_sql(query, engine)
            
        elif category_axis == "date":
            # Time series
            query = """
                SELECT 
                    TO_CHAR(DATE_TRUNC('month', onset_datetime), 'YYYY-MM') as label,
                    COUNT(*) as count
                FROM conditions
                WHERE onset_datetime IS NOT NULL
                GROUP BY DATE_TRUNC('month', onset_datetime)
                ORDER BY DATE_TRUNC('month', onset_datetime)
            """
            df = pd.read_sql(query, engine)
            
        elif category_axis == "encounter_type":
            # Encounter type distribution
            query = """
                SELECT encounter_class as label, COUNT(*) as count
                FROM encounters
                WHERE encounter_class IS NOT NULL
                GROUP BY encounter_class
                ORDER BY count DESC
            """
            df = pd.read_sql(query, engine)
            
        else:
            # Return empty data if no matching axis configuration
            df = pd.DataFrame({
                'label': [],
                'count': []
            })
        
        engine.dispose()
        
        # Format response
        labels = df.iloc[:, 0].tolist()
        values = df.iloc[:, 1].tolist()
        
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": yAxis,
                    "data": values,
                    "backgroundColor": [
                        'rgba(37, 99, 235, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                    ] * (len(values) // 5 + 1),
                    "borderColor": [
                        'rgb(37, 99, 235)',
                        'rgb(16, 185, 129)',
                        'rgb(245, 158, 11)',
                        'rgb(239, 68, 68)',
                        'rgb(139, 92, 246)',
                    ] * (len(values) // 5 + 1),
                    "borderWidth": 2,
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"Error generating visualization: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return empty data on error - DO NOT return fake data for medical software
        return {
            "labels": [],
            "datasets": [
                {
                    "label": yAxis,
                    "data": [],
                    "backgroundColor": [],
                }
            ],
            "error": "查询失败，请检查参数或数据库连接"
        }

