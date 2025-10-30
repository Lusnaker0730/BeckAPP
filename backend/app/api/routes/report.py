"""
Automated Report Generation API Routes
自动化报告生成 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
import logging
import json
import io
import os

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.report import (
    ReportTemplate, ScheduledReport, GeneratedReport,
    ReportType, ReportFormat, ReportFrequency
)
from app.models.fhir_resources import Patient, Condition, Encounter, Observation

router = APIRouter()
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Schemas
# ============================================================================

class TemplateConfig(BaseModel):
    """模板配置"""
    sections: List[Dict[str, Any]]
    styling: Optional[Dict[str, Any]] = {}


class TemplateCreate(BaseModel):
    """创建报告模板"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    report_type: str
    format: str = "pdf"
    template_config: TemplateConfig


class TemplateResponse(BaseModel):
    """报告模板响应"""
    id: int
    name: str
    description: Optional[str]
    report_type: str
    format: str
    template_config: Dict[str, Any]
    created_by: str
    is_system: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduledReportCreate(BaseModel):
    """创建计划报告"""
    name: str
    description: Optional[str] = None
    template_id: int
    frequency: str
    schedule_config: Optional[Dict[str, Any]] = {}
    recipients: List[EmailStr]
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    report_filters: Optional[Dict[str, Any]] = {}


class ScheduledReportResponse(BaseModel):
    """计划报告响应"""
    id: int
    name: str
    description: Optional[str]
    template_id: int
    frequency: str
    schedule_config: Dict[str, Any]
    recipients: List[str]
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateReportRequest(BaseModel):
    """生成报告请求"""
    template_id: int
    name: Optional[str] = None
    format: Optional[str] = "pdf"
    filters: Optional[Dict[str, Any]] = {}


class GeneratedReportResponse(BaseModel):
    """已生成报告响应"""
    id: int
    name: str
    report_type: str
    format: str
    file_path: Optional[str]
    file_size: Optional[int]
    status: str
    generated_by: str
    generation_time_seconds: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Report Templates CRUD
# ============================================================================

@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建报告模板
    """
    # Check if name already exists
    existing = db.query(ReportTemplate).filter(
        ReportTemplate.name == template_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template with name '{template_data.name}' already exists"
        )
    
    try:
        new_template = ReportTemplate(
            name=template_data.name,
            description=template_data.description,
            report_type=template_data.report_type,
            format=template_data.format,
            template_config=template_data.template_config.dict(),
            created_by=current_user.get("username", "unknown"),
            is_system=False,
            is_active=True
        )
        
        db.add(new_template)
        db.commit()
        db.refresh(new_template)
        
        logger.info(f"Created report template: {new_template.name} (ID: {new_template.id})")
        return new_template
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    report_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有报告模板
    """
    query = db.query(ReportTemplate).filter(ReportTemplate.is_active == True)
    
    if report_type:
        query = query.filter(ReportTemplate.report_type == report_type)
    
    templates = query.order_by(desc(ReportTemplate.created_at)).offset(skip).limit(limit).all()
    
    return templates


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定报告模板
    """
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除报告模板（软删除）
    """
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    
    if template.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system templates"
        )
    
    template.is_active = False
    
    try:
        db.commit()
        logger.info(f"Deleted template {template_id}")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )


# ============================================================================
# Report Generation
# ============================================================================

