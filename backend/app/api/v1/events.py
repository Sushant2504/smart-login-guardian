"""
Events API endpoints for login event management
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.event import (
    EventCreate, EventResponse, EventUpdate,
    EventListResponse, EventStatsResponse, EventFilter
)
from app.services.event_service import EventService
from app.api.deps import (
    get_current_user, get_current_analyst_user,
    require_permission, RateLimiter
)
from app.models import User
from app.core import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(calls=100, period=60))]
)
async def create_event(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(require_permission("events:write"))
):
    """
    Create a new login event (for API integrations)

    Rate limited to 100 events per minute per user/IP
    """
    event_service = EventService(db)

    try:
        event = await event_service.create_event(event_data)
        logger.info(
            "Event created",
            event_id=str(event.id),
            user_identifier=event.user_identifier,
            risk_score=event.risk_score
        )
        return event

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=EventListResponse)
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    user_identifier: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:read"))
):
    """
    List login events with filtering and pagination

    Filters:
    - status: success, failed
    - risk_level: low, medium, high, critical
    - user_identifier: exact match
    - start_date/end_date: ISO format datetime
    """
    event_service = EventService(db)

    filters = EventFilter(
        status=status,
        risk_level=risk_level,
        user_identifier=user_identifier,
        start_date=start_date,
        end_date=end_date
    )

    events, total = await event_service.list_events(
        skip=skip,
        limit=limit,
        filters=filters
    )

    return EventListResponse(
        events=events,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/stats", response_model=EventStatsResponse)
async def get_event_statistics(
    hours: int = Query(24, ge=1, le=168),  # Last 1-168 hours (7 days)
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:read"))
):
    """
    Get event statistics for the specified time period

    Returns:
    - Total events
    - Events by status
    - Events by risk level
    - Events by country
    - Trending patterns
    """
    event_service = EventService(db)

    stats = await event_service.get_statistics(hours=hours)

    return stats


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:read"))
):
    """
    Get a specific event by ID
    """
    event_service = EventService(db)

    event = await event_service.get_event(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    return event


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:write"))
):
    """
    Update an event (for corrections or additional analysis)
    """
    event_service = EventService(db)

    event = await event_service.update_event(event_id, event_data)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    logger.info("Event updated", event_id=str(event_id))

    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:write"))
):
    """
    Delete an event (admin only, for data retention compliance)
    """
    event_service = EventService(db)

    deleted = await event_service.delete_event(event_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    logger.info("Event deleted", event_id=str(event_id))


@router.post("/analyze", response_model=EventResponse)
async def analyze_login_attempt(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(require_permission("events:write"))
):
    """
    Analyze a login attempt and get risk assessment

    This endpoint processes the login event through the ML model
    and risk scoring engine, then returns the complete analysis
    """
    event_service = EventService(db)

    event = await event_service.analyze_and_create_event(event_data)

    logger.info(
        "Login analyzed",
        event_id=str(event.id),
        risk_score=event.risk_score,
        ml_anomaly=event.ml_anomaly
    )

    return event


@router.get("/user/{user_identifier}", response_model=List[EventResponse])
async def get_user_events(
    user_identifier: str,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:read"))
):
    """
    Get all events for a specific user
    """
    event_service = EventService(db)

    events = await event_service.get_events_by_user(
        user_identifier=user_identifier,
        limit=limit
    )

    return events


@router.get("/ip/{ip_address}", response_model=List[EventResponse])
async def get_ip_events(
    ip_address: str,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:read"))
):
    """
    Get all events from a specific IP address
    """
    event_service = EventService(db)

    events = await event_service.get_events_by_ip(
        ip_address=ip_address,
        limit=limit
    )

    return events


@router.post("/{event_id}/reanalyze", response_model=EventResponse)
async def reanalyze_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_analyst_user)
):
    """
    Re-run analysis on an existing event

    Useful when ML model has been updated or new context is available
    """
    event_service = EventService(db)

    event = await event_service.reanalyze_event(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    logger.info("Event reanalyzed", event_id=str(event_id))

    return event


@router.post("/bulk", response_model=List[EventResponse])
async def bulk_create_events(
    events_data: List[EventCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:write")),
    dependencies=[Depends(RateLimiter(calls=10, period=60))]
):
    """
    Bulk create events (for batch imports)

    Limited to 10 bulk operations per minute
    Maximum 1000 events per request
    """
    if len(events_data) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 1000 events per bulk request"
        )

    event_service = EventService(db)

    events = await event_service.bulk_create_events(events_data)

    logger.info("Bulk events created", count=len(events))

    return events
