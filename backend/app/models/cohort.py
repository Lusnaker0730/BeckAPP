"""
Cohort Analysis Models
患者群组分析数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Cohort(Base):
    """
    Patient Cohort Model
    患者群组模型
    """
    __tablename__ = "cohorts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True, comment="群组名称")
    description = Column(Text, comment="群组描述")
    
    # Criteria (stored as JSON)
    criteria = Column(JSON, nullable=False, comment="筛选条件 JSON")
    # Example criteria structure:
    # {
    #   "age_min": 18,
    #   "age_max": 65,
    #   "gender": "male",
    #   "conditions": ["Hypertension", "Diabetes"],
    #   "date_range": {"start": "2020-01-01", "end": "2023-12-31"}
    # }
    
    # Metadata
    created_by = Column(String(255), nullable=False, comment="创建者")
    patient_count = Column(Integer, default=0, comment="患者数量")
    last_calculated = Column(DateTime(timezone=True), comment="最后计算时间")
    
    # Status
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Cohort(id={self.id}, name='{self.name}', patients={self.patient_count})>"


class CohortComparison(Base):
    """
    Cohort Comparison Model
    群组对比分析模型
    """
    __tablename__ = "cohort_comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="对比分析名称")
    description = Column(Text, comment="对比描述")
    
    # Cohorts being compared
    cohort_ids = Column(JSON, nullable=False, comment="对比的群组ID列表")
    
    # Analysis type
    analysis_type = Column(
        String(50), 
        nullable=False, 
        comment="分析类型: outcomes, demographics, trends, costs"
    )
    
    # Results (stored as JSON)
    results = Column(JSON, comment="分析结果")
    
    # Metadata
    created_by = Column(String(255), nullable=False, comment="创建者")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CohortComparison(id={self.id}, name='{self.name}')>"

