#!/usr/bin/env python3
"""
Basic usage example for Smart Login Guardian
"""

from datetime import datetime
from guardian import LoginGuardian

def main():
    # Initialize the guardian
    guardian = LoginGuardian()

    print("Smart Login Guardian - Basic Usage Example\n")

    # Example 1: Normal login
    print("=" * 70)
    print("Example 1: Normal Login")
    print("=" * 70)
    normal_login = guardian.analyze_login({
        'username': 'user@example.com',
        'ip_address': '192.168.1.100',
        'timestamp': datetime.utcnow(),
        'success': True,
        'location': {
            'country': 'US',
            'city': 'San Francisco',
            'lat': 37.7749,
            'lon': -122.4194
        }
    })
    print(f"Risk Score: {normal_login.risk_score}/100")
    print(f"Risk Level: {normal_login.risk_level.value}")
    print(f"Signals: {len(normal_login.signals)}\n")

    # Example 2: Multiple failed attempts (brute force)
    print("=" * 70)
    print("Example 2: Brute Force Attack (Multiple Failed Attempts)")
    print("=" * 70)
    for i in range(5):
        guardian.analyze_login({
            'username': 'victim@example.com',
            'ip_address': '203.0.113.50',
            'timestamp': datetime.utcnow(),
            'success': False
        })

    brute_force_attempt = guardian.analyze_login({
        'username': 'victim@example.com',
        'ip_address': '203.0.113.50',
        'timestamp': datetime.utcnow(),
        'success': False
    })
    print(f"Risk Score: {brute_force_attempt.risk_score}/100")
    print(f"Risk Level: {brute_force_attempt.risk_level.value}")
    print(f"Recommendation: {brute_force_attempt.recommendation}")
    for signal in brute_force_attempt.signals:
        print(f"  - {signal.description}\n")

    # Example 3: Impossible travel
    print("=" * 70)
    print("Example 3: Impossible Travel Detection")
    print("=" * 70)
    # First login from New York
    guardian.analyze_login({
        'username': 'traveler@example.com',
        'ip_address': '192.168.1.1',
        'timestamp': '2026-11-08T10:00:00Z',
        'success': True,
        'location': {
            'country': 'US',
            'city': 'New York',
            'lat': 40.7128,
            'lon': -74.0060
        }
    })

    # Login from London 30 minutes later (impossible!)
    impossible_travel = guardian.analyze_login({
        'username': 'traveler@example.com',
        'ip_address': '198.51.100.1',
        'timestamp': '2026-11-08T10:30:00Z',
        'success': True,
        'location': {
            'country': 'GB',
            'city': 'London',
            'lat': 51.5074,
            'lon': -0.1278
        }
    })
    print(f"Risk Score: {impossible_travel.risk_score}/100")
    print(f"Risk Level: {impossible_travel.risk_level.value}")
    for signal in impossible_travel.signals:
        print(f"  - {signal.description}")
        if 'distance_km' in signal.details:
            print(f"    Distance: {signal.details['distance_km']} km")
            print(f"    Required Speed: {signal.details['required_speed_kmh']} km/h\n")

    # Example 4: Account enumeration
    print("=" * 70)
    print("Example 4: Account Enumeration Attack")
    print("=" * 70)
    attacker_ip = '198.51.100.99'
    for i in range(15):
        guardian.analyze_login({
            'username': f'user{i}@example.com',
            'ip_address': attacker_ip,
            'timestamp': datetime.utcnow(),
            'success': False
        })

    enumeration = guardian.analyze_login({
        'username': 'user99@example.com',
        'ip_address': attacker_ip,
        'timestamp': datetime.utcnow(),
        'success': False
    })
    print(f"Risk Score: {enumeration.risk_score}/100")
    print(f"Risk Level: {enumeration.risk_level.value}")
    for signal in enumeration.signals:
        print(f"  - {signal.description}\n")

    # Show overall statistics
    print("=" * 70)
    print("Overall Statistics")
    print("=" * 70)
    stats = guardian.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == '__main__':
    main()
