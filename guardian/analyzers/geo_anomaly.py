from typing import List, Optional
from ..models import LoginAttempt, RiskSignal, SignalType
from ..storage import LoginStorage


class GeoAnomalyAnalyzer:
    """Detects geographic anomalies in login patterns"""

    def __init__(self, storage: LoginStorage):
        self.storage = storage
        self.high_risk_countries = {'CN', 'RU', 'KP', 'IR'}  # Example high-risk list

    def analyze(self, attempt: LoginAttempt) -> List[RiskSignal]:
        """Analyze login attempt for geographic anomalies"""
        signals = []

        if not attempt.location:
            return signals

        # Check for new/unusual location
        location_signal = self._check_unusual_location(attempt)
        if location_signal:
            signals.append(location_signal)

        # Check for high-risk countries
        high_risk_signal = self._check_high_risk_country(attempt)
        if high_risk_signal:
            signals.append(high_risk_signal)

        return signals

    def _check_unusual_location(self, attempt: LoginAttempt) -> Optional[RiskSignal]:
        """Check if login is from an unusual location"""
        profile = self.storage.get_user_profile(attempt.username)

        if not profile or profile.total_logins < 3:
            # Not enough history to determine normal
            return None

        if not profile.usual_locations:
            return None

        # Check if current location matches any usual locations
        current_country = attempt.location.get('country')
        usual_countries = {loc.get('country') for loc in profile.usual_locations}

        if current_country not in usual_countries:
            return RiskSignal(
                signal_type=SignalType.GEO_ANOMALY,
                severity=70,
                description=f"Login from new country: {current_country}",
                details={
                    'current_country': current_country,
                    'current_city': attempt.location.get('city'),
                    'usual_countries': list(usual_countries),
                    'pattern': 'new_location'
                }
            )

        # Check for new city in same country
        current_city = attempt.location.get('city')
        usual_cities = {loc.get('city') for loc in profile.usual_locations}

        if current_city and current_city not in usual_cities:
            return RiskSignal(
                signal_type=SignalType.GEO_ANOMALY,
                severity=40,
                description=f"Login from new city: {current_city}, {current_country}",
                details={
                    'current_city': current_city,
                    'current_country': current_country,
                    'usual_cities': list(usual_cities),
                    'pattern': 'new_city'
                }
            )

        return None

    def _check_high_risk_country(self, attempt: LoginAttempt) -> Optional[RiskSignal]:
        """Check if login is from a high-risk country"""
        if not attempt.location:
            return None

        country = attempt.location.get('country')

        if country in self.high_risk_countries:
            return RiskSignal(
                signal_type=SignalType.SUSPICIOUS_IP,
                severity=60,
                description=f"Login from high-risk country: {country}",
                details={
                    'country': country,
                    'risk_category': 'high_risk_geography'
                }
            )

        return None
