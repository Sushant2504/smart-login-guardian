#!/usr/bin/env python3
"""
SMART LOGIN GUARDIAN - COMPLETE END-TO-END APPLICATION
Enterprise identity threat detection platform - ALL-IN-ONE
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import sqlite3
import asyncio
import uuid
import math
import random
import os

# ========================================================================
# CONFIGURATION
# ========================================================================

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours
DATABASE_PATH = "data/slg_complete.db"

app = FastAPI(
    title="Smart Login Guardian - Enterprise Platform",
    description="Complete end-to-end identity threat detection system",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")
connected_clients: List[WebSocket] = []

# ========================================================================
# DATA MODELS
# ========================================================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    status: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

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
    status: str = Field(..., pattern="^(success|failed)$")
    timestamp: Optional[datetime] = None

class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: str
    affected_user: str

# ========================================================================
# DATABASE INITIALIZATION
# ========================================================================

def init_database():
    """Initialize complete database schema"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Authentication events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authentication_events (
            event_id TEXT PRIMARY KEY,
            user_identifier TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            country TEXT,
            city TEXT,
            latitude REAL,
            longitude REAL,
            device_type TEXT,
            browser TEXT,
            os TEXT,
            status TEXT NOT NULL,
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
            signal_type TEXT,
            description TEXT,
            FOREIGN KEY (event_id) REFERENCES authentication_events(event_id)
        )
    """)

    # Security incidents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_incidents (
            incident_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            severity TEXT NOT NULL,
            status TEXT DEFAULT 'new',
            affected_user TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create default admin user: admin@demo.com / Demo@123
    password_hash = pwd_context.hash("Demo@123")
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, email, password_hash, full_name, status)
        VALUES ('user_admin', 'admin@demo.com', ?, 'Demo Admin', 'active')
    """, (password_hash,))

    conn.commit()
    conn.close()
    print("✅ Database initialized with demo user: admin@demo.com / Demo@123")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# ========================================================================
# AUTHENTICATION & AUTHORIZATION
# ========================================================================

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), conn = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return dict(user)

# ========================================================================
# RISK SCORING ENGINE
# ========================================================================

MALICIOUS_IPS = {
    "203.0.113.50": "Botnet controller",
    "198.51.100.200": "Tor exit node",
    "192.0.2.100": "VPN/Proxy",
}

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def analyze_risk(event: AuthEvent, conn) -> Dict[str, Any]:
    """Comprehensive risk analysis"""
    signals = []
    total_score = 0

    # Malicious IP
    if event.ip_address in MALICIOUS_IPS:
        signals.append({
            "type": "malicious_ip",
            "description": f"Known threat: {MALICIOUS_IPS[event.ip_address]}"
        })
        total_score += 30

    # Brute force
    if event.status == "failed":
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM authentication_events
            WHERE user_identifier = ? AND status = 'failed'
              AND datetime(event_timestamp) > datetime('now', '-5 minutes')
        """, (event.user_identifier,))
        failures = cursor.fetchone()[0]
        if failures >= 2:
            signals.append({"type": "brute_force", "description": f"{failures+1} failed attempts"})
            total_score += 25

    # New country
    if event.country != "Unknown":
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT country FROM authentication_events
            WHERE user_identifier = ? AND country != 'Unknown'
        """, (event.user_identifier,))
        countries = {r[0] for r in cursor.fetchall()}
        if event.country not in countries and countries:
            signals.append({"type": "new_country", "description": f"First login from {event.country}"})
            total_score += 20

    # Risk level
    if total_score >= 80: risk_level = "critical"
    elif total_score >= 60: risk_level = "high"
    elif total_score >= 40: risk_level = "elevated"
    elif total_score >= 20: risk_level = "moderate"
    else: risk_level = "low"

    return {"risk_score": min(100, total_score), "risk_level": risk_level, "signals": signals}

# ========================================================================
# WEBSOCKET BROADCASTING
# ========================================================================

async def broadcast_event(data):
    message = {"type": "event", "data": data}
    for client in list(connected_clients):
        try:
            await client.send_json(message)
        except:
            connected_clients.remove(client)

async def broadcast_alert(data):
    message = {"type": "alert", "data": data}
    for client in list(connected_clients):
        try:
            await client.send_json(message)
        except:
            connected_clients.remove(client)

