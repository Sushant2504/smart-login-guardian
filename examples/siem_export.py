#!/usr/bin/env python3
"""
SIEM Export Example
Demonstrates exporting security events to various SIEM formats
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime
from guardian import LoginGuardian
from guardian.siem import SIEMExporter


def main():
    print("=" * 80)
    print("SIEM INTEGRATION EXAMPLE")
    print("=" * 80)

    guardian = LoginGuardian()

    # Simulate a high-risk login event
    print("\n📡 Analyzing suspicious login attempt...\n")

    assessment = guardian.analyze_login({
        'username': 'admin@company.com',
        'ip_address': '203.0.113.100',
        'timestamp': datetime.utcnow(),
        'success': False,
        'user_agent': 'curl/7.68.0',
        'location': {
            'country': 'RU',
            'city': 'Moscow',
            'lat': 55.7558,
            'lon': 37.6173
        }
    })

    print(f"Risk Score: {assessment.risk_score}/100")
    print(f"Risk Level: {assessment.risk_level.value}")
    print(f"Signals Detected: {len(assessment.signals)}")

    # Export to various SIEM formats
    print("\n" + "=" * 80)
    print("SIEM EXPORT FORMATS")
    print("=" * 80)

    print("\n1. Common Event Format (CEF) - for ArcSight, QRadar:")
    print("-" * 80)
    cef = SIEMExporter.to_cef(assessment)
    print(cef)

    print("\n2. Log Event Extended Format (LEEF) - for IBM QRadar:")
    print("-" * 80)
    leef = SIEMExporter.to_leef(assessment)
    print(leef)

    print("\n3. JSON Format - for Elastic Stack, modern SIEMs:")
    print("-" * 80)
    import json
    json_output = SIEMExporter.to_json(assessment)
    print(json.dumps(json.loads(json_output), indent=2))

    print("\n4. Splunk Format - key-value pairs:")
    print("-" * 80)
    splunk = SIEMExporter.to_splunk(assessment)
    print(splunk)

    print("\n" + "=" * 80)
    print("✅ SIEM export examples complete")
    print("=" * 80)


if __name__ == '__main__':
    main()
