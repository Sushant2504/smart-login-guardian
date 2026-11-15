#!/usr/bin/env python3
"""
Smart Login Guardian - Main Backend Service
Complete event ingestion, risk scoring, threat detection, and incident management
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import sqlite3
import asyncio
import uuid
import math
import random
import os

app = FastAPI(
    title="Smart Login Guardian - Backend",
    description="Complete authentication security monitoring backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_PATH = "data/slg_backend.db"
connected_clients: List[WebSocket] = []

# ==================================================================
# MODELS
# ==================================================================

class AuthEvent(BaseModel):
    user_identifier: EmailStr
    ip_address: str
    country: str = "Unknown"
    city: str = "Unknown"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_type: str = "desktop"
    browser: str = "Chrome"
    os: str = "Windows"
    authentication_method: str = "password"
    status: str = Field(..., pattern="^(success|failed)$")
    mfa_status: str = "not_required"
    timestamp: Optional[datetime] = None
    tenant_id: str = "tenant_default"

class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    affected_user: str
    source_ip: Optional[str] = None

class IncidentResponse(BaseModel):
    incident_id: str
    title: str
    description: str
    severity: str
    status: str
    affected_user: str
    source_ip: Optional[str]
    created_at: str
    updated_at: str

# ==================================================================
# DATABASE
# ==================================================================

def init_db():
    """Initialize SQLite database"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Authentication events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authentication_events (
            event_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            user_identifier TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            country TEXT,
            city TEXT,
            latitude REAL,
            longitude REAL,
            device_type TEXT,
            browser TEXT,
            os TEXT,
            authentication_method TEXT,
            status TEXT NOT NULL,
            mfa_status TEXT,
            risk_score INTEGER DEFAULT 0,
            risk_level TEXT,
            event_timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Risk signals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_signals (
            signal_id TEXT PRIMARY KEY,
            event_id TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            signal_value INTEGER NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES authentication_events(event_id)
        )
    """)

    # Security incidents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_incidents (
            incident_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            severity TEXT NOT NULL,
            status TEXT DEFAULT 'new',
            affected_user TEXT,
            source_ip TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Incident notes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_notes (
            note_id TEXT PRIMARY KEY,
            incident_id TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (incident_id) REFERENCES security_incidents(incident_id)
        )
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user ON authentication_events(user_identifier, event_timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_ip ON authentication_events(ip_address)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_risk ON authentication_events(risk_level, event_timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON security_incidents(status, created_at DESC)")

    conn.commit()
    conn.close()
    print("✅ Backend database initialized")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# ==================================================================
# RISK ANALYSIS
# ==================================================================

MALICIOUS_IPS = {
    "203.0.113.50": "Botnet controller",
    "198.51.100.200": "Tor exit node",
    "192.0.2.100": "VPN/Proxy service",
    "45.142.212.61": "APT infrastructure",
    "185.220.101.32": "Credential stuffing campaign"
}

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between coordinates in km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def analyze_risk(event: AuthEvent, conn) -> Dict[str, Any]:
    """Comprehensive risk analysis"""
    signals = []
    total_score = 0

    # 1. Malicious IP check
    if event.ip_address in MALICIOUS_IPS:
        signals.append({
            "type": "malicious_ip",
            "value": 30,
            "description": f"Known threat: {MALICIOUS_IPS[event.ip_address]}"
        })
        total_score += 30

    # 2. Brute force detection
    if event.status == "failed":
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM authentication_events
            WHERE user_identifier = ?
              AND status = 'failed'
              AND datetime(event_timestamp) > datetime('now', '-5 minutes')
        """, (event.user_identifier,))

        failure_count = cursor.fetchone()[0]

        if failure_count >= 2:
            signals.append({
                "type": "brute_force",
                "value": 25,
                "description": f"{failure_count + 1} failed attempts in 5 minutes"
            })
            total_score += 25

    # 3. New country detection
    if event.country and event.country != "Unknown":
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT country FROM authentication_events
            WHERE user_identifier = ?
              AND country IS NOT NULL
              AND country != 'Unknown'
        """, (event.user_identifier,))

        known_countries = {row[0] for row in cursor.fetchall()}

        if event.country not in known_countries and len(known_countries) > 0:
            signals.append({
                "type": "new_country",
                "value": 20,
                "description": f"First login from {event.country}"
            })
            total_score += 20

    # 4. Impossible travel
    if event.latitude and event.longitude:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT latitude, longitude, event_timestamp
            FROM authentication_events
            WHERE user_identifier = ?
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
            ORDER BY event_timestamp DESC
            LIMIT 1
        """, (event.user_identifier,))

        last_location = cursor.fetchone()

        if last_location:
            distance = calculate_distance(
                last_location[0], last_location[1],
                event.latitude, event.longitude
            )

            time_diff = (datetime.now() - datetime.fromisoformat(last_location[2])).seconds / 3600

            if time_diff > 0 and distance / time_diff > 800:
                signals.append({
                    "type": "impossible_travel",
                    "value": 35,
                    "description": f"{distance:.0f}km in {time_diff:.1f}h ({distance/time_diff:.0f}km/h)"
                })
                total_score += 35

    # 5. Unusual time
    hour = datetime.now().hour
    if hour < 6 or hour > 22:
        signals.append({
            "type": "unusual_time",
            "value": 10,
            "description": f"Login at {hour}:00 (unusual hour)"
        })
        total_score += 10

    # Classify risk level
    if total_score >= 80:
        risk_level = "critical"
    elif total_score >= 60:
        risk_level = "high"
    elif total_score >= 40:
        risk_level = "elevated"
    elif total_score >= 20:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return {
        "risk_score": min(100, total_score),
        "risk_level": risk_level,
        "signals": signals
    }

