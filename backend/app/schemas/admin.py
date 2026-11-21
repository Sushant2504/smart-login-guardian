"""
Admin schemas for system administration
"""
from typing import Optional, Dict, Any
from pydantic import Field
from app.schemas.common import BaseSchema


class SystemHealth(BaseSchema):
    """System health status"""
    status: str
    database: str
    redis: str
    version: str


class SystemConfig(BaseSchema):
    """System configuration"""
    settings: Dict[str, Any]


class AuditLogResponse(BaseSchema):
    """Audit log entry"""
    id: str
    action: str
    user_id: Optional[str]
    timestamp: str
    details: Optional[Dict[str, Any]] = None


class MaintenanceMode(BaseSchema):
    """Maintenance mode setting"""
    enabled: bool
    message: Optional[str] = None


class DataRetentionPolicy(BaseSchema):
    """Data retention policy"""
    events_days: int = Field(default=90, ge=30)
    logs_days: int = Field(default=365, ge=90)
