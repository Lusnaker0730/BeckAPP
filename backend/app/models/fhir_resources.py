from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    fhir_id = Column(String, unique=True, index=True, nullable=False)
    identifier = Column(JSON)
    name = Column(JSON)
    gender = Column(String)
    birth_date = Column(DateTime)
    address = Column(JSON)
    telecom = Column(JSON)
    marital_status = Column(String)
    raw_data = Column(JSON)
    job_id = Column(String, index=True, nullable=True)  # Track which ETL job loaded this record
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Condition(Base):
    __tablename__ = "conditions"
    
    id = Column(Integer, primary_key=True, index=True)
    fhir_id = Column(String, unique=True, index=True, nullable=False)
    patient_id = Column(String, ForeignKey("patients.fhir_id"), index=True)
    code = Column(JSON)
    code_text = Column(String)
    category = Column(JSON)
    clinical_status = Column(String)
    verification_status = Column(String)
    severity = Column(String)
    onset_datetime = Column(DateTime, index=True)
    recorded_date = Column(DateTime, index=True)
    encounter_id = Column(String)
    raw_data = Column(JSON)
    job_id = Column(String, index=True, nullable=True)  # Track which ETL job loaded this record
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Encounter(Base):
    __tablename__ = "encounters"
    
    id = Column(Integer, primary_key=True, index=True)
    fhir_id = Column(String, unique=True, index=True, nullable=False)
    patient_id = Column(String, ForeignKey("patients.fhir_id"), index=True)
    status = Column(String)
    encounter_class = Column(String)
    type = Column(JSON)
    service_type = Column(String)
    priority = Column(String)
    period_start = Column(DateTime, index=True)
    period_end = Column(DateTime)
    reason_code = Column(JSON)
    diagnosis = Column(JSON)
    location = Column(JSON)
    raw_data = Column(JSON)
    job_id = Column(String, index=True, nullable=True)  # Track which ETL job loaded this record
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Observation(Base):
    __tablename__ = "observations"
    
    id = Column(Integer, primary_key=True, index=True)
    fhir_id = Column(String, unique=True, index=True, nullable=False)
    patient_id = Column(String, ForeignKey("patients.fhir_id"), index=True)
    encounter_id = Column(String)
    status = Column(String)
    category = Column(JSON)
    code = Column(JSON)
    code_text = Column(String)
    value = Column(JSON)
    value_quantity = Column(JSON)
    effective_datetime = Column(DateTime, index=True)
    issued = Column(DateTime)
    interpretation = Column(JSON)
    raw_data = Column(JSON)
    job_id = Column(String, index=True, nullable=True)  # Track which ETL job loaded this record
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