# ==================================================================
# WEBSOCKET
# ==================================================================

async def broadcast_event(event_data: Dict):
    """Broadcast event to all connected clients"""
    message = {"type": "event", "data": event_data}
    disconnected = []

    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.append(client)

    for client in disconnected:
        connected_clients.remove(client)

async def broadcast_alert(alert_data: Dict):
    """Broadcast security alert"""
    message = {"type": "alert", "data": alert_data}
    disconnected = []

    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.append(client)

    for client in disconnected:
        connected_clients.remove(client)

# ==================================================================
# API ENDPOINTS
# ==================================================================

@app.on_event("startup")
async def startup():
    init_db()
    print("✅ Backend service started")

@app.post("/api/v1/events/ingest")
async def ingest_event(event: AuthEvent, conn = Depends(get_db)):
    """Ingest authentication event"""
    if not event.timestamp:
        event.timestamp = datetime.now()

    # Analyze risk
    risk_analysis = analyze_risk(event, conn)

    # Store event
    event_id = str(uuid.uuid4())
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO authentication_events (
            event_id, tenant_id, user_identifier, ip_address,
            country, city, latitude, longitude,
            device_type, browser, os, authentication_method,
            status, mfa_status, risk_score, risk_level, event_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, event.tenant_id, event.user_identifier, event.ip_address,
        event.country, event.city, event.latitude, event.longitude,
        event.device_type, event.browser, event.os, event.authentication_method,
        event.status, event.mfa_status, risk_analysis['risk_score'],
        risk_analysis['risk_level'], event.timestamp.isoformat()
    ))

    # Store risk signals
    for signal in risk_analysis['signals']:
        signal_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO risk_signals (signal_id, event_id, signal_type, signal_value, description)
            VALUES (?, ?, ?, ?, ?)
        """, (signal_id, event_id, signal['type'], signal['value'], signal['description']))

    conn.commit()

    # Prepare response
    event_data = {
        "event_id": event_id,
        "user_identifier": event.user_identifier,
        "ip_address": event.ip_address,
        "country": event.country,
        "city": event.city,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "device_type": event.device_type,
        "browser": event.browser,
        "os": event.os,
        "status": event.status,
        "risk_score": risk_analysis['risk_score'],
        "risk_level": risk_analysis['risk_level'],
        "signals": risk_analysis['signals'],
        "timestamp": event.timestamp.isoformat()
    }

    # Broadcast to WebSocket clients
    await broadcast_event(event_data)

    # Auto-create incident if critical
    if risk_analysis['risk_level'] in ['critical', 'high']:
        incident_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO security_incidents (
                incident_id, tenant_id, title, description,
                severity, status, affected_user, source_ip
            ) VALUES (?, ?, ?, ?, ?, 'new', ?, ?)
        """, (
            incident_id,
            event.tenant_id,
            f"{'🚨 Critical' if risk_analysis['risk_level'] == 'critical' else '⚠️ High'} Risk Login Detected",
            f"User {event.user_identifier} logged in from {event.ip_address} with risk score {risk_analysis['risk_score']}/100",
            risk_analysis['risk_level'],
            event.user_identifier,
            event.ip_address
        ))
        conn.commit()

        alert_data = {
            "alert_id": str(uuid.uuid4()),
            "title": f"{'🚨 Critical' if risk_analysis['risk_level'] == 'critical' else '⚠️ High'} Risk Login",
            "description": f"{event.user_identifier} from {event.ip_address}",
            "severity": risk_analysis['risk_level'],
            "timestamp": datetime.now().isoformat()
        }
        await broadcast_alert(alert_data)

    return event_data

