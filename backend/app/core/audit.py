"""
审计日志核心功能

提供审计日志记录的工具函数和装饰器
"""

import logging
import time
from typing import Any, Dict, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def create_audit_log(
    db: Session,
    action: str,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    user_role: Optional[str] = None,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    method: Optional[str] = None,
    endpoint: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status_code: Optional[int] = None,
    description: Optional[str] = None,
    request_params: Optional[Dict[str, Any]] = None,
    response_summary: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[int] = None,
    is_success: str = "success",
    error_message: Optional[str] = None,
) -> AuditLog:
    """
    创建审计日志记录

    Args:
        db: 数据库会话
        action: 操作类型（如 'login', 'query_patient', 'export_data'）
        user_id: 用户ID
        username: 用户名
        user_role: 用户角色
        resource: 资源类型
        resource_id: 资源ID
        method: HTTP方法
        endpoint: API端点
        ip_address: IP地址
        user_agent: 用户代理
        status_code: HTTP状态码
        description: 操作描述
        request_params: 请求参数（敏感信息需脱敏）
        response_summary: 响应摘要
        duration_ms: 处理时间（毫秒）
        is_success: 操作是否成功
        error_message: 错误信息

    Returns:
        创建的审计日志对象
    """
    try:
        # 脱敏处理：移除敏感字段
        safe_params = sanitize_params(request_params) if request_params else None

        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            user_role=user_role,
            action=action,
            resource=resource,
            resource_id=resource_id,
            method=method,
            endpoint=endpoint,
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=status_code,
            description=description,
            request_params=safe_params,
            response_summary=response_summary,
            duration_ms=duration_ms,
            is_success=is_success,
            error_message=error_message,
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        db.rollback()
        # 审计日志失败不应该影响主业务，只记录错误
        return None


def sanitize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    脱敏处理：移除或掩码敏感字段

    Args:
        params: 原始参数字典

    Returns:
        脱敏后的参数字典
    """
    if not params:
        return {}

    # 敏感字段列表
    sensitive_fields = [
        "password",
        "token",
        "secret",
        "api_key",
        "apikey",
        "authorization",
        "credit_card",
        "ssn",
        "social_security",
    ]

    sanitized = {}
    for key, value in params.items():
        # 检查是否是敏感字段（不区分大小写）
        if any(field in key.lower() for field in sensitive_fields):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_params(value)
        elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            sanitized[key] = [sanitize_params(item) for item in value]
        else:
            # 限制字符串长度，避免日志过大
            if isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "...(truncated)"
            else:
                sanitized[key] = value

    return sanitized


def get_client_ip(request: Request) -> str:
    """
    获取客户端真实IP地址

    Args:
        request: FastAPI请求对象

    Returns:
        IP地址字符串
    """
    # 优先从X-Forwarded-For获取（通过代理）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 可能有多个IP，取第一个
        return forwarded_for.split(",")[0].strip()

    # 其次从X-Real-IP获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 最后从客户端直接获取
    if request.client:
        return request.client.host

    return "unknown"


def log_authentication(
    db: Session,
    username: str,
    action: str,
    is_success: str,
    ip_address: str,
    user_agent: str,
    error_message: Optional[str] = None,
):
    """
    记录认证相关操作（登录、登出）

    Args:
        db: 数据库会话
        username: 用户名
        action: 操作类型（'login', 'logout'）
        is_success: 是否成功
        ip_address: IP地址
        user_agent: 用户代理
        error_message: 错误信息
    """
    create_audit_log(
        db=db,
        action=action,
        username=username,
        description=f"User {action}: {username}",
        ip_address=ip_address,
        user_agent=user_agent,
        is_success=is_success,
        error_message=error_message,
    )


def log_data_access(
    db: Session,
    user_id: str,
    username: str,
    user_role: str,
    resource: str,
    action: str,
    resource_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    request_params: Optional[Dict[str, Any]] = None,
    response_summary: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[int] = None,
):
    """
    记录数据访问操作

    Args:
        db: 数据库会话
        user_id: 用户ID
        username: 用户名
        user_role: 用户角色
        resource: 资源类型
        action: 操作类型
        resource_id: 资源ID
        endpoint: API端点
        method: HTTP方法
        status_code: 状态码
        request_params: 请求参数
        response_summary: 响应摘要
        duration_ms: 处理时间
    """
    create_audit_log(
        db=db,
        action=action,
        user_id=user_id,
        username=username,
        user_role=user_role,
        resource=resource,
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        request_params=request_params,
        response_summary=response_summary,
        duration_ms=duration_ms,
        is_success="success" if status_code and status_code < 400 else "failure",
    )


def log_system_event(
    db: Session,
    action: str,
    description: str,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
):
    """
    记录系统事件（ETL作业、系统配置更改等）

    Args:
        db: 数据库会话
        action: 操作类型
        description: 事件描述
        user_id: 用户ID（如果有）
        username: 用户名（如果有）
        details: 事件详情
    """
    create_audit_log(
        db=db,
        action=action,
        user_id=user_id,
        username=username,
        description=description,
        request_params=details,
    )
