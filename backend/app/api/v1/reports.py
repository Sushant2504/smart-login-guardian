"""
Reporting API endpoints for analytics and exports
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.report import (
    ReportRequest, ReportResponse, DashboardMetrics,
    ThreatTrendsResponse, ComplianceReportResponse
)
from app.services.report_service import ReportService
from app.api.deps import get_current_user, require_permission
from app.models import User
from app.core import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:read"))
):
    """
    Get dashboard metrics for the specified time period

    Returns comprehensive metrics for dashboard visualization
    """
    report_service = ReportService(db)

    metrics = await report_service.get_dashboard_metrics(hours=hours)

    return metrics


@router.get("/threats/trends", response_model=ThreatTrendsResponse)
async def get_threat_trends(
    days: int = Query(7, ge=1, le=90),
    granularity: str = Query("day", regex="^(hour|day|week)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:read"))
):
    """
    Get threat trends over time

    Parameters:
    - days: Number of days to analyze
    - granularity: Data grouping (hour, day, week)
    """
    report_service = ReportService(db)

    trends = await report_service.get_threat_trends(
        days=days,
        granularity=granularity
    )

    return trends


@router.get("/geo/distribution")
async def get_geo_distribution(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:read"))
):
    """
    Get geographic distribution of login events
    """
    report_service = ReportService(db)

    distribution = await report_service.get_geo_distribution(days=days)

    return distribution


@router.get("/top-threats")
async def get_top_threats(
    limit: int = Query(10, ge=1, le=100),
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:read"))
):
    """
    Get top threat actors (IPs/users with most high-risk events)
    """
    report_service = ReportService(db)

    threats = await report_service.get_top_threats(limit=limit, days=days)

    return threats


@router.get("/compliance", response_model=ComplianceReportResponse)
async def get_compliance_report(
    start_date: str,
    end_date: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:read"))
):
    """
    Generate compliance report for audit purposes

    Includes:
    - Total events processed
    - Threats detected and resolved
    - Response times
    - System uptime metrics
    """
    report_service = ReportService(db)

    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use ISO format (YYYY-MM-DD)"
        )

    report = await report_service.get_compliance_report(
        start_date=start,
        end_date=end
    )

    return report


@router.post("/export")
async def export_report(
    report_request: ReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:read"))
):
    """
    Export report in specified format (CSV, JSON, PDF)

    Returns download link or file content
    """
    report_service = ReportService(db)

    try:
        export_data = await report_service.export_report(report_request)

        # Set appropriate content type based on format
        content_types = {
            "csv": "text/csv",
            "json": "application/json",
            "pdf": "application/pdf"
        }

        return Response(
            content=export_data,
            media_type=content_types.get(report_request.format, "application/octet-stream"),
            headers={
                "Content-Disposition": f"attachment; filename=report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{report_request.format}"
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/user-activity/{user_identifier}")
async def get_user_activity_report(
    user_identifier: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:read"))
):
    """
    Get detailed activity report for a specific user
    """
    report_service = ReportService(db)

    activity = await report_service.get_user_activity_report(
        user_identifier=user_identifier,
        days=days
    )

    return activity


@router.get("/summary")
async def get_executive_summary(
    period: str = Query("month", regex="^(week|month|quarter|year)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:read"))
):
    """
    Get executive summary for leadership

    High-level metrics and trends
    """
    report_service = ReportService(db)

    summary = await report_service.get_executive_summary(period=period)

    return summary


@router.get("/alerts/response-times")
async def get_alert_response_metrics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:read"))
):
    """
    Get alert response time metrics

    Useful for SLA tracking
    """
    report_service = ReportService(db)

    metrics = await report_service.get_alert_response_metrics(days=days)

    return metrics
