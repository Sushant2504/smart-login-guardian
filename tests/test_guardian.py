#!/usr/bin/env python3
"""
Tests for Smart Login Guardian
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
from guardian import LoginGuardian, RiskLevel


def test_normal_login():
    """Test that normal login has low risk"""
    guardian = LoginGuardian()

    result = guardian.analyze_login({
        'username': 'test@example.com',
        'ip_address': '192.168.1.1',
        'timestamp': datetime.utcnow(),
        'success': True
    })

    assert result.risk_score < 30, "Normal login should have low risk score"
    print("✓ Normal login test passed")


def test_brute_force_detection():
    """Test brute force detection"""
    guardian = LoginGuardian()

    # Generate multiple failed attempts
    for i in range(6):
        guardian.analyze_login({
            'username': 'victim@example.com',
            'ip_address': '203.0.113.50',
            'timestamp': datetime.utcnow(),
            'success': False
        })

    # Next attempt should be flagged
    result = guardian.analyze_login({
        'username': 'victim@example.com',
        'ip_address': '203.0.113.50',
        'timestamp': datetime.utcnow(),
        'success': False
    })

    assert result.risk_score >= 60, "Brute force should be detected"
    assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL], "Should be high/critical risk"
    print("✓ Brute force detection test passed")


def test_impossible_travel():
    """Test impossible travel detection"""
    guardian = LoginGuardian()

    # Login from San Francisco
    guardian.analyze_login({
        'username': 'traveler@example.com',
        'ip_address': '192.168.1.1',
        'timestamp': datetime.utcnow(),
        'success': True,
        'location': {
            'country': 'US',
            'city': 'San Francisco',
            'lat': 37.7749,
            'lon': -122.4194
        }
    })

    # Login from Tokyo 1 hour later (impossible)
    result = guardian.analyze_login({
        'username': 'traveler@example.com',
        'ip_address': '198.51.100.1',
        'timestamp': datetime.utcnow() + timedelta(hours=1),
        'success': True,
        'location': {
            'country': 'JP',
            'city': 'Tokyo',
            'lat': 35.6762,
            'lon': 139.6503
        }
    })

    assert result.risk_score >= 80, "Impossible travel should be flagged"
    assert any('impossible' in s.description.lower() for s in result.signals), "Should detect impossible travel"
    print("✓ Impossible travel detection test passed")


def test_account_enumeration():
    """Test account enumeration detection"""
    guardian = LoginGuardian()

    attacker_ip = '198.51.100.99'

    # Try many different usernames from same IP
    for i in range(12):
        guardian.analyze_login({
            'username': f'user{i}@example.com',
            'ip_address': attacker_ip,
            'timestamp': datetime.utcnow(),
            'success': False
        })

    result = guardian.analyze_login({
        'username': 'another@example.com',
        'ip_address': attacker_ip,
        'timestamp': datetime.utcnow(),
        'success': False
    })

    assert result.risk_score >= 60, "Account enumeration should be detected"
    print("✓ Account enumeration detection test passed")


def test_new_location():
    """Test new location detection"""
    guardian = LoginGuardian()

    # Establish normal pattern
    for _ in range(5):
        guardian.analyze_login({
            'username': 'user@example.com',
            'ip_address': '192.168.1.1',
            'timestamp': datetime.utcnow(),
            'success': True,
            'location': {
                'country': 'US',
                'city': 'New York',
                'lat': 40.7128,
                'lon': -74.0060
            }
        })

    # Login from new country
    result = guardian.analyze_login({
        'username': 'user@example.com',
        'ip_address': '198.51.100.1',
        'timestamp': datetime.utcnow(),
        'success': True,
        'location': {
            'country': 'FR',
            'city': 'Paris',
            'lat': 48.8566,
            'lon': 2.3522
        }
    })

    assert result.risk_score > 30, "New location should increase risk"
    print("✓ New location detection test passed")


def run_all_tests():
    """Run all tests"""
    print("Running Smart Login Guardian Tests\n")

    tests = [
        test_normal_login,
        test_brute_force_detection,
        test_impossible_travel,
        test_account_enumeration,
        test_new_location
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Tests failed: {failed}/{len(tests)}")
    print(f"{'=' * 50}")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
