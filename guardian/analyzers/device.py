from typing import List, Optional
from ..models import LoginAttempt, RiskSignal, SignalType
from ..storage import LoginStorage


class DeviceAnalyzer:
    """Detects new or suspicious devices"""

    def __init__(self, storage: LoginStorage):
        self.storage = storage

    def analyze(self, attempt: LoginAttempt) -> List[RiskSignal]:
        """Analyze login attempt for device-related signals"""
        signals = []

        # Check for new device
        new_device_signal = self._check_new_device(attempt)
        if new_device_signal:
            signals.append(new_device_signal)

        # Check for new IP
        new_ip_signal = self._check_new_ip(attempt)
        if new_ip_signal:
            signals.append(new_ip_signal)

        return signals

    def _check_new_device(self, attempt: LoginAttempt) -> Optional[RiskSignal]:
        """Check if login is from a new device"""
        if not attempt.device_fingerprint:
            return None

        profile = self.storage.get_user_profile(attempt.username)

        if not profile or profile.total_logins < 2:
            # Not enough history
            return None

        if attempt.device_fingerprint not in profile.usual_devices:
            return RiskSignal(
                signal_type=SignalType.NEW_DEVICE,
                severity=55,
                description="Login from a new device",
                details={
                    'device_fingerprint': attempt.device_fingerprint,
                    'user_agent': attempt.user_agent,
                    'known_devices_count': len(profile.usual_devices),
                    'pattern': 'new_device'
                }
            )

        return None

    def _check_new_ip(self, attempt: LoginAttempt) -> Optional[RiskSignal]:
        """Check if login is from a new IP address"""
        profile = self.storage.get_user_profile(attempt.username)

        if not profile or profile.total_logins < 3:
            # Not enough history
            return None

        if attempt.ip_address not in profile.usual_ips:
            return RiskSignal(
                signal_type=SignalType.SUSPICIOUS_IP,
                severity=45,
                description=f"Login from new IP address: {attempt.ip_address}",
                details={
                    'ip_address': attempt.ip_address,
                    'known_ips_count': len(profile.usual_ips),
                    'pattern': 'new_ip'
                }
            )

        return None
