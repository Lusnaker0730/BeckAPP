"""
Automated Report Models
自动化报告数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ReportType(str, enum.Enum):
    """报告类型"""
    SUMMARY = "summary"  # 摘要报告
    QUALITY = "quality"  # 质量报告
    OPERATIONAL = "operational"  # 运营报告
    CLINICAL = "clinical"  # 临床报告
    COMPLIANCE = "compliance"  # 合规报告
    CUSTOM = "custom"  # 自定义报告


class ReportFormat(str, enum.Enum):
    """报告格式"""
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    EXCEL = "excel"


class ReportFrequency(str, enum.Enum):
    """报告频率"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ON_DEMAND = "on_demand"


class ReportTemplate(Base):
    """
    Report Template Model
    报告模板
    """
    __tablename__ = "report_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    
    # Report configuration
    report_type = Column(String(50), nullable=False)
    format = Column(String(20), nullable=False, default="pdf")
    
    # Template structure (JSON)
    # {
    #   "sections": [
    #     {"type": "header", "title": "Monthly Report"},
    #     {"type": "summary_stats"},
    #     {"type": "chart", "chart_type": "bar", "data_source": "top_conditions"},
    #     {"type": "table", "data_source": "patient_demographics"}
    #   ],
    #   "styling": {...}
    # }
    template_config = Column(JSON, nullable=False)
    
    # Metadata
    created_by = Column(String(255), nullable=False)
    is_system = Column(Boolean, default=False, comment="系统内置模板")
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ReportTemplate(id={self.id}, name='{self.name}', type='{self.report_type}')>"


class ScheduledReport(Base):
    """
    Scheduled Report Model
    计划报告
    """
    __tablename__ = "scheduled_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Template reference
    template_id = Column(Integer, nullable=False, comment="报告模板ID")
    
    # Schedule configuration
    frequency = Column(String(20), nullable=False)
    schedule_config = Column(JSON, comment="调度配置: cron表达式, 时间等")
    # Example: {"cron": "0 8 * * 1", "timezone": "UTC", "day_of_week": "monday"}
    
    # Email configuration
    recipients = Column(JSON, nullable=False, comment="收件人邮箱列表")
    # Example: ["admin@example.com", "manager@example.com"]
    
    email_subject = Column(String(255))
    email_body = Column(Text)
    
    # Filters (optional)
    report_filters = Column(JSON, comment="报告数据过滤条件")
    # Example: {"date_range": "last_30_days", "job_id": "specific_job"}
    
    # Status
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True), comment="最后执行时间")
    next_run_at = Column(DateTime(timezone=True), comment="下次执行时间")
    
    # Metadata
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ScheduledReport(id={self.id}, name='{self.name}', frequency='{self.frequency}')>"


class GeneratedReport(Base):
    """
    Generated Report Model
    已生成的报告记录
    """
    __tablename__ = "generated_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    
    # Reference
    template_id = Column(Integer, comment="模板ID")
    scheduled_report_id = Column(Integer, comment="计划报告ID (如果是定时生成的)")
    
    # Report details
    report_type = Column(String(50), nullable=False)
    format = Column(String(20), nullable=False)
    
    # File storage
    file_path = Column(String(500), comment="文件存储路径")
    file_size = Column(Integer, comment="文件大小 (bytes)")
    
    # Report data (for JSON reports or metadata)
    report_data = Column(JSON)
    
    # Generation metadata
    generated_by = Column(String(255), nullable=False)
    generation_time_seconds = Column(Integer, comment="生成耗时(秒)")
    
    # Status
    status = Column(String(20), default="completed", comment="completed, failed, processing")
    error_message = Column(Text, comment="错误信息 (如果失败)")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), comment="过期时间")
    
    def __repr__(self):
        return f"<GeneratedReport(id={self.id}, name='{self.name}', status='{self.status}')>"

