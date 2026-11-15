"""
Event processing service with ML-powered risk analysis
"""
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json

from app.models.event import Event, EventStatus, RiskLevel
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.repositories.event_repository import EventRepository
from app.repositories.alert_repository import AlertRepository
from app.ml.detector import ml_detector
from app.schemas.event import EventCreate


# Known malicious IPs (example database)
MALICIOUS_IPS = {
    "203.0.113.50": "Botnet C&C Server",
    "198.51.100.200": "Tor Exit Node",
    "192.0.2.100": "Known Attacker",
}

# High-risk countries
HIGH_RISK_REGIONS = ["Russia", "China", "North Korea"]


class EventService:
    """Event processing and risk analysis service"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_repo = EventRepository(db)
        self.alert_repo = AlertRepository(db)

    async def process_event(self, event_data: EventCreate) -> Event:
        """
        Process authentication event with ML-powered risk analysis
        """
        # Get user history
        user_history = await self.event_repo.get_by_user(event_data.user_identifier, limit=100)
        user_history_dicts = [self._event_to_dict(e) for e in user_history]

        # ML anomaly detection
        ml_result = ml_detector.predict(
            event_data.model_dump(),
            user_history_dicts
        )

        # Multi-signal risk analysis
        risk_analysis = self._analyze_risk(event_data, user_history, ml_result)

        # Create event
        event = await self.event_repo.create(
            user_identifier=event_data.user_identifier,
            ip_address=event_data.ip_address,
            country=event_data.country,
            city=event_data.city,
            latitude=event_data.latitude,
            longitude=event_data.longitude,
            device=event_data.device,
            browser=event_data.browser,
            user_agent=event_data.user_agent,
            status=event_data.status,
            risk_score=risk_analysis["score"],
            risk_level=risk_analysis["risk_level"],
            signals=json.dumps(risk_analysis["signals"]),
            ml_anomaly=ml_result["anomaly"],
            ml_score=ml_result["score"],
            ml_features=json.dumps(ml_result.get("features", []))
        )

        # Create alert for high/critical risks
        if risk_analysis["risk_level"] in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            await self._create_alert(event, risk_analysis)

        return event

    def _analyze_risk(
        self,
        event_data: EventCreate,
        user_history: List[Event],
        ml_result: Dict
    ) -> Dict[str, Any]:
        """
        Multi-signal risk analysis combining ML with traditional signals
        """
        signals = []
        score = 0

        # Signal 1: IP Reputation (+30 points)
        if event_data.ip_address in MALICIOUS_IPS:
            threat_type = MALICIOUS_IPS[event_data.ip_address]
            signals.append(f"🚨 Known threat: {threat_type}")
            score += 30

        # Signal 2: Failed Login (+15 points)
        if event_data.status == EventStatus.FAILED:
            signals.append("❌ Failed login attempt")
            score += 15

        # Signal 3: Brute Force Pattern (+25 points)
        recent_failures = [e for e in user_history[:10] if e.status == EventStatus.FAILED]
        if len(recent_failures) >= 3:
            signals.append(f"🔨 Brute force pattern ({len(recent_failures)} failures)")
            score += 25

        # Signal 4: Geographic Anomaly (+20 points)
        if user_history:
            user_countries = set(e.country for e in user_history[:20] if e.country)
            if event_data.country and event_data.country not in user_countries and len(user_countries) > 0:
                signals.append(f"🌍 New location: {event_data.country}")
                score += 20

        # Signal 5: High-Risk Region (+15 points)
        if event_data.country in HIGH_RISK_REGIONS:
            signals.append(f"⚠️ High-risk region: {event_data.country}")
            score += 15

        # Signal 6: ML Anomaly (0-40 points)
        if ml_result["status"] == "active":
            if ml_result["anomaly"]:
                signals.append(f"🤖 ML Anomaly Detected (score: {ml_result['score']})")
                score += min(40, ml_result["score"])

        # Cap total score at 100
        final_score = min(100, score)

        # Classify risk level
        if final_score < 20:
            risk_level = RiskLevel.LOW
        elif final_score < 40:
            risk_level = RiskLevel.MODERATE
        elif final_score < 60:
            risk_level = RiskLevel.ELEVATED
        elif final_score < 80:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        return {
            "score": final_score,
            "risk_level": risk_level,
            "signals": signals
        }

    async def _create_alert(self, event: Event, risk_analysis: Dict) -> Alert:
        """Create security alert for high-risk events"""
        severity_map = {
            RiskLevel.HIGH: AlertSeverity.HIGH,
            RiskLevel.CRITICAL: AlertSeverity.CRITICAL
        }

        alert = await self.alert_repo.create(
            event_id=event.id,
            title=f"{risk_analysis['risk_level'].upper()} Risk Login Detected",
            description=f"Detected high-risk login for {event.user_identifier} from {event.ip_address}. "
                       f"Risk score: {risk_analysis['score']}. "
                       f"Signals: {', '.join(risk_analysis['signals'])}",
            severity=severity_map.get(risk_analysis["risk_level"], AlertSeverity.HIGH),
            status=AlertStatus.OPEN
        )
        return alert

    def _event_to_dict(self, event: Event) -> Dict:
        """Convert event model to dictionary for ML processing"""
        return {
            "user_identifier": event.user_identifier,
            "ip_address": event.ip_address,
            "status": event.status.value,
            "country": event.country,
            "created_at": event.created_at.isoformat() if event.created_at else None
        }

    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        total = await self.event_repo.count()

        # Count by status
        success_count = await self.event_repo.count_by_status(EventStatus.SUCCESS)
        failed_count = await self.event_repo.count_by_status(EventStatus.FAILED)

        # Count by risk level
        critical_count = await self.event_repo.count_by_risk_level(RiskLevel.CRITICAL)
        high_count = await self.event_repo.count_by_risk_level(RiskLevel.HIGH)
        elevated_count = await self.event_repo.count_by_risk_level(RiskLevel.ELEVATED)
        moderate_count = await self.event_repo.count_by_risk_level(RiskLevel.MODERATE)
        low_count = await self.event_repo.count_by_risk_level(RiskLevel.LOW)

        # Get recent events
        recent_events = await self.event_repo.get_recent(limit=20)

        # ML stats
        ml_stats = ml_detector.get_stats()

        return {
            "total_events": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": round((success_count / total * 100) if total > 0 else 0, 1),
            "failure_rate": round((failed_count / total * 100) if total > 0 else 0, 1),
            "critical_alerts": critical_count,
            "high_alerts": high_count,
            "elevated_alerts": elevated_count,
            "moderate_alerts": moderate_count,
            "low_alerts": low_count,
            "ml_status": ml_stats["status"],
            "ml_processed": ml_stats["total_processed"],
            "ml_anomalies": ml_stats["anomalies_detected"],
            "ml_training_progress": ml_stats["training_progress"],
            "recent_events": [self._event_to_response(e) for e in recent_events],
            "risk_distribution": {
                "critical": critical_count,
                "high": high_count,
                "elevated": elevated_count,
                "moderate": moderate_count,
                "low": low_count
            }
        }

    def _event_to_response(self, event: Event) -> Dict:
        """Convert event to response dict"""
        return {
            "id": str(event.id),
            "user_identifier": event.user_identifier,
            "ip_address": event.ip_address,
            "country": event.country,
            "city": event.city,
            "risk_score": event.risk_score,
            "risk_level": event.risk_level.value,
            "status": event.status.value,
            "ml_anomaly": event.ml_anomaly,
            "signals": json.loads(event.signals) if event.signals else [],
            "created_at": event.created_at.isoformat() if event.created_at else None
        }
