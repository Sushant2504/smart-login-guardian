#!/usr/bin/env python3
"""
Smart Login Guardian - CLI Interface
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any

from guardian import LoginGuardian


def format_risk_assessment(assessment) -> str:
    """Format risk assessment for display"""
    output = []
    output.append("=" * 70)
    output.append("SMART LOGIN GUARDIAN - RISK ASSESSMENT")
    output.append("=" * 70)
    output.append(f"Username: {assessment.login_attempt.username}")
    output.append(f"IP Address: {assessment.login_attempt.ip_address}")
    output.append(f"Timestamp: {assessment.login_attempt.timestamp}")
    output.append(f"Status: {'SUCCESS' if assessment.login_attempt.success else 'FAILED'}")
    output.append("-" * 70)
    output.append(f"Risk Score: {assessment.risk_score}/100")
    output.append(f"Risk Level: {assessment.risk_level.value.upper()}")
    output.append(f"Recommendation: {assessment.recommendation}")
    output.append("-" * 70)

    if assessment.signals:
        output.append("RISK SIGNALS DETECTED:")
        for i, signal in enumerate(assessment.signals, 1):
            output.append(f"\n{i}. {signal.description}")
            output.append(f"   Type: {signal.signal_type.value}")
            output.append(f"   Severity: {signal.severity}/100 ({signal.severity_label})")
            if signal.details:
                output.append(f"   Details: {json.dumps(signal.details, indent=6)}")
    else:
        output.append("No risk signals detected - login appears safe")

    output.append("=" * 70)
    return "\n".join(output)


def analyze_command(args, guardian: LoginGuardian):
    """Handle the analyze command"""
    login_data = {
        'username': args.username,
        'ip_address': args.ip,
        'timestamp': args.timestamp or datetime.utcnow(),
        'success': args.success,
    }

    if args.user_agent:
        login_data['user_agent'] = args.user_agent

    if args.location:
        try:
            # Expected format: "country:city:lat:lon" e.g., "US:New York:40.7:-74.0"
            parts = args.location.split(':')
            login_data['location'] = {
                'country': parts[0],
                'city': parts[1] if len(parts) > 1 else None,
                'lat': float(parts[2]) if len(parts) > 2 else None,
                'lon': float(parts[3]) if len(parts) > 3 else None,
            }
        except (IndexError, ValueError):
            print("Error: Location format should be 'country:city:lat:lon'")
            sys.exit(1)

    if args.device:
        login_data['device_fingerprint'] = args.device

    assessment = guardian.analyze_login(login_data)

    if args.json:
        print(json.dumps(assessment.to_dict(), indent=2))
    else:
        print(format_risk_assessment(assessment))


def monitor_command(args, guardian: LoginGuardian):
    """Handle the monitor command"""
    try:
        with open(args.source, 'r') as f:
            events = json.load(f)

        if not isinstance(events, list):
            events = [events]

        high_risk_count = 0
        total_count = len(events)

        for event in events:
            assessment = guardian.analyze_login(event)

            if assessment.risk_score >= 60:
                high_risk_count += 1
                if not args.quiet:
                    print(format_risk_assessment(assessment))
                    print()

        print(f"\nSummary: Analyzed {total_count} events, {high_risk_count} high-risk detections")

    except FileNotFoundError:
        print(f"Error: File not found: {args.source}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {args.source}")
        sys.exit(1)


def stats_command(args, guardian: LoginGuardian):
    """Handle the stats command"""
    stats = guardian.get_statistics()

    print("=" * 70)
    print("SMART LOGIN GUARDIAN - STATISTICS")
    print("=" * 70)
    print(f"Total Login Attempts: {stats['total_login_attempts']}")
    print(f"Total Users: {stats['total_users']}")
    print(f"Total Unique IPs: {stats['total_unique_ips']}")
    print(f"Failed Attempts: {stats['failed_attempts']}")
    print(f"Success Rate: {stats['success_rate']:.2f}%")
    print("=" * 70)


def profile_command(args, guardian: LoginGuardian):
    """Handle the profile command"""
    profile = guardian.get_user_profile(args.username)

    if not profile:
        print(f"No profile found for user: {args.username}")
        return

    print("=" * 70)
    print(f"USER PROFILE: {args.username}")
    print("=" * 70)
    print(f"Total Logins: {profile.total_logins}")
    print(f"Failed Attempts: {profile.failed_attempts_count}")
    print(f"First Seen: {profile.first_seen}")
    print(f"Last Updated: {profile.last_updated}")
    print(f"\nUsual IPs ({len(profile.usual_ips)}): {', '.join(profile.usual_ips[:5])}")
    print(f"Usual Login Hours: {sorted(profile.usual_login_hours)}")

    if profile.usual_locations:
        print("\nUsual Locations:")
        for loc in profile.usual_locations[:5]:
            print(f"  - {loc.get('city')}, {loc.get('country')}")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Smart Login Guardian - Identify suspicious login attempts'
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a single login attempt')
    analyze_parser.add_argument('--username', required=True, help='Username attempting login')
    analyze_parser.add_argument('--ip', required=True, help='IP address')
    analyze_parser.add_argument('--timestamp', help='ISO timestamp (default: now)')
    analyze_parser.add_argument('--success', action='store_true', default=True, help='Login successful')
    analyze_parser.add_argument('--failed', action='store_false', dest='success', help='Login failed')
    analyze_parser.add_argument('--user-agent', help='User agent string')
    analyze_parser.add_argument('--location', help='Location (format: country:city:lat:lon)')
    analyze_parser.add_argument('--device', help='Device fingerprint')
    analyze_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor login events from file')
    monitor_parser.add_argument('--source', required=True, help='JSON file with login events')
    monitor_parser.add_argument('--quiet', action='store_true', help='Only show summary')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')

    # Profile command
    profile_parser = subparsers.add_parser('profile', help='Show user profile')
    profile_parser.add_argument('--username', required=True, help='Username to lookup')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    guardian = LoginGuardian()

    if args.command == 'analyze':
        analyze_command(args, guardian)
    elif args.command == 'monitor':
        monitor_command(args, guardian)
    elif args.command == 'stats':
        stats_command(args, guardian)
    elif args.command == 'profile':
        profile_command(args, guardian)


if __name__ == '__main__':
    main()
