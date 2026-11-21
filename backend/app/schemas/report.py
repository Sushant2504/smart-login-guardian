"""
Report schemas for analytics and reporting
"""
from typing import Optional, List
from pydantic import Field
from app.schemas.common import BaseSchema


class DashboardMetrics(BaseSchema):
    """Dashboard metrics"""
    total_events: int
    total_alerts: int
    high_risk_events: int
    active_threats: int


class ThreatTrendsResponse(BaseSchema):
    """Threat trends response"""
    trends: List[dict]


class ComplianceReportResponse(BaseSchema):
    """Compliance report response"""
    period_start: str
    period_end: str
    total_events: int
    threats_detected: int


class ReportRequest(BaseSchema):
    """Report export request"""
    report_type: str
    format: str = Field(default="json", regex="^(json|csv|pdf)$")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
