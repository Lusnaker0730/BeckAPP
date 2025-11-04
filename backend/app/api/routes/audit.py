"""
审计日志API端点

提供查询、过滤和导出审计日志的功能
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.audit_log import AuditLog

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/logs")
@require_role(["admin"])  # 只有管理员可以查看审计日志
async def get_audit_logs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=500, description="返回记录数"),
    user_id: Optional[str] = Query(None, description="按用户ID过滤"),
    username: Optional[str] = Query(None, description="按用户名过滤"),
    action: Optional[str] = Query(None, description="按操作类型过滤"),
    resource: Optional[str] = Query(None, description="按资源类型过滤"),
    is_success: Optional[str] = Query(None, description="按成功/失败过滤"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    ip_address: Optional[str] = Query(None, description="按IP地址过滤"),
    search: Optional[str] = Query(None, description="全文搜索（描述、端点）")
):
    """
    获取审计日志列表
    
    支持多种过滤条件和分页
    """
    try:
        # 构建查询
        query = db.query(AuditLog)
        
        # 应用过滤条件
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if username:
            query = query.filter(AuditLog.username.ilike(f"%{username}%"))
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if resource:
            query = query.filter(AuditLog.resource == resource)
        
        if is_success:
            query = query.filter(AuditLog.is_success == is_success)
        
        if ip_address:
            query = query.filter(AuditLog.ip_address == ip_address)
        
        # 日期范围过滤
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(AuditLog.timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date) + timedelta(days=1)
            query = query.filter(AuditLog.timestamp < end_dt)
        
        # 全文搜索
        if search:
            search_filter = or_(
                AuditLog.description.ilike(f"%{search}%"),
                AuditLog.endpoint.ilike(f"%{search}%"),
                AuditLog.error_message.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # 获取总数
        total = query.count()
        
        # 按时间倒序排序并分页
        logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
        
        # 转换为字典
        logs_data = []
        for log in logs:
            logs_data.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "user_id": log.user_id,
                "username": log.username,
                "user_role": log.user_role,
                "action": log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "method": log.method,
                "endpoint": log.endpoint,
                "ip_address": log.ip_address,
                "status_code": log.status_code,
                "description": log.description,
                "duration_ms": log.duration_ms,
                "is_success": log.is_success,
                "error_message": log.error_message
            })
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "logs": logs_data
        }
    
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{log_id}")
@require_role(["admin"])
async def get_audit_log_detail(
    log_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单条审计日志的详细信息"""
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    return {
        "id": log.id,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "user_id": log.user_id,
        "username": log.username,
        "user_role": log.user_role,
        "action": log.action,
        "resource": log.resource,
        "resource_id": log.resource_id,
        "method": log.method,
        "endpoint": log.endpoint,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "status_code": log.status_code,
        "description": log.description,
        "request_params": log.request_params,
        "response_summary": log.response_summary,
        "duration_ms": log.duration_ms,
        "is_success": log.is_success,
        "error_message": log.error_message
    }


@router.get("/stats")
@require_role(["admin"])
async def get_audit_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=90, description="统计天数")
):
    """
    获取审计日志统计信息
    
    包括：总操作数、失败操作数、活跃用户数、热门操作等
    """
    try:
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 总操作数
        total_operations = db.query(func.count(AuditLog.id)).filter(
            AuditLog.timestamp >= start_date
        ).scalar()
        
        # 失败操作数
        failed_operations = db.query(func.count(AuditLog.id)).filter(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.is_success == "failure"
            )
        ).scalar()
        
        # 活跃用户数
        active_users = db.query(func.count(func.distinct(AuditLog.user_id))).filter(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.user_id.isnot(None)
            )
        ).scalar()
        
        # 按操作类型统计
        operations_by_action = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.timestamp >= start_date
        ).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).limit(10).all()
        
        # 按资源类型统计
        operations_by_resource = db.query(
            AuditLog.resource,
            func.count(AuditLog.id).label('count')
        ).filter(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.resource.isnot(None)
            )
        ).group_by(AuditLog.resource).order_by(func.count(AuditLog.id).desc()).limit(10).all()
        
        # 最活跃用户
        top_users = db.query(
            AuditLog.username,
            func.count(AuditLog.id).label('count')
        ).filter(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.username.isnot(None)
            )
        ).group_by(AuditLog.username).order_by(func.count(AuditLog.id).desc()).limit(10).all()
        
        # 每日操作趋势
        daily_operations = db.query(
            func.date(AuditLog.timestamp).label('date'),
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.timestamp >= start_date
        ).group_by(func.date(AuditLog.timestamp)).order_by(func.date(AuditLog.timestamp)).all()
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "summary": {
                "total_operations": total_operations or 0,
                "failed_operations": failed_operations or 0,
                "success_rate": round((1 - (failed_operations or 0) / (total_operations or 1)) * 100, 2),
                "active_users": active_users or 0
            },
            "by_action": [{"action": action, "count": count} for action, count in operations_by_action],
            "by_resource": [{"resource": resource, "count": count} for resource, count in operations_by_resource],
            "top_users": [{"username": username, "operations": count} for username, count in top_users],
            "daily_trend": [{"date": str(date), "operations": count} for date, count in daily_operations]
        }
    
    except Exception as e:
        logger.error(f"Error fetching audit stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions")
@require_role(["admin"])
async def get_available_actions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有可用的操作类型（用于过滤器）"""
    actions = db.query(AuditLog.action).distinct().all()
    return [action[0] for action in actions if action[0]]


@router.get("/resources")
@require_role(["admin"])
async def get_available_resources(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有可用的资源类型（用于过滤器）"""
    resources = db.query(AuditLog.resource).distinct().all()
    return [resource[0] for resource in resources if resource[0]]