@router.post("/generate", response_model=GeneratedReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    立即生成报告
    
    支持的格式：PDF, HTML, JSON, Excel
    """
    # Get template
    template = db.query(ReportTemplate).filter(
        ReportTemplate.id == request.template_id,
        ReportTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {request.template_id} not found"
        )
    
    # Generate report name
    report_name = request.name or f"{template.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    start_time = datetime.now()
    
    try:
        # Collect report data
        report_data = await _collect_report_data(db, template, request.filters)
        
        # Generate report file
        format_type = request.format or template.format
        file_path = None
        file_size = None
        
        if format_type == "json":
            # For JSON, store data directly
            pass
        elif format_type == "pdf":
            file_path, file_size = await _generate_pdf_report(report_name, template, report_data)
        elif format_type == "html":
            file_path, file_size = await _generate_html_report(report_name, template, report_data)
        elif format_type == "excel":
            file_path, file_size = await _generate_excel_report(report_name, template, report_data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        end_time = datetime.now()
        generation_time = int((end_time - start_time).total_seconds())
        
        # Save report record
        new_report = GeneratedReport(
            name=report_name,
            template_id=template.id,
            report_type=template.report_type,
            format=format_type,
            file_path=file_path,
            file_size=file_size,
            report_data=report_data if format_type == "json" else None,
            generated_by=current_user.get("username", "unknown"),
            generation_time_seconds=generation_time,
            status="completed",
            expires_at=datetime.now() + timedelta(days=30)  # Expire after 30 days
        )
        
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        logger.info(f"Generated report: {report_name} (ID: {new_report.id})")
        
        return new_report
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        
        # Save failed report record
        failed_report = GeneratedReport(
            name=report_name,
            template_id=template.id,
            report_type=template.report_type,
            format=request.format or template.format,
            generated_by=current_user.get("username", "unknown"),
            status="failed",
            error_message=str(e)
        )
        
        db.add(failed_report)
        db.commit()
        db.refresh(failed_report)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/reports", response_model=List[GeneratedReportResponse])
async def list_generated_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取已生成的报告列表
    """
    query = db.query(GeneratedReport)
    
    if status_filter:
        query = query.filter(GeneratedReport.status == status_filter)
    
    reports = query.order_by(desc(GeneratedReport.created_at)).offset(skip).limit(limit).all()
    
    return reports


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    下载生成的报告文件
    """
    report = db.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )
    
    if report.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is not completed (status: {report.status})"
        )
    
    # For JSON reports, return data directly
    if report.format == "json" and report.report_data:
        return report.report_data
    
    # For file-based reports
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )
    
    # Determine media type
    media_types = {
        "pdf": "application/pdf",
        "html": "text/html",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    
    media_type = media_types.get(report.format, "application/octet-stream")
    
    return FileResponse(
        path=report.file_path,
        media_type=media_type,
        filename=f"{report.name}.{report.format}"
    )


# ============================================================================
# Scheduled Reports
# ============================================================================

@router.post("/scheduled", response_model=ScheduledReportResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_report(
    schedule_data: ScheduledReportCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建计划报告
    
    定期自动生成并通过邮件发送报告
    """
    # Validate template exists
    template = db.query(ReportTemplate).filter(
        ReportTemplate.id == schedule_data.template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {schedule_data.template_id} not found"
        )
    
    try:
        # Calculate next run time
        next_run = _calculate_next_run_time(schedule_data.frequency, schedule_data.schedule_config)
        
        new_schedule = ScheduledReport(
            name=schedule_data.name,
            description=schedule_data.description,
            template_id=schedule_data.template_id,
            frequency=schedule_data.frequency,
            schedule_config=schedule_data.schedule_config,
            recipients=schedule_data.recipients,
            email_subject=schedule_data.email_subject or f"Automated Report: {schedule_data.name}",
            email_body=schedule_data.email_body,
            report_filters=schedule_data.report_filters,
            is_active=True,
            next_run_at=next_run,
            created_by=current_user.get("username", "unknown")
        )
        
        db.add(new_schedule)
        db.commit()
        db.refresh(new_schedule)
        
        logger.info(f"Created scheduled report: {new_schedule.name} (ID: {new_schedule.id})")
        
        return new_schedule
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating scheduled report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scheduled report: {str(e)}"
        )


