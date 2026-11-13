from typing import List, Optional
from ..models import LoginAttempt, RiskSignal, SignalType
from ..storage import LoginStorage


class BruteForceAnalyzer:
    """Detects brute force and credential stuffing attacks"""

    def __init__(self, storage: LoginStorage):
        self.storage = storage

    def analyze(self, attempt: LoginAttempt) -> List[RiskSignal]:
        """Analyze login attempt for brute force patterns"""
        signals = []

        # Check for multiple failed attempts
        failed_signal = self._check_failed_attempts(attempt)
        if failed_signal:
            signals.append(failed_signal)

        # Check for account enumeration
        enumeration_signal = self._check_account_enumeration(attempt)
        if enumeration_signal:
            signals.append(enumeration_signal)

        # Check for credential stuffing patterns
        stuffing_signal = self._check_credential_stuffing(attempt)
        if stuffing_signal:
            signals.append(stuffing_signal)

        return signals

    def _check_failed_attempts(self, attempt: LoginAttempt) -> Optional[RiskSignal]:
        """Check for multiple failed login attempts"""
        recent_failed = self.storage.get_recent_failed_attempts(
            attempt.username,
            minutes=30
        )

        if not recent_failed:
            return None

        count = len(recent_failed)

        if count >= 10:
            return RiskSignal(
                signal_type=SignalType.BRUTE_FORCE,
                severity=95,
                description=f"Critical: {count} failed login attempts in the last 30 minutes",
                details={
                    'failed_attempts': count,
                    'time_window': '30 minutes',
                    'pattern': 'aggressive_brute_force'
                }
            )
        elif count >= 5:
            return RiskSignal(
                signal_type=SignalType.BRUTE_FORCE,
                severity=75,
                description=f"High: {count} failed login attempts in the last 30 minutes",
                details={
                    'failed_attempts': count,
                    'time_window': '30 minutes',
                    'pattern': 'moderate_brute_force'
                }
            )
        elif count >= 3:
            return RiskSignal(
                signal_type=SignalType.BRUTE_FORCE,
                severity=50,
                description=f"Medium: {count} failed login attempts in the last 30 minutes",
                details={
                    'failed_attempts': count,
                    'time_window': '30 minutes',
                    'pattern': 'possible_brute_force'
                }
            )

        return None

    def _check_account_enumeration(self, attempt: LoginAttempt) -> Optional[RiskSignal]:
        """Check if IP is trying multiple different usernames"""
        unique_usernames = self.storage.get_unique_usernames_from_ip(
            attempt.ip_address,
            minutes=60
        )

        count = len(unique_usernames)

        if count >= 20:
            return RiskSignal(
                signal_type=SignalType.ACCOUNT_ENUMERATION,
                severity=85,
                description=f"Critical: {count} different usernames attempted from this IP in the last hour",
                details={
                    'unique_usernames': count,
                    'time_window': '60 minutes',
                    'pattern': 'account_enumeration'
                }
            )
        elif count >= 10:
            return RiskSignal(
                signal_type=SignalType.ACCOUNT_ENUMERATION,
                severity=65,
                description=f"High: {count} different usernames attempted from this IP in the last hour",
                details={
                    'unique_usernames': count,
                    'time_window': '60 minutes',
                    'pattern': 'possible_enumeration'
                }
            )

        return None

    def _check_credential_stuffing(self, attempt: LoginAttempt) -> Optional[RiskSignal]:
        """Check for credential stuffing patterns (many IPs, one username)"""
        recent_attempts = self.storage.get_recent_attempts(
            attempt.username,
            minutes=60
        )

        if not recent_attempts:
            return None

        unique_ips = len({a.ip_address for a in recent_attempts})

        if unique_ips >= 10:
            return RiskSignal(
                signal_type=SignalType.CREDENTIAL_STUFFING,
                severity=80,
                description=f"High: Login attempts from {unique_ips} different IPs in the last hour",
                details={
                    'unique_ips': unique_ips,
                    'time_window': '60 minutes',
                    'pattern': 'credential_stuffing'
                }
            )
        elif unique_ips >= 5:
            return RiskSignal(
                signal_type=SignalType.CREDENTIAL_STUFFING,
                severity=60,
                description=f"Medium: Login attempts from {unique_ips} different IPs in the last hour",
                details={
                    'unique_ips': unique_ips,
                    'time_window': '60 minutes',
                    'pattern': 'possible_stuffing'
                }
            )

        return None
