"""
Alerts API endpoints for security alert management
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.alert import (
    AlertResponse, AlertListResponse, AlertUpdate, AlertFilter
)
from app.services.alert_service import AlertService
from app.api.deps import get_current_user, require_permission
from app.models import User
from app.core import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("alerts:read"))
):
    """
    List security alerts with filtering

    Filters:
    - severity: low, medium, high, critical
    - status: open, acknowledged, resolved, false_positive
    - assigned_to: user UUID
    """
    alert_service = AlertService(db)

    filters = AlertFilter(
        severity=severity,
        status=status,
        assigned_to=assigned_to
    )

    alerts, total = await alert_service.list_alerts(
        skip=skip,
        limit=limit,
        filters=filters
    )

    return AlertListResponse(
        alerts=alerts,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("alerts:read"))
):
    """
    Get specific alert by ID
    """
    alert_service = AlertService(db)

    alert = await alert_service.get_alert(alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    alert_data: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("alerts:manage"))
):
    """
    Update alert status, assignment, or add notes
    """
    alert_service = AlertService(db)

    alert = await alert_service.update_alert(alert_id, alert_data, current_user.id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    logger.info(
        "Alert updated",
        alert_id=str(alert_id),
        status=alert_data.status
    )

    return alert


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("alerts:manage"))
):
    """
    Acknowledge an alert
    """
    alert_service = AlertService(db)

    alert = await alert_service.acknowledge_alert(alert_id, current_user.id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    logger.info("Alert acknowledged", alert_id=str(alert_id))

    return alert


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: UUID,
    resolution_note: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("alerts:manage"))
):
    """
    Mark alert as resolved
    """
    alert_service = AlertService(db)

    alert = await alert_service.resolve_alert(
        alert_id,
        current_user.id,
        resolution_note
    )

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    logger.info("Alert resolved", alert_id=str(alert_id))

    return alert


@router.post("/{alert_id}/assign/{user_id}", response_model=AlertResponse)
async def assign_alert(
    alert_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("alerts:manage"))
):
    """
    Assign alert to a user
    """
    alert_service = AlertService(db)

    alert = await alert_service.assign_alert(alert_id, user_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    logger.info("Alert assigned", alert_id=str(alert_id), assigned_to=str(user_id))

    return alert


@router.get("/stats/summary")
async def get_alert_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("alerts:read"))
):
    """
    Get alert statistics summary
    """
    alert_service = AlertService(db)

    summary = await alert_service.get_alert_summary()

    return summary
