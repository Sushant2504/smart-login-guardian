#!/usr/bin/env python3
"""
Smart Login Guardian - LIVE Interactive Demo
Real-time authentication threat monitoring with live attacks
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import uvicorn
import random
import math
import json

app = FastAPI(
    title="Smart Login Guardian - Live Demo",
    description="Real-time Enterprise Identity Threat Detection",
    version="1.0.0-live"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# Data Models
# =====================================================

class AuthEvent(BaseModel):
    user_identifier: str
    ip_address: str
    country: str = "Unknown"
    city: str = "Unknown"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_type: str = "desktop"
    browser: str = "Chrome"
    os: str = "Windows"
    authentication_method: str = "password"
    status: str
    mfa_status: str = "not_required"
    timestamp: Optional[datetime] = None

class ThreatAlert(BaseModel):
    alert_id: str
    severity: str  # critical, high, medium, low
    title: str
    description: str
    affected_user: str
    source_ip: str
    timestamp: datetime
    action_taken: str

# =====================================================
# Global State
# =====================================================

events_store: List[Dict] = []
alerts_store: List[ThreatAlert] = []
active_attacks: Dict[str, Dict] = {}
connected_clients: List[WebSocket] = []
user_history: Dict[str, List[Dict]] = defaultdict(list)
ip_history: Dict[str, List[Dict]] = defaultdict(list)

# Realistic data
MALICIOUS_IPS = {
    "203.0.113.50": "Known botnet controller",
    "198.51.100.200": "Tor exit node",
    "192.0.2.100": "VPN/Proxy service",
    "45.142.212.61": "APT group infrastructure",
    "185.220.101.32": "Credential stuffing campaign",
}

USERS = [
    "alice@company.com", "bob@company.com", "charlie@company.com",
    "admin@company.com", "ceo@company.com", "it.admin@company.com",
    "security@company.com", "finance@company.com", "hr@company.com",
    "developer@company.com", "support@company.com", "sales@company.com"
]

LOCATIONS = [
    {"country": "India", "city": "Pune", "lat": 18.5204, "lon": 73.8567},
    {"country": "India", "city": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"country": "India", "city": "Bangalore", "lat": 12.9716, "lon": 77.5946},
    {"country": "USA", "city": "New York", "lat": 40.7128, "lon": -74.0060},
    {"country": "USA", "city": "San Francisco", "lat": 37.7749, "lon": -122.4194},
    {"country": "UK", "city": "London", "lat": 51.5074, "lon": -0.1278},
    {"country": "Germany", "city": "Berlin", "lat": 52.5200, "lon": 13.4050},
    {"country": "China", "city": "Beijing", "lat": 39.9042, "lon": 116.4074},
    {"country": "Russia", "city": "Moscow", "lat": 55.7558, "lon": 37.6173},
    {"country": "Brazil", "city": "São Paulo", "lat": -23.5505, "lon": -46.6333},
]

ATTACK_SCENARIOS = [
    "brute_force", "credential_stuffing", "account_takeover",
    "password_spraying", "impossible_travel", "unusual_location"
]

# =====================================================
# Risk Scoring
# =====================================================

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between coordinates in km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def analyze_risk(event: AuthEvent) -> Dict[str, Any]:
    """Real-time risk analysis"""
    signals = []
    total_score = 0

    # Malicious IP check
    if event.ip_address in MALICIOUS_IPS:
        signals.append({
            "type": "malicious_ip",
            "value": 30,
            "description": f"Known malicious: {MALICIOUS_IPS[event.ip_address]}"
        })
        total_score += 30

    # Brute force detection
    if event.status == "failed":
        recent_failures = [
            e for e in user_history[event.user_identifier]
            if e["status"] == "failed" and
            (datetime.now() - datetime.fromisoformat(e["timestamp"])).seconds < 300
        ]
        if len(recent_failures) >= 2:
            signals.append({
                "type": "brute_force",
                "value": 25,
                "description": f"{len(recent_failures) + 1} failed attempts in 5 min"
            })
            total_score += 25

    # New country
    user_countries = {e.get("country") for e in user_history[event.user_identifier]}
    if event.country not in user_countries and len(user_countries) > 0 and event.country != "Unknown":
        signals.append({
            "type": "new_country",
            "value": 20,
            "description": f"First login from {event.country}"
        })
        total_score += 20

    # Impossible travel
    if event.latitude and event.longitude and user_history[event.user_identifier]:
        last = user_history[event.user_identifier][-1]
        if last.get("latitude") and last.get("longitude"):
            distance = calculate_distance(
                last["latitude"], last["longitude"],
                event.latitude, event.longitude
            )
            time_diff = (datetime.now() - datetime.fromisoformat(last["timestamp"])).seconds / 3600
            if time_diff > 0:
                speed = distance / time_diff
                if speed > 800:
                    signals.append({
                        "type": "impossible_travel",
                        "value": 35,
                        "description": f"{distance:.0f}km in {time_diff:.1f}h ({speed:.0f}km/h)"
                    })
                    total_score += 35

    # Unusual time
    hour = datetime.now().hour
    if hour < 6 or hour > 22:
        signals.append({
            "type": "unusual_time",
            "value": 10,
            "description": f"Login at {hour}:00 (unusual hour)"
        })
        total_score += 10

    # Multiple IPs same user
    user_ips = {e.get("ip_address") for e in user_history[event.user_identifier][-10:]}
    if len(user_ips) > 5:
        signals.append({
            "type": "multiple_ips",
            "value": 15,
            "description": f"{len(user_ips)} different IPs recently"
        })
        total_score += 15

    # Risk level
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

# =====================================================
# Live Event Generator
# =====================================================

async def generate_normal_traffic():
    """Generate realistic normal authentication traffic"""
    while True:
        try:
            # 70% success rate for normal traffic
            if random.random() < 0.7:
                user = random.choice(USERS[:6])  # Normal users
                location = random.choice(LOCATIONS[:3])  # Home locations
                status = "success"
            else:
                user = random.choice(USERS)
                location = random.choice(LOCATIONS[:5])
                status = "failed"

            event = AuthEvent(
                user_identifier=user,
                ip_address=f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                country=location["country"],
                city=location["city"],
                latitude=location["lat"],
                longitude=location["lon"],
                status=status,
                device_type=random.choice(["desktop", "mobile", "tablet"]),
                browser=random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
                os=random.choice(["Windows", "macOS", "Linux", "iOS", "Android"])
            )

            await process_event(event)
            await asyncio.sleep(random.uniform(2, 5))  # Event every 2-5 seconds

        except Exception as e:
            print(f"Error in normal traffic: {e}")
            await asyncio.sleep(1)

async def simulate_attack(attack_type: str):
    """Simulate real-time attacks"""
    try:
        if attack_type == "brute_force":
            target = "admin@company.com"
            malicious_ip = random.choice(list(MALICIOUS_IPS.keys()))

            for i in range(8):
                event = AuthEvent(
                    user_identifier=target,
                    ip_address=malicious_ip,
                    country="Unknown",
                    city="Unknown",
                    status="failed",
                    browser="curl",
                    os="Linux"
                )
                await process_event(event)
                await asyncio.sleep(0.5)

            # Create alert
            alert = ThreatAlert(
                alert_id=f"alert_{len(alerts_store) + 1}",
                severity="critical",
                title="🚨 Brute Force Attack Detected",
                description=f"8 failed login attempts on {target} from {malicious_ip}",
                affected_user=target,
                source_ip=malicious_ip,
                timestamp=datetime.now(),
                action_taken="Account temporarily locked"
            )
            await broadcast_alert(alert)

        elif attack_type == "impossible_travel":
            user = random.choice(USERS[:4])

            # Login from India
            loc1 = {"country": "India", "city": "Mumbai", "lat": 19.0760, "lon": 72.8777}
            event1 = AuthEvent(
                user_identifier=user,
                ip_address=f"203.0.{random.randint(100, 200)}.{random.randint(1, 254)}",
                country=loc1["country"],
                city=loc1["city"],
                latitude=loc1["lat"],
                longitude=loc1["lon"],
                status="success"
            )
            await process_event(event1)
            await asyncio.sleep(1)

            # Login from USA 2 minutes later
            loc2 = {"country": "USA", "city": "New York", "lat": 40.7128, "lon": -74.0060}
            event2 = AuthEvent(
                user_identifier=user,
                ip_address=f"198.51.{random.randint(100, 200)}.{random.randint(1, 254)}",
                country=loc2["country"],
                city=loc2["city"],
                latitude=loc2["lat"],
                longitude=loc2["lon"],
                status="success"
            )
            await process_event(event2)

            alert = ThreatAlert(
                alert_id=f"alert_{len(alerts_store) + 1}",
                severity="high",
                title="✈️ Impossible Travel Detected",
                description=f"{user} logged in from Mumbai and New York within minutes",
                affected_user=user,
                source_ip=event2.ip_address,
                timestamp=datetime.now(),
                action_taken="Require MFA re-authentication"
            )
            await broadcast_alert(alert)

        elif attack_type == "credential_stuffing":
            malicious_ip = random.choice(list(MALICIOUS_IPS.keys()))

            for i in range(5):
                user = random.choice(USERS)
                event = AuthEvent(
                    user_identifier=user,
                    ip_address=malicious_ip,
                    country="Russia",
                    city="Moscow",
                    status="failed",
                    browser="python-requests",
                    os="Linux"
                )
                await process_event(event)
                await asyncio.sleep(0.3)

            alert = ThreatAlert(
                alert_id=f"alert_{len(alerts_store) + 1}",
                severity="high",
                title="🎯 Credential Stuffing Detected",
                description=f"5 different accounts targeted from {malicious_ip}",
                affected_user="Multiple users",
                source_ip=malicious_ip,
                timestamp=datetime.now(),
                action_taken="IP blocked, users notified"
            )
            await broadcast_alert(alert)

    except Exception as e:
        print(f"Error in attack simulation: {e}")

async def random_attack_generator():
    """Randomly trigger attacks"""
    await asyncio.sleep(10)  # Wait 10s before first attack

    while True:
        try:
            await asyncio.sleep(random.uniform(15, 30))  # Attack every 15-30 seconds
            attack = random.choice(ATTACK_SCENARIOS[:3])  # Choose common attacks
            await simulate_attack(attack)
        except Exception as e:
            print(f"Error in attack generator: {e}")
            await asyncio.sleep(5)

# =====================================================
# Event Processing
# =====================================================

async def process_event(event: AuthEvent):
    """Process and broadcast event"""
    if not event.timestamp:
        event.timestamp = datetime.now()

    # Analyze risk
    assessment = analyze_risk(event)

    # Store event
    event_data = event.dict()
    event_data["timestamp"] = event.timestamp.isoformat()
    event_data["event_id"] = f"evt_{len(events_store) + 1}"
    event_data.update(assessment)

    events_store.append(event_data)
    user_history[event.user_identifier].append(event_data)
    ip_history[event.ip_address].append(event_data)

    # Broadcast to all connected clients
    await broadcast_event(event_data)

    return event_data

async def broadcast_event(event_data: Dict):
    """Send event to all WebSocket clients"""
    message = {"type": "event", "data": event_data}
    disconnected = []

    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.append(client)

    for client in disconnected:
        connected_clients.remove(client)

async def broadcast_alert(alert: ThreatAlert):
    """Broadcast security alert"""
    alerts_store.append(alert)
    message = {"type": "alert", "data": alert.dict(mode='json')}

    disconnected = []
    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.append(client)

    for client in disconnected:
        connected_clients.remove(client)

# =====================================================
# WebSocket Endpoint
# =====================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        # Send initial state
        await websocket.send_json({
            "type": "init",
            "data": {
                "recent_events": events_store[-20:],
                "recent_alerts": [a.dict(mode='json') for a in alerts_store[-10:]]
            }
        })

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Echo back or handle commands
            await websocket.send_json({"type": "pong", "data": "ok"})

    except WebSocketDisconnect:
        connected_clients.remove(websocket)

# =====================================================
# HTTP Endpoints
# =====================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Live interactive dashboard"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🛡️ Smart Login Guardian - LIVE SOC</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
        <style>
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .slide-in { animation: slideIn 0.5s ease-out; }
            .pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
            .critical-bg { background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); }
            .high-bg { background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%); }
            .elevated-bg { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }

            @keyframes blink {
                0%, 50%, 100% { opacity: 1; }
                25%, 75% { opacity: 0.3; }
            }
            .blink { animation: blink 1s ease-in-out infinite; }
        </style>
    </head>
    <body class="bg-gray-900 text-gray-100">
        <div id="app">
            <!-- Header -->
            <header class="bg-gradient-to-r from-blue-600 to-blue-800 shadow-2xl border-b border-blue-500">
                <div class="container mx-auto px-6 py-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-4">
                            <div class="text-4xl">🛡️</div>
                            <div>
                                <h1 class="text-2xl font-bold">Smart Login Guardian</h1>
                                <p class="text-blue-100 text-sm">Live Security Operations Center</p>
                            </div>
                        </div>
                        <div class="flex items-center gap-6">
                            <div class="text-right">
                                <div class="flex items-center gap-2">
                                    <div class="w-3 h-3 rounded-full bg-green-400 pulse"></div>
                                    <span class="text-sm font-medium">LIVE</span>
                                </div>
                                <div class="text-xs text-blue-100">{{ stats.total_events }} events monitored</div>
                            </div>
                            <button @click="triggerAttack('brute_force')"
                                    class="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium">
                                🔥 Trigger Attack
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <!-- Alerts Banner -->
            <div v-if="recentAlerts.length > 0" class="bg-red-900 border-b border-red-700">
                <div class="container mx-auto px-6 py-3">
                    <div class="flex items-center gap-3">
                        <div class="text-2xl blink">🚨</div>
                        <div class="flex-1">
                            <div class="font-bold">{{ recentAlerts[0].title }}</div>
                            <div class="text-sm text-red-200">{{ recentAlerts[0].description }}</div>
                        </div>
                        <div class="text-xs text-red-300">{{ formatTime(recentAlerts[0].timestamp) }}</div>
                    </div>
                </div>
            </div>

            <div class="container mx-auto px-6 py-6">
                <!-- Stats Grid -->
                <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
                    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                        <div class="text-gray-400 text-xs uppercase">Total Events</div>
                        <div class="text-3xl font-bold text-white mt-1">{{ stats.total_events }}</div>
                        <div class="text-green-400 text-xs mt-1">↑ Real-time</div>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-4 border border-red-900">
                        <div class="text-gray-400 text-xs uppercase">Critical</div>
                        <div class="text-3xl font-bold text-red-400 mt-1">{{ stats.critical }}</div>
                        <div class="text-red-400 text-xs mt-1 blink" v-if="stats.critical > 0">⚠️ Active</div>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-4 border border-orange-900">
                        <div class="text-gray-400 text-xs uppercase">High Risk</div>
                        <div class="text-3xl font-bold text-orange-400 mt-1">{{ stats.high }}</div>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-4 border border-yellow-900">
                        <div class="text-gray-400 text-xs uppercase">Active Alerts</div>
                        <div class="text-3xl font-bold text-yellow-400 mt-1">{{ recentAlerts.length }}</div>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-4 border border-green-900">
                        <div class="text-gray-400 text-xs uppercase">Success Rate</div>
                        <div class="text-3xl font-bold text-green-400 mt-1">{{ stats.success_rate }}%</div>
                    </div>
                </div>

                <!-- Main Content Grid -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Live Event Stream (2/3 width) -->
                    <div class="lg:col-span-2 bg-gray-800 rounded-lg border border-gray-700">
                        <div class="p-4 border-b border-gray-700">
                            <div class="flex items-center justify-between">
                                <h2 class="text-lg font-bold flex items-center gap-2">
                                    <div class="w-2 h-2 rounded-full bg-green-400 pulse"></div>
                                    Live Authentication Stream
                                </h2>
                                <div class="text-sm text-gray-400">Auto-updating</div>
                            </div>
                        </div>
                        <div class="p-4 h-96 overflow-y-auto space-y-2">
                            <div v-for="event in liveEvents" :key="event.event_id"
                                 class="slide-in p-3 rounded-lg border"
                                 :class="getEventClass(event)">
                                <div class="flex items-start justify-between">
                                    <div class="flex-1">
                                        <div class="flex items-center gap-2 mb-1">
                                            <span class="font-mono text-sm">{{ event.user_identifier }}</span>
                                            <span :class="getStatusBadge(event.status)"
                                                  class="px-2 py-0.5 rounded text-xs font-medium">
                                                {{ event.status }}
                                            </span>
                                            <span v-if="event.risk_level !== 'low'"
                                                  :class="getRiskBadge(event.risk_level)"
                                                  class="px-2 py-0.5 rounded text-xs font-bold">
                                                {{ event.risk_level.toUpperCase() }}
                                            </span>
                                        </div>
                                        <div class="text-xs text-gray-400">
                                            {{ event.ip_address }} • {{ event.city }}, {{ event.country }} •
                                            {{ event.browser }} on {{ event.os }}
                                        </div>
                                        <div v-if="event.signals && event.signals.length > 0"
                                             class="mt-2 text-xs space-y-1">
                                            <div v-for="signal in event.signals" :key="signal.type"
                                                 class="text-yellow-300">
                                                ⚠️ {{ signal.description }}
                                            </div>
                                        </div>
                                    </div>
                                    <div class="text-right">
                                        <div class="text-2xl font-bold"
                                             :class="getRiskScoreColor(event.risk_score)">
                                            {{ event.risk_score }}
                                        </div>
                                        <div class="text-xs text-gray-400">{{ formatTime(event.timestamp) }}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Alerts Panel (1/3 width) -->
                    <div class="bg-gray-800 rounded-lg border border-gray-700">
                        <div class="p-4 border-b border-gray-700">
                            <h2 class="text-lg font-bold flex items-center gap-2">
                                🚨 Security Alerts
                            </h2>
                        </div>
                        <div class="p-4 h-96 overflow-y-auto space-y-3">
                            <div v-for="alert in recentAlerts" :key="alert.alert_id"
                                 class="slide-in p-3 rounded-lg"
                                 :class="getAlertClass(alert.severity)">
                                <div class="font-bold text-sm mb-1">{{ alert.title }}</div>
                                <div class="text-xs mb-2 opacity-90">{{ alert.description }}</div>
                                <div class="text-xs opacity-75 border-t border-white/20 pt-2">
                                    <div>Action: {{ alert.action_taken }}</div>
                                    <div class="mt-1">{{ formatTime(alert.timestamp) }}</div>
                                </div>
                            </div>
                            <div v-if="recentAlerts.length === 0" class="text-center text-gray-500 py-8">
                                No active alerts
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="mt-6 bg-gray-800 rounded-lg border border-gray-700 p-4">
                    <h3 class="font-bold mb-3">🎯 Simulate Attack Scenarios</h3>
                    <div class="flex gap-2 flex-wrap">
                        <button @click="triggerAttack('brute_force')"
                                class="px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-sm font-medium">
                            🔨 Brute Force
                        </button>
                        <button @click="triggerAttack('impossible_travel')"
                                class="px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded text-sm font-medium">
                            ✈️ Impossible Travel
                        </button>
                        <button @click="triggerAttack('credential_stuffing')"
                                class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm font-medium">
                            🎯 Credential Stuffing
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <script>
        const { createApp } = Vue;

        createApp({
            data() {
                return {
                    ws: null,
                    connected: false,
                    stats: {
                        total_events: 0,
                        critical: 0,
                        high: 0,
                        success_rate: 0
                    },
                    liveEvents: [],
                    recentAlerts: []
                }
            },
            mounted() {
                this.connectWebSocket();
                this.playSound = this.debounce(() => {
                    // Optional: Add sound for critical alerts
                }, 1000);
            },
            methods: {
                connectWebSocket() {
                    const wsUrl = `ws://${window.location.host}/ws`;
                    this.ws = new WebSocket(wsUrl);

                    this.ws.onopen = () => {
                        this.connected = true;
                        console.log('Connected to live stream');
                    };

                    this.ws.onmessage = (event) => {
                        const message = JSON.parse(event.data);

                        if (message.type === 'init') {
                            this.liveEvents = message.data.recent_events.reverse();
                            this.recentAlerts = message.data.recent_alerts.reverse();
                            this.updateStats();
                        } else if (message.type === 'event') {
                            this.liveEvents.unshift(message.data);
                            if (this.liveEvents.length > 20) {
                                this.liveEvents.pop();
                            }
                            this.updateStats();
                        } else if (message.type === 'alert') {
                            this.recentAlerts.unshift(message.data);
                            if (this.recentAlerts.length > 10) {
                                this.recentAlerts.pop();
                            }
                        }
                    };

                    this.ws.onclose = () => {
                        this.connected = false;
                        console.log('Disconnected, reconnecting...');
                        setTimeout(() => this.connectWebSocket(), 2000);
                    };
                },
                updateStats() {
                    this.stats.total_events = this.liveEvents.length;
                    this.stats.critical = this.liveEvents.filter(e => e.risk_level === 'critical').length;
                    this.stats.high = this.liveEvents.filter(e => e.risk_level === 'high').length;
                    const successful = this.liveEvents.filter(e => e.status === 'success').length;
                    this.stats.success_rate = this.liveEvents.length > 0
                        ? Math.round((successful / this.liveEvents.length) * 100)
                        : 0;
                },
                async triggerAttack(type) {
                    await fetch(`/api/attack/${type}`, { method: 'POST' });
                },
                getEventClass(event) {
                    const base = 'bg-gray-900 border-gray-700';
                    if (event.risk_level === 'critical') return 'bg-red-900/30 border-red-700';
                    if (event.risk_level === 'high') return 'bg-orange-900/30 border-orange-700';
                    if (event.risk_level === 'elevated') return 'bg-yellow-900/30 border-yellow-700';
                    return base;
                },
                getStatusBadge(status) {
                    return status === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white';
                },
                getRiskBadge(level) {
                    const badges = {
                        critical: 'bg-red-600 text-white blink',
                        high: 'bg-orange-600 text-white',
                        elevated: 'bg-yellow-600 text-white',
                        moderate: 'bg-blue-600 text-white'
                    };
                    return badges[level] || 'bg-gray-600 text-white';
                },
                getRiskScoreColor(score) {
                    if (score >= 80) return 'text-red-400';
                    if (score >= 60) return 'text-orange-400';
                    if (score >= 40) return 'text-yellow-400';
                    return 'text-green-400';
                },
                getAlertClass(severity) {
                    const classes = {
                        critical: 'critical-bg text-white',
                        high: 'high-bg text-white',
                        medium: 'elevated-bg text-white'
                    };
                    return classes[severity] || 'bg-gray-700 text-white';
                },
                formatTime(timestamp) {
                    return new Date(timestamp).toLocaleTimeString();
                },
                debounce(func, wait) {
                    let timeout;
                    return function(...args) {
                        clearTimeout(timeout);
                        timeout = setTimeout(() => func.apply(this, args), wait);
                    };
                }
            }
        }).mount('#app');
        </script>
    </body>
    </html>
    """

