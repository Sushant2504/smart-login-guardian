# Smart Login Guardian 🛡️

An enterprise-grade cybersecurity system that detects and prevents authentication-based attacks in real-time. Built for security teams, SOCs, and application developers who need comprehensive login monitoring and threat detection.

[![Tests](https://img.shields.io/badge/tests-5%2F5%20passing-brightgreen)]()
[![Security](https://img.shields.io/badge/security-enterprise%20grade-blue)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

An intelligent security system that identifies suspicious login attempts and provides detailed risk analysis.

## Features

- **Real-time Login Monitoring**: Track and analyze login attempts as they occur
- **Risk Scoring**: Multi-factor risk assessment based on various signals
- **Anomaly Detection**: Identify unusual patterns in login behavior
- **Detailed Explanations**: Clear descriptions of why each attempt is flagged as suspicious
- **Configurable Rules**: Customizable thresholds and detection rules

## Risk Signals Detected

- Multiple failed login attempts (brute force)
- Login from unusual geographic locations
- Login at unusual times
- Impossible travel (location changes too fast)
- New device/browser fingerprints
- Unusual IP addresses
- Account enumeration attempts
- Credential stuffing patterns
- Session hijacking indicators

## Installation

```bash
pip install -r requirements.txt
```

## 🚀 Production SaaS Platform

**Full-featured enterprise security platform with:**

✅ **User Authentication** - Registration, login, password hashing  
✅ **Database Backend** - PostgreSQL with migrations  
✅ **API Authentication** - JWT tokens + API keys  
✅ **Beautiful Landing Page** - Marketing website  
✅ **3D Dashboard** - Interactive threat visualization  
✅ **Admin Panel** - User & system management  
✅ **Docker Deployment** - One-command setup  
✅ **Security** - Rate limiting, CORS, input validation  
✅ **Monitoring** - Health checks, metrics, logging  

### Quick Start

```bash
# Deploy with Docker (Recommended)
./deploy.sh

# Or run manually
pip install -r requirements-prod.txt
python3 web/production_app.py
```

**Access:**
- Landing: http://localhost:5000
- Register: http://localhost:5000/register
- Dashboard: http://localhost:5000/dashboard (after login)
- API: http://localhost:5000/api/v1

See `DEPLOYMENT.md` for full production deployment guide.

## Usage

### CLI Interface

```bash
# Analyze a single login attempt
python guardian.py analyze --username "user@example.com" --ip "192.168.1.1"

# Monitor login stream from file
python guardian.py monitor --source login_events.json

# Start API server
python guardian.py serve --port 8000
```

### Python API

```python
from guardian import LoginGuardian

guardian = LoginGuardian()

# Analyze a login attempt
result = guardian.analyze_login({
    'username': 'user@example.com',
    'ip_address': '192.168.1.1',
    'timestamp': '2026-11-08T10:30:00Z',
    'user_agent': 'Mozilla/5.0...',
    'success': True
})

print(f"Risk Score: {result.risk_score}/100")
print(f"Risk Level: {result.risk_level}")
for signal in result.signals:
    print(f"- {signal.description}")
```

## Project Structure

```
smart-login-guardian/
├── guardian/
│   ├── __init__.py
│   ├── core.py              # Main LoginGuardian class
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── brute_force.py   # Brute force detection
│   │   ├── geo_anomaly.py   # Geographic anomaly detection
│   │   ├── time_anomaly.py  # Temporal pattern analysis
│   │   ├── device.py        # Device fingerprint analysis
│   │   └── velocity.py      # Impossible travel detection
│   ├── models.py            # Data models
│   └── storage.py           # Login history storage
├── tests/
├── examples/
├── guardian.py              # CLI entry point
└── requirements.txt
```
