"""
Admin API endpoints for system management
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.admin import (
    SystemHealth, SystemConfig, AuditLogResponse,
    MaintenanceMode, DataRetentionPolicy
)
from app.services.admin_service import AdminService
from app.api.deps import get_current_admin_user
from app.models import User
from app.core import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=SystemHealth)
async def get_system_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get comprehensive system health status

    Includes:
    - Database connectivity
    - Redis connectivity
    - ML model status
    - System resources
    - Service status
    """
    admin_service = AdminService(db)

    health = await admin_service.get_system_health()

    return health


@router.get("/config", response_model=SystemConfig)
async def get_system_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get current system configuration
    """
    admin_service = AdminService(db)

    config = await admin_service.get_system_config()

    return config


@router.patch("/config", response_model=SystemConfig)
async def update_system_config(
    config_update: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update system configuration

    Changes require service restart for some settings
    """
    admin_service = AdminService(db)

    config = await admin_service.update_system_config(config_update)

    logger.info("System config updated", user_id=str(current_user.id))

    return config


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get audit logs for compliance and security

    Tracks all administrative actions
    """
    admin_service = AdminService(db)

    logs = await admin_service.get_audit_logs(
        skip=skip,
        limit=limit,
        action=action,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )

    return logs


@router.post("/maintenance", status_code=status.HTTP_204_NO_CONTENT)
async def set_maintenance_mode(
    maintenance: MaintenanceMode,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Enable/disable maintenance mode
    """
    admin_service = AdminService(db)

    await admin_service.set_maintenance_mode(
        enabled=maintenance.enabled,
        message=maintenance.message
    )

    logger.info(
        "Maintenance mode updated",
        enabled=maintenance.enabled,
        user_id=str(current_user.id)
    )


@router.post("/database/backup", status_code=status.HTTP_202_ACCEPTED)
async def trigger_database_backup(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Trigger manual database backup
    """
    admin_service = AdminService(db)

    task_id = await admin_service.trigger_backup()

    logger.info("Database backup triggered", task_id=task_id, user_id=str(current_user.id))

    return {
        "task_id": task_id,
        "status": "backup_initiated",
        "message": "Database backup started"
    }


@router.post("/database/cleanup", status_code=status.HTTP_202_ACCEPTED)
async def cleanup_old_data(
    days: int = Query(90, ge=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Clean up old data based on retention policy

    Removes events and logs older than specified days
    """
    admin_service = AdminService(db)

    task_id = await admin_service.cleanup_old_data(days=days)

    logger.info("Data cleanup triggered", days=days, user_id=str(current_user.id))

    return {
        "task_id": task_id,
        "status": "cleanup_initiated",
        "message": f"Cleaning up data older than {days} days"
    }


@router.get("/retention-policy", response_model=DataRetentionPolicy)
async def get_retention_policy(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get current data retention policy
    """
    admin_service = AdminService(db)

    policy = await admin_service.get_retention_policy()

    return policy


@router.put("/retention-policy", response_model=DataRetentionPolicy)
async def update_retention_policy(
    policy: DataRetentionPolicy,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update data retention policy
    """
    admin_service = AdminService(db)

    updated_policy = await admin_service.update_retention_policy(policy)

    logger.info("Retention policy updated", user_id=str(current_user.id))

    return updated_policy


@router.get("/metrics/prometheus")
async def get_prometheus_metrics(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get Prometheus metrics endpoint
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.post("/cache/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cache(
    pattern: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Clear Redis cache

    Optionally specify pattern to clear specific keys
    """
    admin_service = AdminService(db)

    await admin_service.clear_cache(pattern=pattern)

    logger.info("Cache cleared", pattern=pattern or "all", user_id=str(current_user.id))


@router.get("/stats/system")
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get comprehensive system statistics
    """
    admin_service = AdminService(db)

    stats = await admin_service.get_system_stats()

    return stats