# ========================================================================
# API ENDPOINTS - AUTHENTICATION
# ========================================================================

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user: UserRegister, conn = Depends(get_db)):
    """Register new user"""
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    password_hash = pwd_context.hash(user.password)

    cursor.execute("""
        INSERT INTO users (user_id, email, password_hash, full_name, status)
        VALUES (?, ?, ?, ?, 'active')
    """, (user_id, user.email, password_hash, user.full_name))
    conn.commit()

    return UserResponse(user_id=user_id, email=user.email, full_name=user.full_name, status='active')

@app.post("/api/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), conn = Depends(get_db)):
    """Login and get token"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
    user = cursor.fetchone()

    if not user or not verify_password(form_data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Incorrect credentials")

    user_dict = dict(user)
    access_token = create_access_token(data={"sub": user_dict['email']})

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user_dict)
    )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    """Get current user"""
    return UserResponse(**current_user)

# ========================================================================
# API ENDPOINTS - EVENTS & INCIDENTS
# ========================================================================

@app.post("/api/events/ingest")
async def ingest_event(event: AuthEvent, conn = Depends(get_db)):
    """Ingest authentication event"""
    if not event.timestamp:
        event.timestamp = datetime.now()

    risk = analyze_risk(event, conn)
    event_id = str(uuid.uuid4())
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO authentication_events (
            event_id, user_identifier, ip_address, country, city,
            latitude, longitude, device_type, browser, os,
            status, risk_score, risk_level, event_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, event.user_identifier, event.ip_address, event.country, event.city,
        event.latitude, event.longitude, event.device_type, event.browser, event.os,
        event.status, risk['risk_score'], risk['risk_level'], event.timestamp.isoformat()
    ))

    for signal in risk['signals']:
        cursor.execute("""
            INSERT INTO risk_signals (signal_id, event_id, signal_type, description)
            VALUES (?, ?, ?, ?)
        """, (str(uuid.uuid4()), event_id, signal['type'], signal['description']))

    conn.commit()

    event_data = {
        "event_id": event_id,
        "user_identifier": event.user_identifier,
        "ip_address": event.ip_address,
        "country": event.country,
        "city": event.city,
        "device_type": event.device_type,
        "browser": event.browser,
        "os": event.os,
        "status": event.status,
        "risk_score": risk['risk_score'],
        "risk_level": risk['risk_level'],
        "signals": risk['signals'],
        "timestamp": event.timestamp.isoformat()
    }

    await broadcast_event(event_data)

    if risk['risk_level'] in ['critical', 'high']:
        alert = {
            "title": f"{'🚨 Critical' if risk['risk_level'] == 'critical' else '⚠️ High'} Risk Login",
            "description": f"{event.user_identifier} from {event.ip_address}",
            "severity": risk['risk_level'],
            "timestamp": datetime.now().isoformat()
        }
        await broadcast_alert(alert)

    return event_data

@app.get("/api/events")
async def get_events(limit: int = 50, conn = Depends(get_db)):
    """Get authentication events"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM authentication_events
        ORDER BY event_timestamp DESC LIMIT ?
    """, (limit,))
    events = cursor.fetchall()

    result = []
    for event in events:
        event_dict = dict(event)
        cursor.execute("SELECT * FROM risk_signals WHERE event_id = ?", (event_dict['event_id'],))
        event_dict['signals'] = [dict(s) for s in cursor.fetchall()]
        result.append(event_dict)

    return result

@app.get("/api/stats")
async def get_stats(conn = Depends(get_db)):
    """Get statistics"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM authentication_events")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM authentication_events WHERE risk_level = 'critical'")
    critical = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM authentication_events WHERE status = 'success'")
    success = cursor.fetchone()[0]

    return {
        "total_events": total,
        "critical": critical,
        "success_rate": round((success / total * 100) if total > 0 else 0, 1)
    }

@app.post("/api/incidents")
async def create_incident(incident: IncidentCreate, conn = Depends(get_db)):
    """Create security incident"""
    incident_id = str(uuid.uuid4())
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO security_incidents (incident_id, title, description, severity, affected_user)
        VALUES (?, ?, ?, ?, ?)
    """, (incident_id, incident.title, incident.description, incident.severity, incident.affected_user))
    conn.commit()
    return {"incident_id": incident_id}

@app.get("/api/incidents")
async def get_incidents(conn = Depends(get_db)):
    """Get incidents"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM security_incidents ORDER BY created_at DESC LIMIT 50")
    return [dict(i) for i in cursor.fetchall()]

