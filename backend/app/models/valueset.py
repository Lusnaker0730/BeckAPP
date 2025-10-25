from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class Valueset(Base):
    __tablename__ = "valuesets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    url = Column(String, unique=True)
    version = Column(String)
    status = Column(String, default="active")  # draft, active, retired
    description = Column(Text)
    code_system = Column(String, index=True)
    codes = Column(JSON)  # Array of code objects
    compose = Column(JSON)
    expansion = Column(JSON)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Valueset(name='{self.name}', code_system='{self.code_system}')>"

