"""
ML schemas for machine learning operations
"""
from typing import Optional, List
from pydantic import Field
from app.schemas.common import BaseSchema


class MLModelInfo(BaseSchema):
    """ML model information"""
    model_id: str
    version: str
    created_at: str
    is_active: bool
    accuracy: float


class MLModelMetrics(BaseSchema):
    """ML model metrics"""
    model_id: str
    accuracy: float
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0


class MLTrainingRequest(BaseSchema):
    """ML training request"""
    days_back: int = Field(default=30, ge=1, le=365)
    contamination: float = Field(default=0.1, ge=0.01, le=0.5)


class MLPredictionRequest(BaseSchema):
    """ML prediction request"""
    features: dict


class MLPredictionResponse(BaseSchema):
    """ML prediction response"""
    is_anomaly: bool
    anomaly_score: float
    confidence: float


class MLFeatureImportance(BaseSchema):
    """Feature importance"""
    feature_name: str
    importance_score: float
