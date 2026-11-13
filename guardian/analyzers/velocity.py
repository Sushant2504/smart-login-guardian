from typing import List, Optional
from math import radians, sin, cos, sqrt, atan2
from datetime import timedelta
from ..models import LoginAttempt, RiskSignal, SignalType
from ..storage import LoginStorage


class VelocityAnalyzer:
    """Detects impossible travel (velocity check)"""

    def __init__(self, storage: LoginStorage):
        self.storage = storage
        self.max_speed_kmh = 900  # Speed of commercial aircraft

    def analyze(self, attempt: LoginAttempt) -> List[RiskSignal]:
        """Analyze login attempt for impossible travel"""
        signals = []

        if not attempt.location:
            return signals

        velocity_signal = self._check_impossible_travel(attempt)
        if velocity_signal:
            signals.append(velocity_signal)

        return signals

    def _check_impossible_travel(self, attempt: LoginAttempt) -> Optional[RiskSignal]:
        """Check if travel between locations is physically impossible"""
        profile = self.storage.get_user_profile(attempt.username)

        if not profile or not profile.last_login:
            return None

        last_login = profile.last_login

        if not last_login.location:
            return None

        # Calculate distance between locations
        distance_km = self._calculate_distance(
            last_login.location.get('lat'),
            last_login.location.get('lon'),
            attempt.location.get('lat'),
            attempt.location.get('lon')
        )

        # Calculate time difference
        time_diff = attempt.timestamp - last_login.timestamp

        if time_diff.total_seconds() <= 0:
            return None

        # Calculate required speed
        hours = time_diff.total_seconds() / 3600
        required_speed_kmh = distance_km / hours if hours > 0 else float('inf')

        # Check if travel is impossible
        if required_speed_kmh > self.max_speed_kmh:
            last_location = f"{last_login.location.get('city')}, {last_login.location.get('country')}"
            current_location = f"{attempt.location.get('city')}, {attempt.location.get('country')}"

            time_diff_str = self._format_time_diff(time_diff)

            return RiskSignal(
                signal_type=SignalType.IMPOSSIBLE_TRAVEL,
                severity=90,
                description=f"Impossible travel: {last_location} to {current_location} in {time_diff_str}",
                details={
                    'distance_km': round(distance_km, 2),
                    'time_hours': round(hours, 2),
                    'required_speed_kmh': round(required_speed_kmh, 2),
                    'max_possible_speed_kmh': self.max_speed_kmh,
                    'previous_location': last_location,
                    'current_location': current_location,
                    'pattern': 'impossible_travel'
                }
            )

        return None

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        if None in (lat1, lon1, lat2, lon2):
            return 0

        R = 6371  # Earth's radius in kilometers

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def _format_time_diff(self, td: timedelta) -> str:
        """Format time difference in human-readable form"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
