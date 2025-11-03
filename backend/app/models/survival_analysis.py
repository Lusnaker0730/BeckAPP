"""
Survival Analysis Models

用於存活分析的數據模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class SurvivalCohort(Base):
    """存活分析群組"""
    __tablename__ = "survival_cohorts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # 定義條件
    inclusion_criteria = Column(JSON)  # 納入條件
    exclusion_criteria = Column(JSON)  # 排除條件
    
    # 時間定義
    start_event = Column(String(100))  # 起始事件（如：診斷、治療開始）
    end_event = Column(String(100))    # 結束事件（如：死亡、復發）
    
    # 追蹤期間
    follow_up_start = Column(DateTime(timezone=True))
    follow_up_end = Column(DateTime(timezone=True))
    
    # 分析結果（可以快取複雜分析結果）
    analysis_results = Column(JSON)
    
    # 元數據
    created_by = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)


class SurvivalEvent(Base):
    """存活分析事件記錄"""
    __tablename__ = "survival_events"
    
    id = Column(Integer, primary_key=True, index=True)
    cohort_id = Column(Integer, index=True)
    patient_id = Column(String(255), index=True)
    
    # 時間點
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    end_date = Column(DateTime(timezone=True), index=True)
    
    # 存活時間（天數）
    duration_days = Column(Float)
    
    # 事件狀態
    event_occurred = Column(Boolean, default=False)  # True: 事件發生, False: 被審查（censored）
    event_type = Column(String(100))  # 事件類型
    
    # 協變量（用於分層分析）
    age_group = Column(String(50))
    gender = Column(String(50))
    diagnosis = Column(String(255))
    treatment = Column(String(255))
    covariates = Column(JSON)  # 其他協變量
    
    # 元數據
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

