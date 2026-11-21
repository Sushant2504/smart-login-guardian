"""
Audit logging for compliance and security tracking
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_logger
from app.models.audit import AuditLog

logger = get_logger(__name__)


class AuditLogger:
    """
    Audit logger for tracking security-relevant events
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        user_id: Optional[str],
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True
    ):
        """
        Log an audit event

        Args:
            action: Action performed (e.g., "user.login", "alert.resolve")
            user_id: ID of user performing action
            resource_type: Type of resource affected (e.g., "user", "event")
            resource_id: ID of resource affected
            details: Additional details as JSON
            ip_address: IP address of request
            user_agent: User agent string
            success: Whether action succeeded
        """
        try:
            audit_entry = AuditLog(
                action=action,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                timestamp=datetime.utcnow()
            )

            self.db.add(audit_entry)
            await self.db.commit()

            logger.info(
                "Audit log created",
                action=action,
                user_id=user_id,
                success=success
            )

        except Exception as e:
            logger.error("Failed to create audit log", error=str(e))
            # Don't fail the main operation if audit logging fails
            await self.db.rollback()


async def log_auth_event(
    db: AsyncSession,
    action: str,
    user_id: Optional[str],
    success: bool,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log authentication-related events
    """
    auditor = AuditLogger(db)
    await auditor.log(
        action=f"auth.{action}",
        user_id=user_id,
        resource_type="authentication",
        success=success,
        ip_address=ip_address,
        details=details
    )


async def log_data_access(
    db: AsyncSession,
    user_id: str,
    resource_type: str,
    resource_id: str,
    action: str,
    ip_address: Optional[str] = None
):
    """
    Log data access for compliance
    """
    auditor = AuditLogger(db)
    await auditor.log(
        action=f"data.{action}",
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address
    )


async def log_admin_action(
    db: AsyncSession,
    user_id: str,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
):
    """
    Log administrative actions
    """
    auditor = AuditLogger(db)
    await auditor.log(
        action=f"admin.{action}",
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address
    )
