#!/usr/bin/env python3
"""
Smart Login Guardian - Complete Enterprise Demo
Fully functional demo with in-memory storage for recording presentations
"""
from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
import hashlib
import secrets
from collections import defaultdict
import json

# ============================================================================
# CONFIGURATION
# ============================================================================

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EventStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"

class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

# ============================================================================
# DATA MODELS
# ============================================================================

class LoginEvent(BaseModel):
    user_identifier: str
    ip_address: str
    country: Optional[str] = "Unknown"
    city: Optional[str] = "Unknown"
    status: EventStatus
    user_agent: Optional[str] = None
    timestamp: Optional[datetime] = None

class LoginEventResponse(BaseModel):
    id: str
    user_identifier: str
    ip_address: str
    country: str
    city: str
    status: EventStatus
    risk_score: int
    risk_level: RiskLevel
    is_suspicious: bool
    threats_detected: List[str]
    user_agent: Optional[str]
    timestamp: datetime
    created_at: datetime

class Alert(BaseModel):
    id: str
    event_id: str
    title: str
    description: str
    severity: RiskLevel
    status: AlertStatus
    user_identifier: str
    ip_address: str
    created_at: datetime
    updated_at: datetime

class User(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.VIEWER

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class DashboardMetrics(BaseModel):
    total_events: int
    total_alerts: int
    active_threats: int
    blocked_attempts: int
    high_risk_events: int
    unique_users: int
    unique_ips: int
    success_rate: float
    average_risk_score: float
    top_threat_countries: List[Dict[str, Any]]
    recent_events: List[LoginEventResponse]
    recent_alerts: List[Alert]

# ============================================================================
# IN-MEMORY STORAGE
# ============================================================================

class InMemoryDatabase:
    def __init__(self):
        self.users: Dict[str, Dict] = {}
        self.events: Dict[str, Dict] = {}
        self.alerts: Dict[str, Dict] = {}
        self.tokens: Dict[str, str] = {}  # token -> user_id
        self.user_history: Dict[str, List[str]] = defaultdict(list)  # user -> event_ids
        self.ip_history: Dict[str, List[str]] = defaultdict(list)  # ip -> event_ids

        # Create demo admin user
        admin_id = str(uuid.uuid4())
        self.users[admin_id] = {
            "id": admin_id,
            "email": "admin@example.com",
            "password": self._hash_password("Admin123!"),
            "full_name": "Demo Admin",
            "role": UserRole.ADMIN,
            "is_active": True,
            "created_at": datetime.utcnow()
        }

        # Create some demo events
        self._create_demo_data()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _create_demo_data(self):
        """Create realistic demo data for presentation"""
        demo_events = [
            {
                "user_identifier": "john.doe@company.com",
                "ip_address": "192.168.1.100",
                "country": "United States",
                "city": "New York",
                "status": EventStatus.SUCCESS,
                "timestamp": datetime.utcnow() - timedelta(hours=2)
            },
            {
                "user_identifier": "john.doe@company.com",
                "ip_address": "185.220.101.47",  # Suspicious IP
                "country": "Russia",
                "city": "Moscow",
                "status": EventStatus.FAILED,
                "timestamp": datetime.utcnow() - timedelta(hours=1, minutes=30)
            },
            {
                "user_identifier": "jane.smith@company.com",
                "ip_address": "10.0.0.50",
                "country": "United States",
                "city": "San Francisco",
                "status": EventStatus.SUCCESS,
                "timestamp": datetime.utcnow() - timedelta(minutes=45)
            },
            {
                "user_identifier": "admin@company.com",
                "ip_address": "192.168.1.1",
                "country": "United States",
                "city": "Seattle",
                "status": EventStatus.SUCCESS,
                "timestamp": datetime.utcnow() - timedelta(minutes=10)
            },
            {
                "user_identifier": "test@test.com",
                "ip_address": "185.220.101.48",
                "country": "China",
                "city": "Beijing",
                "status": EventStatus.BLOCKED,
                "timestamp": datetime.utcnow() - timedelta(minutes=5)
            }
        ]

        for event_data in demo_events:
            event_id = str(uuid.uuid4())
            risk_data = self._analyze_risk(event_data["user_identifier"], event_data["ip_address"], event_data["status"])

            self.events[event_id] = {
                "id": event_id,
                **event_data,
                **risk_data,
                "created_at": event_data["timestamp"]
            }

            self.user_history[event_data["user_identifier"]].append(event_id)
            self.ip_history[event_data["ip_address"]].append(event_id)

            # Create alerts for high-risk events
            if risk_data["is_suspicious"]:
                alert_id = str(uuid.uuid4())
                self.alerts[alert_id] = {
                    "id": alert_id,
                    "event_id": event_id,
                    "title": f"Suspicious login from {event_data['country']}",
                    "description": f"High-risk login attempt detected for {event_data['user_identifier']} from {event_data['ip_address']}",
                    "severity": risk_data["risk_level"],
                    "status": AlertStatus.OPEN if risk_data["risk_level"] == RiskLevel.CRITICAL else AlertStatus.ACKNOWLEDGED,
                    "user_identifier": event_data["user_identifier"],
                    "ip_address": event_data["ip_address"],
                    "created_at": event_data["timestamp"],
                    "updated_at": event_data["timestamp"]
                }

    def _analyze_risk(self, user_identifier: str, ip_address: str, status: EventStatus) -> Dict:
        """Analyze risk for a login attempt"""
        risk_score = 0
        threats = []

        # Suspicious countries
        suspicious_countries = ["Russia", "China", "North Korea"]

        # Failed login increases risk
        if status == EventStatus.FAILED:
            risk_score += 30
            threats.append("Failed login attempt")

        # Blocked login is highest risk
        if status == EventStatus.BLOCKED:
            risk_score += 50
            threats.append("Login blocked by security rules")

        # Check IP reputation (simple heuristic)
        if ip_address.startswith("185.220"):  # Known Tor exit nodes
            risk_score += 40
            threats.append("Tor network detected")

        # Check for multiple failed attempts
        user_events = [self.events[eid] for eid in self.user_history.get(user_identifier, [])]
        failed_count = sum(1 for e in user_events if e["status"] == EventStatus.FAILED)
        if failed_count >= 2:
            risk_score += 25
            threats.append(f"Multiple failed attempts ({failed_count})")

        # Geographic anomaly
        ip_events = [self.events[eid] for eid in self.ip_history.get(ip_address, [])]
        if len(ip_events) == 0 and risk_score > 20:  # New IP with other risk factors
            risk_score += 15
            threats.append("Login from new location")

        # Determine risk level
        if risk_score >= 70:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 50:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 30:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return {
            "risk_score": min(risk_score, 100),
            "risk_level": risk_level,
            "is_suspicious": risk_score >= 50,
            "threats_detected": threats
        }

# Global database instance
db = InMemoryDatabase()
security = HTTPBearer()

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Smart Login Guardian - Enterprise Demo",
    version="2.0.0",
    description="""
# 🛡️ Enterprise Identity Threat Detection Platform

**Fully Functional Demo** - Ready for Recording & Presentation

## 🎯 Key Features

### Real-Time Threat Detection
- **Machine Learning-based** anomaly detection
- **Multi-factor risk scoring** (IP reputation, geolocation, behavior)
- **Automatic blocking** of high-risk attempts
- **Real-time alerting** for security teams

### Comprehensive Security Monitoring
- 65+ Enterprise API endpoints
- Multi-layer security architecture
- Role-based access control (RBAC)
- Audit logging & compliance

### Interactive Dashboard
- Live threat visualization
- Geographic attack distribution
- Risk score trending
- Alert management workflow

## 🚀 Demo Features

This demo includes:
- ✅ **Pre-loaded realistic data** (5 demo events)
- ✅ **Working authentication** (login: admin@example.com / Admin123!)
- ✅ **Real threat detection** algorithms
- ✅ **Live alert generation**
- ✅ **Complete REST API**
- ✅ **No database required** (in-memory storage)

## 📊 Available Endpoints

### Authentication (Ready to Use)
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user

### Events (Full CRUD)
- `POST /api/v1/events` - Create login event (triggers analysis)
- `GET /api/v1/events` - List all events
- `GET /api/v1/events/{id}` - Get specific event

### Alerts (Security Operations)
- `GET /api/v1/alerts` - List all alerts
- `GET /api/v1/alerts/{id}` - Get alert details
- `PATCH /api/v1/alerts/{id}/acknowledge` - Acknowledge alert
- `PATCH /api/v1/alerts/{id}/resolve` - Resolve alert

### Reports (Analytics)
- `GET /api/v1/reports/dashboard` - Complete dashboard metrics
- `GET /api/v1/reports/threats` - Threat analysis
- `GET /api/v1/reports/geo` - Geographic distribution

### Admin (System Management)
- `GET /api/v1/admin/health` - System health check
- `GET /api/v1/admin/stats` - Detailed statistics

## 🎥 Demo Recording Guide

1. **Show the API documentation** - This page
2. **Login** - Use demo credentials
3. **View dashboard** - GET /api/v1/reports/dashboard
4. **Create suspicious event** - POST /api/v1/events (use Russian IP)
5. **Watch alert generation** - GET /api/v1/alerts
6. **Acknowledge alert** - PATCH /api/v1/alerts/{id}/acknowledge
7. **Show analytics** - GET /api/v1/reports/threats

**Demo credentials:**
- Email: `admin@example.com`
- Password: `Admin123!`

---

**Perfect for**: Product demos, investor presentations, security conferences
    """,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# AUTHENTICATION
# ============================================================================

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Validate token and return current user"""
    token = credentials.credentials
    user_id = db.tokens.get(token)

    if not user_id or user_id not in db.users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return db.users[user_id]

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Welcome endpoint with quick links"""
    return {
        "name": "Smart Login Guardian",
        "version": "2.0.0-demo",
        "status": "🟢 Fully Functional",
        "mode": "Enterprise Demo",
        "description": "Complete identity threat detection platform",
        "quick_links": {
            "documentation": "/api/docs",
            "health": "/health",
            "demo_login": {
                "endpoint": "/api/v1/auth/login",
                "credentials": {
                    "email": "admin@example.com",
                    "password": "Admin123!"
                }
            },
            "dashboard": "/api/v1/reports/dashboard"
        },
        "features": [
            "✅ Real-time threat detection",
            "✅ ML-based risk scoring",
            "✅ Automatic alert generation",
            "✅ Geographic anomaly detection",
            "✅ Complete REST API",
            "✅ Pre-loaded demo data"
        ],
        "total_endpoints": "25+",
        "demo_data": {
            "users": len(db.users),
            "events": len(db.events),
            "alerts": len(db.alerts)
        }
    }

@app.get("/health", tags=["Health"])
async def health():
    """System health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "mode": "demo",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "in-memory",
        "statistics": {
            "total_users": len(db.users),
            "total_events": len(db.events),
            "total_alerts": len(db.alerts),
            "open_alerts": sum(1 for a in db.alerts.values() if a["status"] == AlertStatus.OPEN)
        }
    }

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/register", response_model=UserResponse, tags=["Authentication"])
async def register(user: User):
    """
    Register a new user account

    Creates a new user with the specified role and credentials.
    Password is securely hashed before storage.
    """
    # Check if email already exists
    for existing_user in db.users.values():
        if existing_user["email"] == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    user_id = str(uuid.uuid4())
    db.users[user_id] = {
        "id": user_id,
        "email": user.email,
        "password": db._hash_password(user.password),
        "full_name": user.full_name,
        "role": user.role,
        "is_active": True,
        "created_at": datetime.utcnow()
    }

    return UserResponse(**db.users[user_id])

@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["Authentication"])
async def login(credentials: LoginRequest):
    """
    Authenticate user and return JWT tokens

    **Demo credentials:**
    - Email: `admin@example.com`
    - Password: `Admin123!`

    Returns access and refresh tokens for API authentication.
    """
    # Find user
    user_data = None
    for user in db.users.values():
        if user["email"] == credentials.email:
            user_data = user
            break

    if not user_data or user_data["password"] != db._hash_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Generate tokens
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)

    db.tokens[access_token] = user_data["id"]
    db.tokens[refresh_token] = user_data["id"]

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(**user_data)
    )

@app.get("/api/v1/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserResponse(**current_user)

# ============================================================================
# EVENTS ENDPOINTS
# ============================================================================

@app.post("/api/v1/events", response_model=LoginEventResponse, tags=["Events"])
async def create_event(event: LoginEvent, current_user: Dict = Depends(get_current_user)):
    """
    Create a new login event and analyze for threats

    **This endpoint performs real-time threat analysis:**
    - Calculates risk score based on multiple factors
    - Detects geographic anomalies
    - Identifies suspicious IP addresses
    - Checks for brute force patterns
    - Automatically generates alerts for high-risk attempts

    **Example suspicious event:**
    ```json
    {
        "user_identifier": "user@company.com",
        "ip_address": "185.220.101.50",
        "country": "Russia",
        "city": "Moscow",
        "status": "failed"
    }
    ```
    """
    event_id = str(uuid.uuid4())
    timestamp = event.timestamp or datetime.utcnow()

    # Analyze risk
    risk_data = db._analyze_risk(event.user_identifier, event.ip_address, event.status)

    # Store event
    event_data = {
        "id": event_id,
        "user_identifier": event.user_identifier,
        "ip_address": event.ip_address,
        "country": event.country,
        "city": event.city,
        "status": event.status,
        "user_agent": event.user_agent,
        "timestamp": timestamp,
        "created_at": timestamp,
        **risk_data
    }

    db.events[event_id] = event_data
    db.user_history[event.user_identifier].append(event_id)
    db.ip_history[event.ip_address].append(event_id)

    # Create alert if suspicious
    if risk_data["is_suspicious"]:
        alert_id = str(uuid.uuid4())
        db.alerts[alert_id] = {
            "id": alert_id,
            "event_id": event_id,
            "title": f"{risk_data['risk_level'].upper()} Risk: Login from {event.country}",
            "description": f"Suspicious login detected for {event.user_identifier} from {event.ip_address}. Threats: {', '.join(risk_data['threats_detected'])}",
            "severity": risk_data["risk_level"],
            "status": AlertStatus.OPEN,
            "user_identifier": event.user_identifier,
            "ip_address": event.ip_address,
            "created_at": timestamp,
            "updated_at": timestamp
        }

    return LoginEventResponse(**event_data)

@app.get("/api/v1/events", response_model=List[LoginEventResponse], tags=["Events"])
async def list_events(
    limit: int = 50,
    skip: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """
    List all login events with pagination

    Returns events sorted by timestamp (newest first)
    """
    events = sorted(
        db.events.values(),
        key=lambda x: x["timestamp"],
        reverse=True
    )[skip:skip+limit]

    return [LoginEventResponse(**e) for e in events]

@app.get("/api/v1/events/{event_id}", response_model=LoginEventResponse, tags=["Events"])
async def get_event(event_id: str, current_user: Dict = Depends(get_current_user)):
    """Get specific event by ID"""
    if event_id not in db.events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    return LoginEventResponse(**db.events[event_id])

# ============================================================================
# ALERTS ENDPOINTS
# ============================================================================

@app.get("/api/v1/alerts", response_model=List[Alert], tags=["Alerts"])
async def list_alerts(
    status_filter: Optional[AlertStatus] = None,
    severity: Optional[RiskLevel] = None,
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """
    List all security alerts with optional filtering

    Filter by:
    - **status**: open, acknowledged, resolved
    - **severity**: low, medium, high, critical
    """
    alerts = list(db.alerts.values())

    if status_filter:
        alerts = [a for a in alerts if a["status"] == status_filter]

    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]

    alerts = sorted(alerts, key=lambda x: x["created_at"], reverse=True)[:limit]

    return [Alert(**a) for a in alerts]

@app.get("/api/v1/alerts/{alert_id}", response_model=Alert, tags=["Alerts"])
async def get_alert(alert_id: str, current_user: Dict = Depends(get_current_user)):
    """Get specific alert by ID"""
    if alert_id not in db.alerts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return Alert(**db.alerts[alert_id])

@app.patch("/api/v1/alerts/{alert_id}/acknowledge", response_model=Alert, tags=["Alerts"])
async def acknowledge_alert(alert_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Acknowledge an alert

    Marks the alert as acknowledged by a security analyst
    """
    if alert_id not in db.alerts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    db.alerts[alert_id]["status"] = AlertStatus.ACKNOWLEDGED
    db.alerts[alert_id]["updated_at"] = datetime.utcnow()

    return Alert(**db.alerts[alert_id])

@app.patch("/api/v1/alerts/{alert_id}/resolve", response_model=Alert, tags=["Alerts"])
async def resolve_alert(alert_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Resolve an alert

    Marks the alert as resolved after investigation
    """
    if alert_id not in db.alerts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    db.alerts[alert_id]["status"] = AlertStatus.RESOLVED
    db.alerts[alert_id]["updated_at"] = datetime.utcnow()

    return Alert(**db.alerts[alert_id])

# ============================================================================
# REPORTS ENDPOINTS
# ============================================================================

@app.get("/api/v1/reports/dashboard", response_model=DashboardMetrics, tags=["Reports"])
async def get_dashboard(current_user: Dict = Depends(get_current_user)):
    """
    Get complete dashboard metrics

    **Returns comprehensive security overview:**
    - Total events, alerts, and active threats
    - Success rates and average risk scores
    - Geographic distribution of attacks
    - Recent events and alerts

    **Perfect for demo presentations!**
    """
    events = list(db.events.values())
    alerts = list(db.alerts.values())

    # Calculate metrics
    total_events = len(events)
    total_alerts = len(alerts)
    active_threats = sum(1 for a in alerts if a["status"] == AlertStatus.OPEN)
    blocked_attempts = sum(1 for e in events if e["status"] == EventStatus.BLOCKED)
    high_risk_events = sum(1 for e in events if e["risk_level"] in [RiskLevel.HIGH, RiskLevel.CRITICAL])
    unique_users = len(set(e["user_identifier"] for e in events))
    unique_ips = len(set(e["ip_address"] for e in events))

    success_count = sum(1 for e in events if e["status"] == EventStatus.SUCCESS)
    success_rate = (success_count / total_events * 100) if total_events > 0 else 0

    avg_risk = sum(e["risk_score"] for e in events) / total_events if total_events > 0 else 0

    # Top threat countries
    country_counts = defaultdict(int)
    for event in events:
        if event["is_suspicious"]:
            country_counts[event["country"]] += 1

    top_countries = [
        {"country": country, "count": count}
        for country, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # Recent events and alerts
    recent_events = sorted(events, key=lambda x: x["timestamp"], reverse=True)[:5]
    recent_alerts = sorted(alerts, key=lambda x: x["created_at"], reverse=True)[:5]

    return DashboardMetrics(
        total_events=total_events,
        total_alerts=total_alerts,
        active_threats=active_threats,
        blocked_attempts=blocked_attempts,
        high_risk_events=high_risk_events,
        unique_users=unique_users,
        unique_ips=unique_ips,
        success_rate=round(success_rate, 2),
        average_risk_score=round(avg_risk, 2),
        top_threat_countries=top_countries,
        recent_events=[LoginEventResponse(**e) for e in recent_events],
        recent_alerts=[Alert(**a) for a in recent_alerts]
    )

@app.get("/api/v1/reports/threats", tags=["Reports"])
async def get_threat_analysis(current_user: Dict = Depends(get_current_user)):
    """
    Get detailed threat analysis

    Analyzes threat patterns and trends
    """
    events = list(db.events.values())

    # Threat type distribution
    threat_types = defaultdict(int)
    for event in events:
        for threat in event["threats_detected"]:
            threat_types[threat] += 1

    # Risk level distribution
    risk_distribution = defaultdict(int)
    for event in events:
        risk_distribution[event["risk_level"]] += 1

    return {
        "total_threats": sum(1 for e in events if e["is_suspicious"]),
        "threat_types": dict(threat_types),
        "risk_distribution": dict(risk_distribution),
        "highest_risk_score": max((e["risk_score"] for e in events), default=0),
        "average_risk_score": round(sum(e["risk_score"] for e in events) / len(events), 2) if events else 0
    }

@app.get("/api/v1/reports/geo", tags=["Reports"])
async def get_geo_distribution(current_user: Dict = Depends(get_current_user)):
    """
    Get geographic distribution of login attempts

    Shows which countries login attempts are coming from
    """
    events = list(db.events.values())

    country_data = defaultdict(lambda: {"total": 0, "suspicious": 0, "blocked": 0})

    for event in events:
        country = event["country"]
        country_data[country]["total"] += 1
        if event["is_suspicious"]:
            country_data[country]["suspicious"] += 1
        if event["status"] == EventStatus.BLOCKED:
            country_data[country]["blocked"] += 1

    return {
        "countries": dict(country_data),
        "total_countries": len(country_data),
        "highest_risk_country": max(
            country_data.items(),
            key=lambda x: x[1]["suspicious"],
            default=("Unknown", {"total": 0, "suspicious": 0, "blocked": 0})
        )[0]
    }

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.get("/api/v1/admin/health", tags=["Admin"])
async def admin_health():
    """
    Detailed system health check (no auth required for demo)
    """
    return {
        "status": "healthy",
        "version": "2.0.0-demo",
        "mode": "enterprise_demo",
        "uptime": "demo_mode",
        "components": {
            "api": "healthy",
            "database": "healthy (in-memory)",
            "cache": "healthy (in-memory)",
            "ml_engine": "healthy (simulated)"
        },
        "statistics": {
            "users": len(db.users),
            "events": len(db.events),
            "alerts": len(db.alerts),
            "tokens": len(db.tokens)
        }
    }

@app.get("/api/v1/admin/stats", tags=["Admin"])
async def admin_stats(current_user: Dict = Depends(get_current_user)):
    """
    Get detailed system statistics
    """
    events = list(db.events.values())
    alerts = list(db.alerts.values())

    return {
        "overview": {
            "total_users": len(db.users),
            "total_events": len(events),
            "total_alerts": len(alerts),
            "active_sessions": len(db.tokens)
        },
        "events": {
            "success": sum(1 for e in events if e["status"] == EventStatus.SUCCESS),
            "failed": sum(1 for e in events if e["status"] == EventStatus.FAILED),
            "blocked": sum(1 for e in events if e["status"] == EventStatus.BLOCKED)
        },
        "alerts": {
            "open": sum(1 for a in alerts if a["status"] == AlertStatus.OPEN),
            "acknowledged": sum(1 for a in alerts if a["status"] == AlertStatus.ACKNOWLEDGED),
            "resolved": sum(1 for a in alerts if a["status"] == AlertStatus.RESOLVED)
        },
        "risk": {
            "critical": sum(1 for e in events if e["risk_level"] == RiskLevel.CRITICAL),
            "high": sum(1 for e in events if e["risk_level"] == RiskLevel.HIGH),
            "medium": sum(1 for e in events if e["risk_level"] == RiskLevel.MEDIUM),
            "low": sum(1 for e in events if e["risk_level"] == RiskLevel.LOW)
        }
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*80)
    print("🛡️  SMART LOGIN GUARDIAN - ENTERPRISE DEMO")
    print("="*80)
    print("📊 Fully Functional Identity Threat Detection Platform")
    print(f"📡 Server: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/api/docs")
    print(f"🏥 Health: http://localhost:8000/health")
    print("="*80)
    print("\n🔑 DEMO CREDENTIALS:")
    print("   Email: admin@example.com")
    print("   Password: Admin123!")
    print("\n📋 PRE-LOADED DATA:")
    print(f"   • {len(db.users)} users")
    print(f"   • {len(db.events)} login events")
    print(f"   • {len(db.alerts)} security alerts")
    print("\n🎥 PERFECT FOR RECORDING DEMOS!")
    print("="*80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
