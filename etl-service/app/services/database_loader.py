import json
import logging
from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseLoader:
    """Load transformed FHIR data into PostgreSQL"""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    async def load_file(self, json_file: str, resource_type: str, job_id: str = None) -> Dict[str, Any]:
        """Load a JSON file into the database"""
        
        with open(json_file, 'r', encoding='utf-8') as f:
            records = json.load(f)
        
        loaded = 0
        failed = 0
        
        session = self.SessionLocal()
        
        try:
            for record in records:
                try:
                    if resource_type == "Patient":
                        self._load_patient(session, record, job_id)
                    elif resource_type == "Condition":
                        self._load_condition(session, record, job_id)
                    elif resource_type == "Encounter":
                        self._load_encounter(session, record, job_id)
                    elif resource_type == "Observation":
                        self._load_observation(session, record, job_id)
                    
                    loaded += 1
                except Exception as e:
                    logger.error(f"Error loading record: {e}")
                    failed += 1
            
            session.commit()
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error committing transaction: {e}")
            raise
        
        finally:
            session.close()
        
        return {
            "loaded": loaded,
            "failed": failed
        }
    
    def _load_patient(self, session, record: Dict[str, Any], job_id: str = None):
        """Load Patient record"""
        from sqlalchemy import text
        
        # Use raw SQL for simplicity (in production, use ORM models)
        sql = text("""
            INSERT INTO patients (fhir_id, identifier, name, gender, birth_date, address, telecom, marital_status, raw_data, job_id, created_at)
            VALUES (:fhir_id, :identifier, :name, :gender, :birth_date, :address, :telecom, :marital_status, :raw_data, :job_id, :created_at)
            ON CONFLICT (fhir_id) DO UPDATE SET
                identifier = EXCLUDED.identifier,
                name = EXCLUDED.name,
                gender = EXCLUDED.gender,
                birth_date = EXCLUDED.birth_date,
                address = EXCLUDED.address,
                telecom = EXCLUDED.telecom,
                marital_status = EXCLUDED.marital_status,
                raw_data = EXCLUDED.raw_data,
                job_id = EXCLUDED.job_id,
                updated_at = CURRENT_TIMESTAMP
        """)
        
        session.execute(sql, {
            "fhir_id": record["fhir_id"],
            "identifier": json.dumps(record.get("identifier")),
            "name": json.dumps(record.get("name")),
            "gender": record.get("gender"),
            "birth_date": self._parse_date(record.get("birth_date")),
            "address": json.dumps(record.get("address")),
            "telecom": json.dumps(record.get("telecom")),
            "marital_status": record.get("marital_status"),
            "raw_data": json.dumps(record.get("raw_data")),
            "job_id": job_id,
            "created_at": datetime.now()
        })
    
    def _load_condition(self, session, record: Dict[str, Any], job_id: str = None):
        """Load Condition record"""
        from sqlalchemy import text
        
        sql = text("""
            INSERT INTO conditions (fhir_id, patient_id, code, code_text, category, clinical_status, 
                                   verification_status, severity, onset_datetime, recorded_date, 
                                   encounter_id, raw_data, job_id, created_at)
            VALUES (:fhir_id, :patient_id, :code, :code_text, :category, :clinical_status,
                    :verification_status, :severity, :onset_datetime, :recorded_date,
                    :encounter_id, :raw_data, :job_id, :created_at)
            ON CONFLICT (fhir_id) DO UPDATE SET
                patient_id = EXCLUDED.patient_id,
                code = EXCLUDED.code,
                code_text = EXCLUDED.code_text,
                job_id = EXCLUDED.job_id,
                updated_at = CURRENT_TIMESTAMP
        """)
        
        session.execute(sql, {
            "fhir_id": record["fhir_id"],
            "patient_id": record.get("patient_id"),
            "code": json.dumps(record.get("code")),
            "code_text": record.get("code_text"),
            "category": json.dumps(record.get("category")),
            "clinical_status": record.get("clinical_status"),
            "verification_status": record.get("verification_status"),
            "severity": record.get("severity"),
            "onset_datetime": self._parse_datetime(record.get("onset_datetime")),
            "recorded_date": self._parse_datetime(record.get("recorded_date")),
            "encounter_id": record.get("encounter_id"),
            "raw_data": json.dumps(record.get("raw_data")),
            "job_id": job_id,
            "created_at": datetime.now()
        })
    
    def _load_encounter(self, session, record: Dict[str, Any], job_id: str = None):
        """Load Encounter record"""
        from sqlalchemy import text
        
        sql = text("""
            INSERT INTO encounters (fhir_id, patient_id, status, encounter_class, type, service_type,
                                   priority, period_start, period_end, reason_code, diagnosis, location,
                                   raw_data, job_id, created_at)
            VALUES (:fhir_id, :patient_id, :status, :encounter_class, :type, :service_type,
                    :priority, :period_start, :period_end, :reason_code, :diagnosis, :location,
                    :raw_data, :job_id, :created_at)
            ON CONFLICT (fhir_id) DO UPDATE SET
                status = EXCLUDED.status,
                job_id = EXCLUDED.job_id,
                updated_at = CURRENT_TIMESTAMP
        """)
        
        session.execute(sql, {
            "fhir_id": record["fhir_id"],
            "patient_id": record.get("patient_id"),
            "status": record.get("status"),
            "encounter_class": record.get("encounter_class"),
            "type": json.dumps(record.get("type")),
            "service_type": record.get("service_type"),
            "priority": record.get("priority"),
            "period_start": self._parse_datetime(record.get("period_start")),
            "period_end": self._parse_datetime(record.get("period_end")),
            "reason_code": json.dumps(record.get("reason_code")),
            "diagnosis": json.dumps(record.get("diagnosis")),
            "location": json.dumps(record.get("location")),
            "raw_data": json.dumps(record.get("raw_data")),
            "job_id": job_id,
            "created_at": datetime.now()
        })
    
    def _load_observation(self, session, record: Dict[str, Any], job_id: str = None):
        """Load Observation record"""
        from sqlalchemy import text
        
        sql = text("""
            INSERT INTO observations (fhir_id, patient_id, encounter_id, status, category, code,
                                     code_text, value, value_quantity, effective_datetime, issued,
                                     interpretation, raw_data, job_id, created_at)
            VALUES (:fhir_id, :patient_id, :encounter_id, :status, :category, :code,
                    :code_text, :value, :value_quantity, :effective_datetime, :issued,
                    :interpretation, :raw_data, :job_id, :created_at)
            ON CONFLICT (fhir_id) DO UPDATE SET
                value = EXCLUDED.value,
                job_id = EXCLUDED.job_id,
                updated_at = CURRENT_TIMESTAMP
        """)
        
        session.execute(sql, {
            "fhir_id": record["fhir_id"],
            "patient_id": record.get("patient_id"),
            "encounter_id": record.get("encounter_id"),
            "status": record.get("status"),
            "category": json.dumps(record.get("category")),
            "code": json.dumps(record.get("code")),
            "code_text": record.get("code_text"),
            "value": json.dumps(record.get("value")),
            "value_quantity": json.dumps(record.get("value_quantity")),
            "effective_datetime": self._parse_datetime(record.get("effective_datetime")),
            "issued": self._parse_datetime(record.get("issued")),
            "interpretation": json.dumps(record.get("interpretation")),
            "raw_data": json.dumps(record.get("raw_data")),
            "job_id": job_id,
            "created_at": datetime.now()
        })
    
    def _parse_date(self, date_str: str):
        """Parse date string"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        except:
            return None
    
    def _parse_datetime(self, datetime_str: str):
        """Parse datetime string"""
        if not datetime_str:
            return None
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except:
            return None