@app.post("/api/attack/{attack_type}")
async def trigger_attack(attack_type: str):
    """Manually trigger an attack scenario"""
    asyncio.create_task(simulate_attack(attack_type))
    return {"message": f"Triggering {attack_type} attack"}

@app.get("/api/stats")
async def get_stats():
    """Get current statistics"""
    total = len(events_store)
    critical = len([e for e in events_store if e.get("risk_level") == "critical"])
    high = len([e for e in events_store if e.get("risk_level") == "high"])
    successful = len([e for e in events_store if e.get("status") == "success"])

    return {
        "total_events": total,
        "critical": critical,
        "high": high,
        "success_rate": round((successful / total * 100) if total > 0 else 0, 1)
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Smart Login Guardian Live Demo",
        "version": "1.0.0-live",
        "connected_clients": len(connected_clients),
        "events_monitored": len(events_store)
    }

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(generate_normal_traffic())
    asyncio.create_task(random_attack_generator())
    print("✅ Background traffic generators started")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║    SMART LOGIN GUARDIAN - LIVE SOC DASHBOARD                     ║
    ╚══════════════════════════════════════════════════════════════════╝

    🌐 Live Dashboard: http://localhost:8080
    📡 WebSocket:      ws://localhost:8080/ws
    🔒 Status:         ACTIVE - Real-time monitoring

    Features:
    ✅ Auto-generating authentication traffic
    ✅ Random attack simulations every 15-30s
    ✅ Real-time threat detection
    ✅ Live WebSocket updates
    ✅ Security alerts with visual indicators

    Starting live demo server...
    """)

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
