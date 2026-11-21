"""
Machine Learning API endpoints for model management and training
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.ml import (
    MLModelInfo, MLModelMetrics, MLTrainingRequest,
    MLPredictionRequest, MLPredictionResponse, MLFeatureImportance
)
from app.services.ml_service import MLService
from app.api.deps import get_current_user, get_current_analyst_user, require_permission
from app.models import User
from app.core import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/models", response_model=List[MLModelInfo])
async def list_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:read"))
):
    """
    List all available ML models
    """
    ml_service = MLService(db)

    models = await ml_service.list_models()

    return models


@router.get("/models/active", response_model=MLModelInfo)
async def get_active_model(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:read"))
):
    """
    Get currently active ML model info
    """
    ml_service = MLService(db)

    model_info = await ml_service.get_active_model_info()

    return model_info


@router.get("/models/{model_id}/metrics", response_model=MLModelMetrics)
async def get_model_metrics(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:read"))
):
    """
    Get performance metrics for a specific model
    """
    ml_service = MLService(db)

    metrics = await ml_service.get_model_metrics(model_id)

    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    return metrics


@router.post("/train", status_code=status.HTTP_202_ACCEPTED)
async def train_model(
    training_request: MLTrainingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_analyst_user)
):
    """
    Trigger ML model training (async background task)

    Training runs in background and can take several minutes
    """
    ml_service = MLService(db)

    task_id = await ml_service.start_training(
        days_back=training_request.days_back,
        contamination=training_request.contamination,
        user_id=current_user.id
    )

    logger.info("ML training started", task_id=task_id, user_id=str(current_user.id))

    return {
        "task_id": task_id,
        "status": "training_started",
        "message": "Model training initiated. Check /ml/training/{task_id} for progress"
    }


@router.get("/training/{task_id}")
async def get_training_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:read"))
):
    """
    Get status of a training task
    """
    ml_service = MLService(db)

    status_info = await ml_service.get_training_status(task_id)

    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training task not found"
        )

    return status_info


@router.post("/predict", response_model=MLPredictionResponse)
async def predict_anomaly(
    prediction_request: MLPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:write"))
):
    """
    Get anomaly prediction for a login event
    """
    ml_service = MLService(db)

    try:
        prediction = await ml_service.predict(prediction_request)
        return prediction

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/features/importance", response_model=List[MLFeatureImportance])
async def get_feature_importance(
    model_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:read"))
):
    """
    Get feature importance scores from the ML model
    """
    ml_service = MLService(db)

    importance = await ml_service.get_feature_importance(model_id)

    return importance


@router.post("/models/{model_id}/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_analyst_user)
):
    """
    Activate a specific model version
    """
    ml_service = MLService(db)

    activated = await ml_service.activate_model(model_id)

    if not activated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    logger.info("Model activated", model_id=model_id, user_id=str(current_user.id))


@router.get("/drift/check")
async def check_model_drift(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("events:read"))
):
    """
    Check for model drift over specified period
    """
    ml_service = MLService(db)

    drift_analysis = await ml_service.check_model_drift(days=days)

    return drift_analysis


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_analyst_user)
):
    """
    Delete a model (cannot delete active model)
    """
    ml_service = MLService(db)

    deleted = await ml_service.delete_model(model_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete active model or model not found"
        )

    logger.info("Model deleted", model_id=model_id, user_id=str(current_user.id))