@app.get("/api/v1/events")
async def get_events(
    limit: int = 50,
    risk_level: Optional[str] = None,
    conn = Depends(get_db)
):
    """Get authentication events"""
    cursor = conn.cursor()

    query = "SELECT * FROM authentication_events"
    params = []

    if risk_level:
        query += " WHERE risk_level = ?"
        params.append(risk_level)

    query += " ORDER BY event_timestamp DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    events = cursor.fetchall()

    result = []
    for event in events:
        event_dict = dict(event)

        # Get signals
        cursor.execute(
            "SELECT signal_type, signal_value, description FROM risk_signals WHERE event_id = ?",
            (event_dict['event_id'],)
        )
        signals = [dict(s) for s in cursor.fetchall()]
        event_dict['signals'] = signals

        result.append(event_dict)

    return result

@app.get("/api/v1/stats")
async def get_stats(conn = Depends(get_db)):
    """Get dashboard statistics"""
    cursor = conn.cursor()

    # Total events
    cursor.execute("SELECT COUNT(*) FROM authentication_events")
    total_events = cursor.fetchone()[0]

    # Critical and high risk
    cursor.execute("SELECT COUNT(*) FROM authentication_events WHERE risk_level = 'critical'")
    critical = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM authentication_events WHERE risk_level = 'high'")
    high = cursor.fetchone()[0]

    # Success rate
    cursor.execute("SELECT COUNT(*) FROM authentication_events WHERE status = 'success'")
    successful = cursor.fetchone()[0]

    # Active incidents
    cursor.execute("SELECT COUNT(*) FROM security_incidents WHERE status IN ('new', 'investigating')")
    active_incidents = cursor.fetchone()[0]

    return {
        "total_events": total_events,
        "critical": critical,
        "high": high,
        "success_rate": round((successful / total_events * 100) if total_events > 0 else 0, 1),
        "active_incidents": active_incidents
    }

@app.post("/api/v1/incidents", response_model=IncidentResponse)
async def create_incident(incident: IncidentCreate, conn = Depends(get_db)):
    """Create security incident"""
    incident_id = str(uuid.uuid4())
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO security_incidents (
            incident_id, tenant_id, title, description,
            severity, status, affected_user, source_ip
        ) VALUES (?, 'tenant_default', ?, ?, ?, 'new', ?, ?)
    """, (
        incident_id, incident.title, incident.description,
        incident.severity, incident.affected_user, incident.source_ip
    ))

    conn.commit()

    cursor.execute("SELECT * FROM security_incidents WHERE incident_id = ?", (incident_id,))
    created = dict(cursor.fetchone())

    return IncidentResponse(**created)

@app.get("/api/v1/incidents", response_model=List[IncidentResponse])
async def get_incidents(status: Optional[str] = None, conn = Depends(get_db)):
    """Get security incidents"""
    cursor = conn.cursor()

    if status:
        cursor.execute(
            "SELECT * FROM security_incidents WHERE status = ? ORDER BY created_at DESC LIMIT 50",
            (status,)
        )
    else:
        cursor.execute("SELECT * FROM security_incidents ORDER BY created_at DESC LIMIT 50")

    incidents = cursor.fetchall()
    return [IncidentResponse(**dict(i)) for i in incidents]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"✅ Client connected. Total: {len(connected_clients)}")

    try:
        # Send initial data
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM authentication_events ORDER BY event_timestamp DESC LIMIT 20")
        events = [dict(e) for e in cursor.fetchall()]

        await websocket.send_json({"type": "init", "data": {"recent_events": events}})
        conn.close()

        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print(f"❌ Client disconnected. Total: {len(connected_clients)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "backend",
        "version": "1.0.0",
        "connected_clients": len(connected_clients)
    }

if __name__ == "__main__":
    import uvicorn
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║         SMART LOGIN GUARDIAN - MAIN BACKEND SERVICE              ║
    ╚══════════════════════════════════════════════════════════════════╝

    🚀 Backend Service Starting...

    Features:
    ✅ Event ingestion with validation
    ✅ Real-time risk scoring
    ✅ Threat detection (5+ patterns)
    ✅ Automatic incident creation
    ✅ WebSocket live updates
    ✅ SQLite persistence
    ✅ RESTful API

    API Docs: http://localhost:8002/docs

    Starting server...
    """)

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
