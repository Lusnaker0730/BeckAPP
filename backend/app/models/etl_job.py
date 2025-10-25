from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.core.database import Base

class ETLJob(Base):
    __tablename__ = "etl_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    resource_type = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    fhir_server_url = Column(String)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_log = Column(Text)
    config = Column(JSON)
    result = Column(JSON)
    created_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ETLJob(job_id='{self.job_id}', status='{self.status}')>"

