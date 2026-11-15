"""
Alert repository
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertStatus, AlertSeverity
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    """Alert repository"""

    def __init__(self, db: AsyncSession):
        super().__init__(Alert, db)

    async def get_by_status(self, status: AlertStatus, skip: int = 0, limit: int = 100) -> List[Alert]:
        """Get alerts by status"""
        result = await self.db.execute(
            select(Alert)
            .where(Alert.status == status)
            .order_by(desc(Alert.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_severity(self, severity: AlertSeverity, skip: int = 0, limit: int = 100) -> List[Alert]:
        """Get alerts by severity"""
        result = await self.db.execute(
            select(Alert)
            .where(Alert.severity == severity)
            .order_by(desc(Alert.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_assigned_to_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Alert]:
        """Get alerts assigned to a user"""
        result = await self.db.execute(
            select(Alert)
            .where(Alert.assigned_to == user_id)
            .order_by(desc(Alert.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_open_alerts(self) -> int:
        """Count open alerts"""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count()).select_from(Alert).where(Alert.status == AlertStatus.OPEN)
        )
        return result.scalar_one()
