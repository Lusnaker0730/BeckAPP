"""
审计日志数据模型

记录系统中所有重要操作，用于安全审计和合规性要求
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """审计日志模型"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # 时间戳
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # 用户信息
    user_id = Column(String(255), index=True)  # 用户ID
    username = Column(String(255), index=True)  # 用户名
    user_role = Column(String(50))  # 用户角色（admin, engineer, analyst等）
    
    # 操作信息
    action = Column(String(100), nullable=False, index=True)  # 操作类型（login, query, export等）
    resource = Column(String(255), index=True)  # 资源类型（Patient, Condition等）
    resource_id = Column(String(255))  # 资源ID
    
    # 请求信息
    method = Column(String(10))  # HTTP方法（GET, POST等）
    endpoint = Column(String(500))  # API端点
    ip_address = Column(String(45))  # IP地址（支持IPv6）
    user_agent = Column(Text)  # 用户代理
    
    # 操作详情
    status_code = Column(Integer)  # HTTP状态码
    description = Column(Text)  # 操作描述
    request_params = Column(JSON)  # 请求参数（敏感信息需脱敏）
    response_summary = Column(JSON)  # 响应摘要
    
    # 性能信息
    duration_ms = Column(Integer)  # 请求处理时间（毫秒）
    
    # 安全信息
    is_success = Column(String(10))  # 操作是否成功
    error_message = Column(Text)  # 错误信息（如果有）
    
    # 索引优化
    __table_args__ = (
        Index('idx_audit_timestamp_user', 'timestamp', 'user_id'),
        Index('idx_audit_action_resource', 'action', 'resource'),
        Index('idx_audit_timestamp_action', 'timestamp', 'action'),
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user={self.username}, action={self.action}, timestamp={self.timestamp})>"

