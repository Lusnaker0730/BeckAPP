"""
审计日志中间件

自动记录所有API请求的审计日志
"""

import logging
import time

from fastapi import Request, Response
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.audit import create_audit_log, get_client_ip, sanitize_params
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    审计日志中间件

    记录所有API请求的详细信息用于审计
    """

    # 不需要审计的端点（静态资源、健康检查等）
    SKIP_PATHS = ["/docs", "/redoc", "/openapi.json", "/favicon.ico", "/static", "/health"]

    # 敏感端点（需要特别关注）
    SENSITIVE_ENDPOINTS = [
        "/api/auth/login",
        "/api/auth/register",
        "/api/export",
        "/api/admin",
        "/api/analytics/patients",
        "/api/analytics/conditions",
    ]

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """处理请求并记录审计日志"""

        # 检查是否需要跳过审计
        if self._should_skip_audit(request.url.path):
            return await call_next(request)

        # 记录开始时间
        start_time = time.time()

        # 获取请求信息
        method = request.method
        endpoint = str(request.url.path)
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "Unknown")

        # 获取用户信息（如果已认证）
        user_id = None
        username = None
        user_role = None

        if hasattr(request.state, "user"):
            user = request.state.user
            user_id = user.get("sub")
            username = user.get("username")
            user_role = user.get("role")

        # 执行请求
        response = None
        status_code = None
        error_message = None

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            error_message = str(e)
            logger.error(f"Request failed: {e}")
            raise
        finally:
            # 计算处理时间
            duration_ms = int((time.time() - start_time) * 1000)

            # 异步记录审计日志（不阻塞响应）
            try:
                self._create_audit_log_async(
                    method=method,
                    endpoint=endpoint,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    user_id=user_id,
                    username=username,
                    user_role=user_role,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    error_message=error_message,
                    request=request,
                )
            except Exception as e:
                # 审计日志失败不应影响主请求
                logger.error(f"Failed to create audit log: {e}")

        return response

    def _should_skip_audit(self, path: str) -> bool:
        """判断是否应该跳过审计"""
        for skip_path in self.SKIP_PATHS:
            if path.startswith(skip_path):
                return True
        return False

    def _is_sensitive_endpoint(self, path: str) -> bool:
        """判断是否是敏感端点"""
        for sensitive_path in self.SENSITIVE_ENDPOINTS:
            if path.startswith(sensitive_path):
                return True
        return False

    def _create_audit_log_async(
        self,
        method: str,
        endpoint: str,
        ip_address: str,
        user_agent: str,
        user_id: str,
        username: str,
        user_role: str,
        status_code: int,
        duration_ms: int,
        error_message: str,
        request: Request,
    ):
        """异步创建审计日志"""
        db: Session = SessionLocal()

        try:
            # 确定操作类型
            action = self._determine_action(method, endpoint)

            # 确定资源类型
            resource = self._determine_resource(endpoint)

            # 获取请求参数（仅记录查询参数，不记录body以保护隐私）
            request_params = None
            if self._is_sensitive_endpoint(endpoint):
                # 敏感端点记录更多信息
                request_params = {
                    "query_params": dict(request.query_params),
                    "path_params": (
                        dict(request.path_params) if hasattr(request, "path_params") else {}
                    ),
                }

            # 生成描述
            description = f"{method} {endpoint}"
            if username:
                description = f"User '{username}' performed {method} on {endpoint}"

            # 创建审计日志
            create_audit_log(
                db=db,
                action=action,
                user_id=user_id,
                username=username,
                user_role=user_role,
                resource=resource,
                method=method,
                endpoint=endpoint,
                ip_address=ip_address,
                user_agent=user_agent,
                status_code=status_code,
                description=description,
                request_params=request_params,
                duration_ms=duration_ms,
                is_success="success" if status_code < 400 else "failure",
                error_message=error_message,
            )
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
        finally:
            db.close()

    def _determine_action(self, method: str, endpoint: str) -> str:
        """根据HTTP方法和端点确定操作类型"""
        if "/auth/login" in endpoint:
            return "login"
        elif "/auth/logout" in endpoint:
            return "logout"
        elif "/export" in endpoint:
            return "export_data"
        elif "/admin" in endpoint:
            return "admin_operation"
        elif method == "GET":
            if "/patients" in endpoint or "/conditions" in endpoint:
                return "query_data"
            return "view"
        elif method == "POST":
            return "create"
        elif method == "PUT" or method == "PATCH":
            return "update"
        elif method == "DELETE":
            return "delete"
        else:
            return "unknown"

    def _determine_resource(self, endpoint: str) -> str:
        """根据端点确定资源类型"""
        if "/patients" in endpoint:
            return "Patient"
        elif "/conditions" in endpoint:
            return "Condition"
        elif "/encounters" in endpoint:
            return "Encounter"
        elif "/observations" in endpoint:
            return "Observation"
        elif "/etl" in endpoint:
            return "ETL_Job"
        elif "/reports" in endpoint:
            return "Report"
        elif "/cohorts" in endpoint:
            return "Cohort"
        elif "/survival" in endpoint:
            return "Survival_Analysis"
        elif "/auth" in endpoint:
            return "Authentication"
        else:
            return "System"