@router.get("/scheduled", response_model=List[ScheduledReportResponse])
async def list_scheduled_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = Query(True),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有计划报告
    """
    query = db.query(ScheduledReport)
    
    if active_only:
        query = query.filter(ScheduledReport.is_active == True)
    
    schedules = query.order_by(desc(ScheduledReport.created_at)).offset(skip).limit(limit).all()
    
    return schedules


# ============================================================================
# Helper Functions
# ============================================================================

async def _collect_report_data(db: Session, template: ReportTemplate, filters: Dict[str, Any]) -> Dict[str, Any]:
    """收集报告数据"""
    data = {
        "generated_at": datetime.now().isoformat(),
        "template_name": template.name,
        "filters": filters
    }
    
    # Collect basic statistics
    total_patients = db.query(func.count(Patient.id)).scalar() or 0
    total_conditions = db.query(func.count(Condition.id)).scalar() or 0
    total_encounters = db.query(func.count(Encounter.id)).scalar() or 0
    total_observations = db.query(func.count(Observation.id)).scalar() or 0
    
    data["summary"] = {
        "total_patients": total_patients,
        "total_conditions": total_conditions,
        "total_encounters": total_encounters,
        "total_observations": total_observations
    }
    
    # Gender distribution
    gender_dist = db.query(
        Patient.gender,
        func.count(Patient.id).label('count')
    ).group_by(Patient.gender).all()
    
    data["gender_distribution"] = {row.gender or "unknown": row.count for row in gender_dist}
    
    # Top conditions
    top_conditions = db.query(
        Condition.code_text,
        func.count(Condition.id).label('count')
    ).filter(
        Condition.code_text.isnot(None)
    ).group_by(Condition.code_text).order_by(
        func.count(Condition.id).desc()
    ).limit(10).all()
    
    data["top_conditions"] = [
        {"condition": row.code_text, "count": row.count}
        for row in top_conditions
    ]
    
    return data


async def _generate_pdf_report(name: str, template: ReportTemplate, data: Dict[str, Any]) -> tuple:
    """生成PDF报告"""
    # TODO: Implement PDF generation using ReportLab or WeasyPrint
    # For now, return a placeholder
    file_path = f"/tmp/reports/{name}.pdf"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Placeholder: Save JSON data to file
    with open(file_path, 'w') as f:
        f.write(f"PDF Report: {name}\n")
        f.write(json.dumps(data, indent=2))
    
    file_size = os.path.getsize(file_path)
    return file_path, file_size


async def _generate_html_report(name: str, template: ReportTemplate, data: Dict[str, Any]) -> tuple:
    """生成HTML报告"""
    file_path = f"/tmp/reports/{name}.html"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; }}
            .stat-card {{ background: #f8f9fa; padding: 20px; margin: 10px 0; border-radius: 8px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #667eea; color: white; }}
        </style>
    </head>
    <body>
        <h1>{template.name}</h1>
        <p>Generated at: {data.get('generated_at')}</p>
        
        <h2>Summary Statistics</h2>
        <div class="stat-card">
            <p>Total Patients: {data['summary']['total_patients']}</p>
            <p>Total Conditions: {data['summary']['total_conditions']}</p>
            <p>Total Encounters: {data['summary']['total_encounters']}</p>
        </div>
        
        <h2>Top Conditions</h2>
        <table>
            <tr><th>Condition</th><th>Count</th></tr>
            {''.join(f'<tr><td>{c["condition"]}</td><td>{c["count"]}</td></tr>' for c in data.get('top_conditions', []))}
        </table>
    </body>
    </html>
    """
    
    with open(file_path, 'w') as f:
        f.write(html_content)
    
    file_size = os.path.getsize(file_path)
    return file_path, file_size


async def _generate_excel_report(name: str, template: ReportTemplate, data: Dict[str, Any]) -> tuple:
    """生成Excel报告"""
    # TODO: Implement Excel generation using openpyxl or xlsxwriter
    file_path = f"/tmp/reports/{name}.xlsx"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Placeholder
    with open(file_path, 'w') as f:
        f.write(json.dumps(data, indent=2))
    
    file_size = os.path.getsize(file_path)
    return file_path, file_size


def _calculate_next_run_time(frequency: str, config: Dict[str, Any]) -> datetime:
    """计算下次执行时间"""
    now = datetime.now()
    
    if frequency == "daily":
        return now + timedelta(days=1)
    elif frequency == "weekly":
        return now + timedelta(weeks=1)
    elif frequency == "monthly":
        return now + timedelta(days=30)
    elif frequency == "quarterly":
        return now + timedelta(days=90)
    elif frequency == "yearly":
        return now + timedelta(days=365)
    else:
        return now + timedelta(days=1)

