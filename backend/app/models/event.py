"""
Event model
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class EventStatus(str, enum.Enum):
    """Event status"""
    SUCCESS = "success"
    FAILED = "failed"


class RiskLevel(str, enum.Enum):
    """Risk level"""
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class Event(BaseModel):
    """Authentication event model"""

    __tablename__ = "events"

    # User information
    user_identifier = Column(String(255), nullable=False, index=True)

    # Location information
    ip_address = Column(String(45), nullable=False, index=True)  # IPv6 support
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Device information
    device = Column(String(255), nullable=True)
    browser = Column(String(255), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Event status
    status = Column(SQLEnum(EventStatus), nullable=False, index=True)

    # Risk analysis
    risk_score = Column(Integer, default=0, nullable=False, index=True)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, index=True)
    signals = Column(Text, nullable=True)  # JSON array of risk signals

    # ML analysis
    ml_anomaly = Column(Boolean, default=False, nullable=False, index=True)
    ml_score = Column(Float, default=0.0, nullable=False)
    ml_features = Column(Text, nullable=True)  # JSON array of feature values

    # Relationships
    alert = relationship("Alert", back_populates="event", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Event {self.id} - {self.user_identifier} - {self.risk_level}>"
