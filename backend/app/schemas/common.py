"""
Common Pydantic schemas
"""
from typing import Optional
from pydantic import BaseModel as PydanticBase
from datetime import datetime
from uuid import UUID


class BaseSchema(PydanticBase):
    """Base schema with common configuration"""

    class Config:
        from_attributes = True


class PaginationParams(BaseSchema):
    """Pagination parameters"""
    skip: int = 0
    limit: int = 100


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper"""
    total: int
    skip: int
    limit: int
    items: list


class HealthCheck(BaseSchema):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
