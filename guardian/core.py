from typing import Dict, Any, Optional
from datetime import datetime

from .models import LoginAttempt, RiskAssessment
from .storage import LoginStorage
from .analyzers import (
    BruteForceAnalyzer,
    GeoAnomalyAnalyzer,
    TimeAnomalyAnalyzer,
    VelocityAnalyzer,
    DeviceAnalyzer
)


class LoginGuardian:
    """Main class for analyzing login attempts and detecting suspicious activity"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LoginGuardian

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.storage = LoginStorage(
            persistence_path=self.config.get('persistence_path')
        )

        # Initialize analyzers
        self.analyzers = [
            BruteForceAnalyzer(self.storage),
            GeoAnomalyAnalyzer(self.storage),
            TimeAnomalyAnalyzer(self.storage),
            VelocityAnalyzer(self.storage),
            DeviceAnalyzer(self.storage)
        ]

    def analyze_login(self, login_data: Dict[str, Any]) -> RiskAssessment:
        """
        Analyze a login attempt and return risk assessment

        Args:
            login_data: Dictionary containing login attempt data
                Required: username, ip_address, timestamp, success
                Optional: user_agent, location, device_fingerprint, session_id

        Returns:
            RiskAssessment with risk score and detected signals
        """
        # Parse login attempt
        attempt = self._parse_login_attempt(login_data)

        # Create risk assessment
        assessment = RiskAssessment(
            login_attempt=attempt,
            risk_score=0,
            risk_level=None
        )

        # Run all analyzers
        for analyzer in self.analyzers:
            signals = analyzer.analyze(attempt)
            for signal in signals:
                assessment.add_signal(signal)

        # Store the login attempt
        self.storage.add_login_attempt(attempt)

        return assessment

    def _parse_login_attempt(self, data: Dict[str, Any]) -> LoginAttempt:
        """Parse login data into LoginAttempt object"""
        return LoginAttempt(
            username=data['username'],
            ip_address=data['ip_address'],
            timestamp=data.get('timestamp', datetime.utcnow()),
            success=data.get('success', True),
            user_agent=data.get('user_agent'),
            location=data.get('location'),
            device_fingerprint=data.get('device_fingerprint'),
            session_id=data.get('session_id')
        )

    def get_user_profile(self, username: str):
        """Get historical profile for a user"""
        return self.storage.get_user_profile(username)

    def cleanup_old_data(self, days: int = 30):
        """Remove login data older than specified days"""
        self.storage.cleanup_old_entries(days)

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        total_attempts = len(self.storage.login_history)
        total_users = len(self.storage.user_profiles)
        total_ips = len(self.storage.ip_history)

        failed_attempts = sum(
            1 for attempt in self.storage.login_history
            if not attempt.success
        )

        return {
            'total_login_attempts': total_attempts,
            'total_users': total_users,
            'total_unique_ips': total_ips,
            'failed_attempts': failed_attempts,
            'success_rate': (total_attempts - failed_attempts) / total_attempts * 100
            if total_attempts > 0 else 0
        }
