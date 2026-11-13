from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class RiskLevel(Enum):
    """Risk level classification"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalType(Enum):
    """Types of risk signals"""
    BRUTE_FORCE = "brute_force"
    GEO_ANOMALY = "geo_anomaly"
    TIME_ANOMALY = "time_anomaly"
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    NEW_DEVICE = "new_device"
    SUSPICIOUS_IP = "suspicious_ip"
    ACCOUNT_ENUMERATION = "account_enumeration"
    CREDENTIAL_STUFFING = "credential_stuffing"
    SESSION_HIJACKING = "session_hijacking"


@dataclass
class LoginAttempt:
    """Represents a single login attempt"""
    username: str
    ip_address: str
    timestamp: datetime
    success: bool
    user_agent: Optional[str] = None
    location: Optional[dict] = None  # {'country': 'US', 'city': 'New York', 'lat': 40.7, 'lon': -74.0}
    device_fingerprint: Optional[str] = None
    session_id: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))


@dataclass
class RiskSignal:
    """Represents a detected risk signal"""
    signal_type: SignalType
    severity: int  # 0-100
    description: str
    details: dict = field(default_factory=dict)

    @property
    def severity_label(self) -> str:
        if self.severity >= 80:
            return "Critical"
        elif self.severity >= 60:
            return "High"
        elif self.severity >= 40:
            return "Medium"
        elif self.severity >= 20:
            return "Low"
        return "Informational"


@dataclass
class RiskAssessment:
    """Complete risk assessment for a login attempt"""
    login_attempt: LoginAttempt
    risk_score: int  # 0-100
    risk_level: RiskLevel
    signals: List[RiskSignal] = field(default_factory=list)
    recommendation: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def add_signal(self, signal: RiskSignal):
        """Add a risk signal to the assessment"""
        self.signals.append(signal)
        self._recalculate_risk_score()

    def _recalculate_risk_score(self):
        """Recalculate overall risk score based on signals"""
        if not self.signals:
            self.risk_score = 0
            self.risk_level = RiskLevel.SAFE
            return

        # Use maximum severity with diminishing returns for multiple signals
        max_severity = max(s.severity for s in self.signals)
        additional_signals_bonus = min(len(self.signals) - 1, 5) * 5

        self.risk_score = min(100, max_severity + additional_signals_bonus)

        # Determine risk level
        if self.risk_score >= 80:
            self.risk_level = RiskLevel.CRITICAL
            self.recommendation = "BLOCK: High risk of malicious activity detected"
        elif self.risk_score >= 60:
            self.risk_level = RiskLevel.HIGH
            self.recommendation = "CHALLENGE: Require additional authentication (MFA, CAPTCHA)"
        elif self.risk_score >= 40:
            self.risk_level = RiskLevel.MEDIUM
            self.recommendation = "MONITOR: Allow but log for review"
        elif self.risk_score >= 20:
            self.risk_level = RiskLevel.LOW
            self.recommendation = "ALLOW: Minor anomalies detected"
        else:
            self.risk_level = RiskLevel.SAFE
            self.recommendation = "ALLOW: No significant risks detected"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'username': self.login_attempt.username,
            'ip_address': self.login_attempt.ip_address,
            'timestamp': self.login_attempt.timestamp.isoformat(),
            'success': self.login_attempt.success,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level.value,
            'recommendation': self.recommendation,
            'signals': [
                {
                    'type': s.signal_type.value,
                    'severity': s.severity,
                    'severity_label': s.severity_label,
                    'description': s.description,
                    'details': s.details
                }
                for s in self.signals
            ]
        }


@dataclass
class UserProfile:
    """Historical profile of a user's login patterns"""
    username: str
    usual_locations: List[dict] = field(default_factory=list)
    usual_ips: List[str] = field(default_factory=list)
    usual_devices: List[str] = field(default_factory=list)
    usual_login_hours: List[int] = field(default_factory=list)  # 0-23
    last_login: Optional[LoginAttempt] = None
    failed_attempts_count: int = 0
    total_logins: int = 0
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
