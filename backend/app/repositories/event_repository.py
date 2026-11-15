"""
Event repository
"""
from typing import List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.models.event import Event, RiskLevel, EventStatus
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    """Event repository"""

    def __init__(self, db: AsyncSession):
        super().__init__(Event, db)

    async def get_by_user(self, user_identifier: str, limit: int = 100) -> List[Event]:
        """Get events for a specific user"""
        result = await self.db.execute(
            select(Event)
            .where(Event.user_identifier == user_identifier)
            .order_by(desc(Event.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_risk_level(self, risk_level: RiskLevel, skip: int = 0, limit: int = 100) -> List[Event]:
        """Get events by risk level"""
        result = await self.db.execute(
            select(Event)
            .where(Event.risk_level == risk_level)
            .order_by(desc(Event.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(self, limit: int = 20) -> List[Event]:
        """Get most recent events"""
        result = await self.db.execute(
            select(Event)
            .order_by(desc(Event.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_ip(self, ip_address: str, limit: int = 100) -> List[Event]:
        """Get events from specific IP"""
        result = await self.db.execute(
            select(Event)
            .where(Event.ip_address == ip_address)
            .order_by(desc(Event.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self, status: EventStatus) -> int:
        """Count events by status"""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count()).select_from(Event).where(Event.status == status)
        )
        return result.scalar_one()

    async def count_by_risk_level(self, risk_level: RiskLevel) -> int:
        """Count events by risk level"""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count()).select_from(Event).where(Event.risk_level == risk_level)
        )
        return result.scalar_one()
