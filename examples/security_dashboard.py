#!/usr/bin/env python3
"""
Security Dashboard Example
Demonstrates comprehensive security monitoring and threat detection
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
from guardian import LoginGuardian, RiskLevel
from guardian.threat_intel import ThreatIntelligence
from guardian.analyzers.threat_intel_analyzer import ThreatIntelAnalyzer


class SecurityDashboard:
    """Security monitoring dashboard"""

    def __init__(self):
        self.guardian = LoginGuardian()
        self.threat_intel = ThreatIntelligence()

        # Add threat intel analyzer
        threat_analyzer = ThreatIntelAnalyzer(self.threat_intel)
        self.guardian.analyzers.append(threat_analyzer)

    def analyze_attack_scenario(self, name: str, attacks: list):
        """Analyze a security attack scenario"""
        print("\n" + "=" * 80)
        print(f"SECURITY SCENARIO: {name}")
        print("=" * 80)

        high_risk_count = 0
        critical_count = 0

        for attack in attacks:
            result = self.guardian.analyze_login(attack)

            if result.risk_level == RiskLevel.CRITICAL:
                critical_count += 1
                print(f"\n🚨 CRITICAL ALERT - {attack['username']} from {attack['ip_address']}")
            elif result.risk_level == RiskLevel.HIGH:
                high_risk_count += 1
                print(f"\n⚠️  HIGH RISK - {attack['username']} from {attack['ip_address']}")
            elif result.risk_score >= 40:
                print(f"\n⚡ MEDIUM RISK - {attack['username']} from {attack['ip_address']}")

            if result.risk_score >= 40:
                print(f"   Risk Score: {result.risk_score}/100")
                print(f"   Recommendation: {result.recommendation}")
                for signal in result.signals:
                    print(f"   • {signal.description}")

        print(f"\n📊 Scenario Summary:")
        print(f"   Total Attempts: {len(attacks)}")
        print(f"   Critical Alerts: {critical_count}")
        print(f"   High Risk: {high_risk_count}")
        print("=" * 80)

    def run_security_simulations(self):
        """Run various security attack simulations"""

        # Scenario 1: Advanced Persistent Threat (APT)
        apt_attacks = []
        base_time = datetime.utcnow()

        # Slow and low attack - trying to stay under radar
        for i in range(3):
            apt_attacks.append({
                'username': 'cto@company.com',
                'ip_address': '198.51.100.50',
                'timestamp': base_time + timedelta(minutes=i * 20),
                'success': False,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'location': {'country': 'CN', 'city': 'Shanghai', 'lat': 31.2304, 'lon': 121.4737}
            })

        self.analyze_attack_scenario("Advanced Persistent Threat (APT)", apt_attacks)

        # Scenario 2: Credential Stuffing Attack
        stuffing_attacks = []
        leaked_passwords_ip = '203.0.113.100'

        for i in range(20):
            stuffing_attacks.append({
                'username': f'user{i}@company.com',
                'ip_address': leaked_passwords_ip,
                'timestamp': base_time + timedelta(seconds=i * 2),
                'success': False,
                'user_agent': 'python-requests/2.28.0'
            })

        self.threat_intel.report_ip(leaked_passwords_ip, 'credential_stuffing')
        self.analyze_attack_scenario("Credential Stuffing Attack", stuffing_attacks)

        # Scenario 3: Insider Threat
        insider_attacks = []

        # Normal logins first
        for i in range(5):
            self.guardian.analyze_login({
                'username': 'insider@company.com',
                'ip_address': '192.168.1.100',
                'timestamp': base_time - timedelta(days=7 - i),
                'success': True,
                'location': {'country': 'US', 'city': 'San Francisco', 'lat': 37.7749, 'lon': -122.4194}
            })

        # Suspicious late-night access
        insider_attacks.append({
            'username': 'insider@company.com',
            'ip_address': '192.168.1.100',
            'timestamp': base_time.replace(hour=2, minute=30),
            'success': True,
            'location': {'country': 'US', 'city': 'San Francisco', 'lat': 37.7749, 'lon': -122.4194}
        })

        self.analyze_attack_scenario("Insider Threat - Unusual Time Access", insider_attacks)

        # Scenario 4: Account Takeover via Session Hijacking
        takeover_attacks = []

        # Legitimate user login
        self.guardian.analyze_login({
            'username': 'victim@company.com',
            'ip_address': '192.168.1.50',
            'timestamp': base_time - timedelta(hours=2),
            'success': True,
            'device_fingerprint': 'device_legitimate_123',
            'location': {'country': 'US', 'city': 'Boston', 'lat': 42.3601, 'lon': -71.0589}
        })

        # Attacker using stolen session from different location
        takeover_attacks.append({
            'username': 'victim@company.com',
            'ip_address': '198.51.100.200',
            'timestamp': base_time,
            'success': True,
            'device_fingerprint': 'device_attacker_999',
            'location': {'country': 'RU', 'city': 'Moscow', 'lat': 55.7558, 'lon': 37.6173}
        })

        self.analyze_attack_scenario("Account Takeover / Session Hijacking", takeover_attacks)

        # Scenario 5: Distributed Brute Force
        distributed_attacks = []
        attacker_ips = ['198.51.100.' + str(i) for i in range(10, 20)]

        for ip in attacker_ips:
            for attempt in range(3):
                distributed_attacks.append({
                    'username': 'admin@company.com',
                    'ip_address': ip,
                    'timestamp': base_time + timedelta(seconds=len(distributed_attacks) * 2),
                    'success': False,
                    'user_agent': 'curl/7.68.0'
                })

        self.analyze_attack_scenario("Distributed Brute Force Attack", distributed_attacks)

        # Scenario 6: Web Scraping / Reconnaissance
        recon_attacks = []
        scanner_ip = '203.0.113.250'

        for i in range(50):
            recon_attacks.append({
                'username': f'test{i}@company.com',
                'ip_address': scanner_ip,
                'timestamp': base_time + timedelta(seconds=i),
                'success': False,
                'user_agent': 'nikto/2.1.6'
            })

        self.analyze_attack_scenario("Reconnaissance / Scanning Activity", recon_attacks)

    def show_threat_intelligence_summary(self):
        """Display threat intelligence summary"""
        print("\n" + "=" * 80)
        print("THREAT INTELLIGENCE SUMMARY")
        print("=" * 80)
        print(f"Known Malicious IPs: {len(self.threat_intel.malicious_ips)}")
        print(f"Recent IP Reports: {len(self.threat_intel.recent_reports)}")
        print(f"IP Reputation Scores: {len(self.threat_intel.ip_reputation)}")

        if self.threat_intel.recent_reports:
            print("\nRecently Reported IPs:")
            for ip, timestamp in list(self.threat_intel.recent_reports.items())[:5]:
                print(f"  {ip} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        print("=" * 80)


def main():
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║         SMART LOGIN GUARDIAN - SECURITY DASHBOARD                ║
    ║                  Threat Detection & Analysis                     ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

    dashboard = SecurityDashboard()

    print("\n🔍 Running Security Attack Simulations...\n")
    dashboard.run_security_simulations()

    print("\n📈 Overall System Statistics:")
    stats = dashboard.guardian.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    dashboard.show_threat_intelligence_summary()

    print("\n✅ Security analysis complete!")


if __name__ == '__main__':
    main()
