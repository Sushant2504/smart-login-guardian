from typing import List, Optional
from ..models import LoginAttempt, RiskSignal, SignalType
from ..storage import LoginStorage


class TimeAnomalyAnalyzer:
    """Detects temporal anomalies in login patterns"""

    def __init__(self, storage: LoginStorage):
        self.storage = storage

    def analyze(self, attempt: LoginAttempt) -> List[RiskSignal]:
        """Analyze login attempt for time-based anomalies"""
        signals = []

        # Check for unusual login hours
        unusual_time_signal = self._check_unusual_time(attempt)
        if unusual_time_signal:
            signals.append(unusual_time_signal)

        return signals

    def _check_unusual_time(self, attempt: LoginAttempt) -> Optional[RiskSignal]:
        """Check if login occurs at an unusual time for this user"""
        profile = self.storage.get_user_profile(attempt.username)

        if not profile or profile.total_logins < 5:
            # Not enough history to determine normal patterns
            return None

        if not profile.usual_login_hours:
            return None

        current_hour = attempt.timestamp.hour

        # Check if current hour is within usual hours
        # Allow +/- 2 hours from usual times
        is_usual = False
        for usual_hour in profile.usual_login_hours:
            if abs(current_hour - usual_hour) <= 2:
                is_usual = True
                break
            # Handle wrap-around (e.g., 23 and 1)
            if abs(current_hour - usual_hour - 24) <= 2:
                is_usual = True
                break
            if abs(current_hour - usual_hour + 24) <= 2:
                is_usual = True
                break

        if not is_usual:
            # Determine if it's night time (higher risk)
            is_night = current_hour < 6 or current_hour >= 22
            severity = 60 if is_night else 35

            time_str = f"{current_hour:02d}:00"
            usual_times = [f"{h:02d}:00" for h in sorted(profile.usual_login_hours)]

            return RiskSignal(
                signal_type=SignalType.TIME_ANOMALY,
                severity=severity,
                description=f"Login at unusual time: {time_str} (usual times: {', '.join(usual_times[:3])})",
                details={
                    'current_hour': current_hour,
                    'usual_hours': profile.usual_login_hours,
                    'is_night_time': is_night,
                    'pattern': 'unusual_time'
                }
            )

        return None
