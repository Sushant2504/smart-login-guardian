#!/usr/bin/env python3
"""
Smart Login Guardian - Web Server
Real-time 3D security dashboard with WebSocket support
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import sys
import os
from datetime import datetime
from threading import Lock

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardian import LoginGuardian, RiskLevel
from guardian.threat_intel import ThreatIntelligence
from guardian.analyzers.threat_intel_analyzer import ThreatIntelAnalyzer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'guardian-secret-key-change-in-production'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Guardian
guardian = LoginGuardian()
threat_intel = ThreatIntelligence()
threat_analyzer = ThreatIntelAnalyzer(threat_intel)
guardian.analyzers.append(threat_analyzer)

# Thread-safe storage for recent events
recent_events = []
events_lock = Lock()
MAX_RECENT_EVENTS = 100


@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('dashboard.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_login():
    """Analyze a login attempt via API"""
    data = request.json

    try:
        assessment = guardian.analyze_login(data)
        result = assessment.to_dict()

        # Add to recent events
        with events_lock:
            recent_events.append(result)
            if len(recent_events) > MAX_RECENT_EVENTS:
                recent_events.pop(0)

        # Broadcast to all connected clients
        socketio.emit('new_login', result, namespace='/')

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    stats = guardian.get_statistics()

    # Add risk distribution
    risk_distribution = {
        'safe': 0,
        'low': 0,
        'medium': 0,
        'high': 0,
        'critical': 0
    }

    with events_lock:
        for event in recent_events:
            risk_level = event.get('risk_level', 'safe')
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1

    stats['risk_distribution'] = risk_distribution
    stats['recent_event_count'] = len(recent_events)

    return jsonify(stats)


@app.route('/api/recent')
def get_recent():
    """Get recent login events"""
    with events_lock:
        return jsonify(recent_events[-50:])


@app.route('/api/threat-intel')
def get_threat_intel():
    """Get threat intelligence summary"""
    return jsonify({
        'malicious_ips_count': len(threat_intel.malicious_ips),
        'recent_reports_count': len(threat_intel.recent_reports),
        'reputation_db_size': len(threat_intel.ip_reputation),
        'recent_reports': [
            {'ip': ip, 'timestamp': ts.isoformat()}
            for ip, ts in list(threat_intel.recent_reports.items())[:10]
        ]
    })


@app.route('/api/simulate/<scenario>')
def simulate_scenario(scenario):
    """Simulate different attack scenarios for demo purposes"""
    scenarios = {
        'brute_force': simulate_brute_force,
        'credential_stuffing': simulate_credential_stuffing,
        'impossible_travel': simulate_impossible_travel,
        'apt': simulate_apt,
        'enumeration': simulate_enumeration
    }

    if scenario in scenarios:
        results = scenarios[scenario]()
        return jsonify({'message': f'Simulated {scenario}', 'events': len(results)})

    return jsonify({'error': 'Unknown scenario'}), 404


def simulate_brute_force():
    """Simulate brute force attack"""
    results = []
    for i in range(8):
        assessment = guardian.analyze_login({
            'username': 'admin@company.com',
            'ip_address': '203.0.113.50',
            'timestamp': datetime.utcnow().isoformat(),
            'success': False,
            'user_agent': 'curl/7.64.1'
        })
        results.append(assessment.to_dict())

        with events_lock:
            recent_events.append(assessment.to_dict())

        socketio.emit('new_login', assessment.to_dict(), namespace='/')

    return results


def simulate_credential_stuffing():
    """Simulate credential stuffing attack"""
    results = []
    ips = [f'198.51.100.{i}' for i in range(10, 20)]

    for ip in ips:
        assessment = guardian.analyze_login({
            'username': 'victim@company.com',
            'ip_address': ip,
            'timestamp': datetime.utcnow().isoformat(),
            'success': False,
            'user_agent': 'python-requests/2.28.0'
        })
        results.append(assessment.to_dict())

        with events_lock:
            recent_events.append(assessment.to_dict())

        socketio.emit('new_login', assessment.to_dict(), namespace='/')

    return results


def simulate_impossible_travel():
    """Simulate impossible travel"""
    # First login from New York
    assessment1 = guardian.analyze_login({
        'username': 'traveler@company.com',
        'ip_address': '192.168.1.100',
        'timestamp': datetime.utcnow().isoformat(),
        'success': True,
        'location': {'country': 'US', 'city': 'New York', 'lat': 40.7128, 'lon': -74.0060}
    })

    # Second login from Tokyo 1 hour later
    assessment2 = guardian.analyze_login({
        'username': 'traveler@company.com',
        'ip_address': '198.51.100.200',
        'timestamp': datetime.utcnow().isoformat(),
        'success': True,
        'location': {'country': 'JP', 'city': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503}
    })

    with events_lock:
        recent_events.extend([assessment1.to_dict(), assessment2.to_dict()])

    socketio.emit('new_login', assessment1.to_dict(), namespace='/')
    socketio.emit('new_login', assessment2.to_dict(), namespace='/')

    return [assessment1.to_dict(), assessment2.to_dict()]


def simulate_apt():
    """Simulate APT attack"""
    results = []
    for i in range(3):
        assessment = guardian.analyze_login({
            'username': 'ceo@company.com',
            'ip_address': '203.0.113.100',
            'timestamp': datetime.utcnow().isoformat(),
            'success': False,
            'location': {'country': 'CN', 'city': 'Beijing', 'lat': 39.9042, 'lon': 116.4074},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
        results.append(assessment.to_dict())

        with events_lock:
            recent_events.append(assessment.to_dict())

        socketio.emit('new_login', assessment.to_dict(), namespace='/')

    return results


def simulate_enumeration():
    """Simulate account enumeration"""
    results = []
    for i in range(15):
        assessment = guardian.analyze_login({
            'username': f'user{i}@company.com',
            'ip_address': '198.51.100.250',
            'timestamp': datetime.utcnow().isoformat(),
            'success': False,
            'user_agent': 'nikto/2.1.6'
        })
        results.append(assessment.to_dict())

        with events_lock:
            recent_events.append(assessment.to_dict())

        socketio.emit('new_login', assessment.to_dict(), namespace='/')

    return results


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'message': 'Connected to Guardian'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║         SMART LOGIN GUARDIAN - 3D WEB DASHBOARD                  ║
    ╚══════════════════════════════════════════════════════════════════╝

    🌐 Dashboard: http://localhost:5000
    📡 WebSocket: Enabled
    🔒 Guardian: Active

    Starting server...
    """)

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
