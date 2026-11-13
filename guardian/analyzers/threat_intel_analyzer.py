from typing import List, Optional
from ..models import LoginAttempt, RiskSignal, SignalType
from ..threat_intel import ThreatIntelligence


class ThreatIntelAnalyzer:
    """Analyzes login attempts against threat intelligence data"""

    def __init__(self, threat_intel: ThreatIntelligence):
        self.threat_intel = threat_intel

    def analyze(self, attempt: LoginAttempt) -> List[RiskSignal]:
        """Analyze login attempt against threat intelligence"""
        signals = []

        # Check IP reputation
        ip_signal = self._check_ip_reputation(attempt)
        if ip_signal:
            signals.append(ip_signal)

        # Check user agent
        ua_signal = self._check_user_agent(attempt)
        if ua_signal:
            signals.append(ua_signal)

        return signals

    def _check_ip_reputation(self, attempt: LoginAttempt) -> Optional[RiskSignal]:
        """Check IP against threat intelligence"""
        reputation = self.threat_intel.get_ip_reputation(attempt.ip_address)

        if reputation >= 90:
            return RiskSignal(
                signal_type=SignalType.SUSPICIOUS_IP,
                severity=95,
                description=f"IP address is known malicious: {attempt.ip_address}",
                details={
                    'ip_address': attempt.ip_address,
                    'reputation_score': reputation,
                    'threat_level': 'critical'
                }
            )
        elif reputation >= 70:
            return RiskSignal(
                signal_type=SignalType.SUSPICIOUS_IP,
                severity=75,
                description=f"IP address has poor reputation (score: {reputation})",
                details={
                    'ip_address': attempt.ip_address,
                    'reputation_score': reputation,
                    'threat_level': 'high'
                }
            )
        elif reputation >= 50:
            return RiskSignal(
                signal_type=SignalType.SUSPICIOUS_IP,
                severity=55,
                description=f"IP address has questionable reputation (score: {reputation})",
                details={
                    'ip_address': attempt.ip_address,
                    'reputation_score': reputation,
                    'threat_level': 'medium'
                }
            )

        return None

    def _check_user_agent(self, attempt: LoginAttempt) -> Optional[RiskSignal]:
        """Check if user agent is suspicious"""
        if self.threat_intel.check_user_agent_suspicious(attempt.user_agent):
            return RiskSignal(
                signal_type=SignalType.SUSPICIOUS_IP,
                severity=65,
                description=f"Suspicious user agent detected: {attempt.user_agent or 'None'}",
                details={
                    'user_agent': attempt.user_agent,
                    'pattern': 'bot_or_scanner'
                }
            )

        return None
