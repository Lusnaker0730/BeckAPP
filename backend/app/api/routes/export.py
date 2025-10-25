from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import json
from io import BytesIO, StringIO
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.fhir_resources import Patient, Condition, Encounter, Observation

router = APIRouter()

class ExportConfig(BaseModel):
    dataType: str
    format: str
    dateFrom: Optional[str] = None
    dateTo: Optional[str] = None
    includeFields: dict

@router.post("")
async def export_data(
    config: ExportConfig,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export FHIR data in various formats"""
    
    # Fetch data based on dataType
    if config.dataType == "patients":
        query = db.query(Patient)
        if config.dateFrom:
            query = query.filter(Patient.created_at >= config.dateFrom)
        if config.dateTo:
            query = query.filter(Patient.created_at <= config.dateTo)
        data = query.all()
        
        # Convert to dict
        records = []
        for patient in data:
            record = {
                "fhir_id": patient.fhir_id,
                "gender": patient.gender,
                "birth_date": str(patient.birth_date) if patient.birth_date else None,
            }
            if config.includeFields.get("patient"):
                record.update({
                    "name": patient.name,
                    "address": patient.address,
                })
            records.append(record)
    
    elif config.dataType == "conditions":
        query = db.query(Condition)
        if config.dateFrom:
            query = query.filter(Condition.onset_datetime >= config.dateFrom)
        if config.dateTo:
            query = query.filter(Condition.onset_datetime <= config.dateTo)
        data = query.all()
        
        records = []
        for condition in data:
            record = {
                "fhir_id": condition.fhir_id,
                "patient_id": condition.patient_id,
                "code_text": condition.code_text,
                "clinical_status": condition.clinical_status,
                "onset_datetime": str(condition.onset_datetime) if condition.onset_datetime else None,
            }
            records.append(record)
    
    elif config.dataType == "encounters":
        query = db.query(Encounter)
        if config.dateFrom:
            query = query.filter(Encounter.period_start >= config.dateFrom)
        if config.dateTo:
            query = query.filter(Encounter.period_start <= config.dateTo)
        data = query.all()
        
        records = []
        for encounter in data:
            record = {
                "fhir_id": encounter.fhir_id,
                "patient_id": encounter.patient_id,
                "status": encounter.status,
                "encounter_class": encounter.encounter_class,
                "period_start": str(encounter.period_start) if encounter.period_start else None,
            }
            records.append(record)
    
    elif config.dataType == "observations":
        query = db.query(Observation)
        if config.dateFrom:
            query = query.filter(Observation.effective_datetime >= config.dateFrom)
        if config.dateTo:
            query = query.filter(Observation.effective_datetime <= config.dateTo)
        data = query.all()
        
        records = []
        for obs in data:
            record = {
                "fhir_id": obs.fhir_id,
                "patient_id": obs.patient_id,
                "code_text": obs.code_text,
                "value": obs.value,
                "effective_datetime": str(obs.effective_datetime) if obs.effective_datetime else None,
            }
            records.append(record)
    
    else:  # combined
        # Create a combined report
        records = [
            {
                "type": "summary",
                "total_patients": db.query(Patient).count(),
                "total_conditions": db.query(Condition).count(),
                "total_encounters": db.query(Encounter).count(),
            }
        ]
    
    # Convert to requested format
    df = pd.DataFrame(records)
    
    if config.format == "csv":
        output = StringIO()
        df.to_csv(output, index=False)
        content = output.getvalue().encode('utf-8')
        media_type = "text/csv"
        filename = f"fhir_export_{config.dataType}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    elif config.format == "json":
        content = json.dumps(records, indent=2, default=str).encode('utf-8')
        media_type = "application/json"
        filename = f"fhir_export_{config.dataType}_{datetime.now().strftime('%Y%m%d')}.json"
    
    elif config.format == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=config.dataType)
        content = output.getvalue()
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"fhir_export_{config.dataType}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    elif config.format == "parquet":
        output = BytesIO()
        df.to_parquet(output, index=False)
        content = output.getvalue()
        media_type = "application/octet-stream"
        filename = f"fhir_export_{config.dataType}_{datetime.now().strftime('%Y%m%d')}.parquet"
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
    
    return StreamingResponse(
        BytesIO(content),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

