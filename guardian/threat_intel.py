"""
Threat Intelligence Module
Integrates with threat intelligence feeds to detect malicious IPs and patterns
"""

from typing import Dict, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class ThreatIntelligence:
    """Threat intelligence database"""

    # Known malicious IPs
    malicious_ips: Set[str] = field(default_factory=set)

    # Known VPN/Proxy IPs (can be used to hide location)
    vpn_ips: Set[str] = field(default_factory=set)

    # Known bot user agents
    bot_user_agents: Set[str] = field(default_factory=set)

    # IP reputation scores (0-100, higher = worse)
    ip_reputation: Dict[str, int] = field(default_factory=dict)

    # Recently reported IPs
    recent_reports: Dict[str, datetime] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize with some default known threats"""
        # Example malicious IPs (normally would come from threat feeds)
        self.malicious_ips.update([
            '198.51.100.0/24',  # Example range
            '203.0.113.0/24',   # Example range
        ])

        # Common bot user agents
        self.bot_user_agents.update([
            'curl',
            'wget',
            'python-requests',
            'scrapy',
            'bot',
            'crawler',
            'scanner',
            'nikto',
            'sqlmap',
            'nmap',
            'masscan',
        ])

    def check_ip_malicious(self, ip: str) -> bool:
        """Check if IP is known malicious"""
        # Simple check - in production, use proper CIDR matching
        for malicious_range in self.malicious_ips:
            if ip.startswith(malicious_range.split('/')[0][:7]):
                return True
        return False

    def check_ip_vpn(self, ip: str) -> bool:
        """Check if IP is a known VPN/proxy"""
        return ip in self.vpn_ips

    def get_ip_reputation(self, ip: str) -> int:
        """Get IP reputation score (0-100, higher is worse)"""
        if self.check_ip_malicious(ip):
            return 95

        if ip in self.ip_reputation:
            return self.ip_reputation[ip]

        # Check if recently reported
        if ip in self.recent_reports:
            report_age = datetime.utcnow() - self.recent_reports[ip]
            if report_age < timedelta(hours=24):
                return 70
            elif report_age < timedelta(days=7):
                return 50

        return 0

    def check_user_agent_suspicious(self, user_agent: Optional[str]) -> bool:
        """Check if user agent indicates a bot or scanner"""
        if not user_agent:
            return True  # No user agent is suspicious

        user_agent_lower = user_agent.lower()

        for bot_pattern in self.bot_user_agents:
            if bot_pattern in user_agent_lower:
                return True

        return False

    def report_ip(self, ip: str, reason: str):
        """Report an IP as suspicious"""
        self.recent_reports[ip] = datetime.utcnow()

        # Update reputation
        current_rep = self.ip_reputation.get(ip, 0)
        self.ip_reputation[ip] = min(100, current_rep + 20)

    def add_malicious_ip(self, ip: str):
        """Add IP to malicious list"""
        self.malicious_ips.add(ip)
        self.ip_reputation[ip] = 100

    def cleanup_old_reports(self, days: int = 30):
        """Remove old reports"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        self.recent_reports = {
            ip: timestamp
            for ip, timestamp in self.recent_reports.items()
            if timestamp >= cutoff
        }