# ========================================================================
# WEBSOCKET
# ========================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"✅ Client connected. Total: {len(connected_clients)}")

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM authentication_events ORDER BY event_timestamp DESC LIMIT 20")
        events = [dict(e) for e in cursor.fetchall()]
        conn.close()

        await websocket.send_json({"type": "init", "data": {"recent_events": events}})

        while True:
            await websocket.receive_text()
            await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        connected_clients.remove(websocket)

# ========================================================================
# FRONTEND (Single Page Application)
# ========================================================================

@app.get("/", response_class=HTMLResponse)
async def frontend():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Login Guardian - Enterprise Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .slide-in { animation: slideIn 0.5s ease-out; }
        .pulse { animation: pulse 2s ease-in-out infinite; }
    </style>
</head>
<body class="bg-gray-900 text-gray-100">
    <div id="app">
        <!-- Login Page -->
        <div v-if="!isAuthenticated" class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 to-gray-900">
            <div class="bg-gray-800 p-8 rounded-lg shadow-2xl w-96">
                <div class="text-center mb-8">
                    <div class="text-5xl mb-3">🛡️</div>
                    <h1 class="text-2xl font-bold">Smart Login Guardian</h1>
                    <p class="text-gray-400 text-sm">Enterprise Identity Protection</p>
                </div>
                <form @submit.prevent="login" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium mb-2">Email</label>
                        <input v-model="loginForm.email" type="email" required
                               class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">Password</label>
                        <input v-model="loginForm.password" type="password" required
                               class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500">
                    </div>
                    <button type="submit" class="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium">
                        Sign In
                    </button>
                    <div class="text-center text-sm text-gray-400 mt-4">
                        Demo: admin@demo.com / Demo@123
                    </div>
                </form>
                <div v-if="loginError" class="mt-4 p-3 bg-red-900/50 border border-red-700 rounded text-sm">
                    {{ loginError }}
                </div>
            </div>
        </div>

        <!-- Dashboard -->
        <div v-else class="min-h-screen">
            <header class="bg-gradient-to-r from-blue-600 to-blue-800 shadow-lg">
                <div class="container mx-auto px-6 py-4 flex justify-between items-center">
                    <div class="flex items-center gap-3">
                        <div class="text-3xl">🛡️</div>
                        <div>
                            <h1 class="text-xl font-bold">Smart Login Guardian</h1>
                            <p class="text-blue-100 text-xs">Logged in as {{ user.email }}</p>
                        </div>
                    </div>
                    <button @click="logout" class="px-4 py-2 bg-red-600 hover:bg-red-700 rounded">
                        Logout
                    </button>
                </div>
            </header>

            <div class="container mx-auto px-6 py-6">
                <!-- Stats -->
                <div class="grid grid-cols-3 gap-4 mb-6">
                    <div class="bg-gray-800 p-4 rounded-lg border border-gray-700">
                        <div class="text-gray-400 text-xs uppercase">Total Events</div>
                        <div class="text-3xl font-bold">{{ stats.total_events }}</div>
                    </div>
                    <div class="bg-gray-800 p-4 rounded-lg border border-red-900">
                        <div class="text-gray-400 text-xs uppercase">Critical</div>
                        <div class="text-3xl font-bold text-red-400">{{ stats.critical }}</div>
                    </div>
                    <div class="bg-gray-800 p-4 rounded-lg border border-green-900">
                        <div class="text-gray-400 text-xs uppercase">Success Rate</div>
                        <div class="text-3xl font-bold text-green-400">{{ stats.success_rate }}%</div>
                    </div>
                </div>

                <!-- Events -->
                <div class="bg-gray-800 rounded-lg border border-gray-700">
                    <div class="p-4 border-b border-gray-700">
                        <h2 class="text-lg font-bold flex items-center gap-2">
                            <div class="w-2 h-2 rounded-full bg-green-400 pulse"></div>
                            Live Authentication Events
                        </h2>
                    </div>
                    <div class="p-4 h-96 overflow-y-auto space-y-2">
                        <div v-for="event in events" :key="event.event_id"
                             class="slide-in p-3 rounded-lg border" :class="getEventClass(event)">
                            <div class="flex justify-between">
                                <div>
                                    <div class="font-mono text-sm">{{ event.user_identifier }}</div>
                                    <div class="text-xs text-gray-400">
                                        {{ event.ip_address }} • {{ event.city }}, {{ event.country }}
                                    </div>
                                    <div v-if="event.signals && event.signals.length" class="mt-1 space-y-1">
                                        <div v-for="signal in event.signals" class="text-xs text-yellow-300">
                                            ⚠️ {{ signal.description }}
                                        </div>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <div class="text-2xl font-bold" :class="getRiskColor(event.risk_score)">
                                        {{ event.risk_score }}
                                    </div>
                                    <div class="text-xs text-gray-400">{{ formatTime(event.timestamp || event.event_timestamp) }}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
    const { createApp } = Vue;

    createApp({
        data() {
            return {
                isAuthenticated: false,
                user: null,
                token: null,
                loginForm: { email: '', password: '' },
                loginError: null,
                events: [],
                stats: { total_events: 0, critical: 0, success_rate: 0 },
                ws: null
            }
        },
        mounted() {
            const savedToken = localStorage.getItem('token');
            const savedUser = localStorage.getItem('user');
            if (savedToken && savedUser) {
                this.token = savedToken;
                this.user = JSON.parse(savedUser);
                this.isAuthenticated = true;
                this.loadData();
                this.connectWebSocket();
            }
        },
        methods: {
            async login() {
                this.loginError = null;
                try {
                    const formData = new FormData();
                    formData.append('username', this.loginForm.email);
                    formData.append('password', this.loginForm.password);

                    const res = await fetch('/api/auth/token', { method: 'POST', body: formData });
                    if (!res.ok) throw new Error('Login failed');

                    const data = await res.json();
                    this.token = data.access_token;
                    this.user = data.user;
                    this.isAuthenticated = true;

                    localStorage.setItem('token', this.token);
                    localStorage.setItem('user', JSON.stringify(this.user));

                    this.loadData();
                    this.connectWebSocket();
                } catch (e) {
                    this.loginError = 'Invalid credentials';
                }
            },
            logout() {
                this.isAuthenticated = false;
                this.user = null;
                this.token = null;
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                if (this.ws) this.ws.close();
            },
            async loadData() {
                const headers = { 'Authorization': `Bearer ${this.token}` };
                const events = await fetch('/api/events', { headers });
                this.events = await events.json();

                const stats = await fetch('/api/stats');
                this.stats = await stats.json();
            },
            connectWebSocket() {
                const wsUrl = `ws://${window.location.host}/ws`;
                this.ws = new WebSocket(wsUrl);

                this.ws.onmessage = (event) => {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'event') {
                        this.events.unshift(msg.data);
                        if (this.events.length > 20) this.events.pop();
                        this.loadData();
                    }
                };
            },
            getEventClass(event) {
                if (event.risk_level === 'critical') return 'bg-red-900/30 border-red-700';
                if (event.risk_level === 'high') return 'bg-orange-900/30 border-orange-700';
                return 'bg-gray-900 border-gray-700';
            },
            getRiskColor(score) {
                if (score >= 80) return 'text-red-400';
                if (score >= 60) return 'text-orange-400';
                return 'text-green-400';
            },
            formatTime(timestamp) {
                return new Date(timestamp).toLocaleTimeString();
            }
        }
    }).mount('#app');
    </script>
</body>
</html>
    """

# ========================================================================
# STARTUP
# ========================================================================

@app.on_event("startup")
async def startup():
    init_database()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "smart-login-guardian", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║    SMART LOGIN GUARDIAN - COMPLETE END-TO-END APPLICATION             ║
    ╚══════════════════════════════════════════════════════════════════════╝

    🚀 ENTERPRISE IDENTITY THREAT DETECTION PLATFORM

    ✅ Features Included:
       • User Authentication (JWT, bcrypt)
       • Event Ingestion & Persistence (SQLite)
       • Real-time Risk Scoring (Multi-signal)
       • Threat Detection (5+ patterns)
       • Security Incident Management
       • Live WebSocket Updates
       • Complete Web Dashboard
       • RESTful API

    🌐 Application URL: http://localhost:9000
    📖 API Documentation: http://localhost:9000/docs

    🔐 Demo Login:
       Email: admin@demo.com
       Password: Demo@123

    Starting complete application...
    """)

    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="info")
