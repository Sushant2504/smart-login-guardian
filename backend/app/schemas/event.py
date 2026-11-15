"""
Event schemas
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import Field, IPvAnyAddress

from app.schemas.common import BaseSchema
from app.models.event import EventStatus, RiskLevel


class EventBase(BaseSchema):
    """Base event schema"""
    user_identifier: str = Field(..., min_length=1, max_length=255)
    ip_address: str = Field(..., min_length=7, max_length=45)
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    device: Optional[str] = Field(None, max_length=255)
    browser: Optional[str] = Field(None, max_length=255)
    user_agent: Optional[str] = None
    status: EventStatus


class EventCreate(EventBase):
    """Schema for creating an event"""
    pass


class EventInDB(EventBase):
    """Event schema with database fields"""
    id: UUID
    risk_score: int
    risk_level: RiskLevel
    signals: Optional[str] = None
    ml_anomaly: bool
    ml_score: float
    ml_features: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Event(EventInDB):
    """Public event schema"""
    pass


class EventWithAlert(Event):
    """Event with related alert"""
    alert: Optional["AlertInDB"] = None


# Import here to avoid circular dependency
from app.schemas.alert import AlertInDB

EventWithAlert.model_rebuild()
