"""
Alert schemas
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import Field

from app.schemas.common import BaseSchema
from app.models.alert import AlertSeverity, AlertStatus


class AlertBase(BaseSchema):
    """Base alert schema"""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.OPEN


class AlertCreate(AlertBase):
    """Schema for creating an alert"""
    event_id: UUID


class AlertUpdate(BaseSchema):
    """Schema for updating an alert"""
    status: Optional[AlertStatus] = None
    assigned_to: Optional[UUID] = None
    resolution_notes: Optional[str] = None


class AlertInDB(AlertBase):
    """Alert schema with database fields"""
    id: UUID
    event_id: UUID
    assigned_to: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Alert(AlertInDB):
    """Public alert schema"""
    pass


class AlertResponse(Alert):
    """Alert API response"""
    pass


class AlertFilter(BaseSchema):
    """Alert filter parameters"""
    severity: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None


class AlertListResponse(BaseSchema):
    """Alert list response"""
    alerts: List[Alert]
    total: int
    skip: int
    limit: int
