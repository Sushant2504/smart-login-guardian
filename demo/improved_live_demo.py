#!/usr/bin/env python3
"""
Smart Login Guardian - IMPROVED LIVE Demo
Real-time authentication monitoring with working interactive buttons
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict
import asyncio
import uvicorn
import random
import math

app = FastAPI(title="Smart Login Guardian - Live SOC", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# Models & Storage
# =====================================================

class AuthEvent(BaseModel):
    user_identifier: str
    ip_address: str
    country: str = "Unknown"
    city: str = "Unknown"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    timestamp: Optional[datetime] = None

events_store: List[Dict] = []
alerts_store: List[Dict] = []
connected_clients: List[WebSocket] = []
user_history: Dict[str, List[Dict]] = defaultdict(list)

MALICIOUS_IPS = {
    "203.0.113.50": "Botnet controller",
    "198.51.100.200": "Tor exit node",
    "192.0.2.100": "VPN/Proxy",
}

USERS = ["alice@company.com", "bob@company.com", "admin@company.com", "ceo@company.com"]

LOCATIONS = [
    {"country": "India", "city": "Pune", "lat": 18.5204, "lon": 73.8567},
    {"country": "USA", "city": "New York", "lat": 40.7128, "lon": -74.0060},
    {"country": "UK", "city": "London", "lat": 51.5074, "lon": -0.1278},
]

# =====================================================
# Risk Analysis
# =====================================================

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def analyze_risk(event: AuthEvent) -> Dict[str, Any]:
    signals = []
    total_score = 0

    if event.ip_address in MALICIOUS_IPS:
        signals.append({
            "type": "malicious_ip",
            "description": f"Known malicious: {MALICIOUS_IPS[event.ip_address]}"
        })
        total_score += 30

    if event.status == "failed":
        recent_failures = [
            e for e in user_history[event.user_identifier]
            if e["status"] == "failed" and
            (datetime.now() - datetime.fromisoformat(e["timestamp"])).seconds < 300
        ]
        if len(recent_failures) >= 2:
            signals.append({
                "type": "brute_force",
                "description": f"{len(recent_failures) + 1} failed attempts"
            })
            total_score += 25

    user_countries = {e.get("country") for e in user_history[event.user_identifier]}
    if event.country not in user_countries and len(user_countries) > 0:
        signals.append({
            "type": "new_country",
            "description": f"First login from {event.country}"
        })
        total_score += 20

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

    return {"risk_score": min(100, total_score), "risk_level": risk_level, "signals": signals}

# =====================================================
# Traffic Generation
# =====================================================

async def generate_normal_traffic():
    await asyncio.sleep(2)
    while True:
        try:
            user = random.choice(USERS[:2])
            location = random.choice(LOCATIONS[:2])
            status = "success" if random.random() < 0.8 else "failed"

            event = AuthEvent(
                user_identifier=user,
                ip_address=f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                country=location["country"],
                city=location["city"],
                latitude=location["lat"],
                longitude=location["lon"],
                status=status
            )

            await process_event(event)
            await asyncio.sleep(random.uniform(3, 6))
        except:
            await asyncio.sleep(1)

async def simulate_attack(attack_type: str):
    print(f"🚨 Triggering {attack_type} attack!")
    try:
        if attack_type == "brute_force":
            target = "admin@company.com"
            malicious_ip = list(MALICIOUS_IPS.keys())[0]

            for i in range(6):
                event = AuthEvent(
                    user_identifier=target,
                    ip_address=malicious_ip,
                    country="Unknown",
                    city="Unknown",
                    status="failed"
                )
                await process_event(event)
                await asyncio.sleep(0.4)

            alert = {
                "alert_id": f"alert_{len(alerts_store) + 1}",
                "severity": "critical",
                "title": "🚨 Brute Force Attack Detected",
                "description": f"6 failed attempts on {target} from {malicious_ip}",
                "timestamp": datetime.now().isoformat()
            }
            await broadcast_alert(alert)

        elif attack_type == "impossible_travel":
            user = random.choice(USERS[:2])

            event1 = AuthEvent(
                user_identifier=user,
                ip_address=f"203.0.{random.randint(100, 200)}.10",
                country="India",
                city="Mumbai",
                latitude=19.0760,
                longitude=72.8777,
                status="success"
            )
            await process_event(event1)
            await asyncio.sleep(1)

            event2 = AuthEvent(
                user_identifier=user,
                ip_address=f"198.51.{random.randint(100, 200)}.25",
                country="USA",
                city="New York",
                latitude=40.7128,
                longitude=-74.0060,
                status="success"
            )
            await process_event(event2)

            alert = {
                "alert_id": f"alert_{len(alerts_store) + 1}",
                "severity": "high",
                "title": "✈️ Impossible Travel Detected",
                "description": f"{user} logged in from India and USA within seconds",
                "timestamp": datetime.now().isoformat()
            }
            await broadcast_alert(alert)

        elif attack_type == "credential_stuffing":
            malicious_ip = list(MALICIOUS_IPS.keys())[1]

            for user in USERS[:4]:
                event = AuthEvent(
                    user_identifier=user,
                    ip_address=malicious_ip,
                    country="Russia",
                    city="Moscow",
                    status="failed"
                )
                await process_event(event)
                await asyncio.sleep(0.3)

            alert = {
                "alert_id": f"alert_{len(alerts_store) + 1}",
                "severity": "high",
                "title": "🎯 Credential Stuffing Detected",
                "description": f"4 accounts targeted from {malicious_ip}",
                "timestamp": datetime.now().isoformat()
            }
            await broadcast_alert(alert)

        print(f"✅ {attack_type} attack completed!")

    except Exception as e:
        print(f"❌ Error in attack simulation: {e}")

async def random_attack_generator():
    await asyncio.sleep(20)
    while True:
        try:
            await asyncio.sleep(random.uniform(25, 40))
            attack = random.choice(["brute_force", "impossible_travel", "credential_stuffing"])
            await simulate_attack(attack)
        except:
            await asyncio.sleep(5)

# =====================================================
# Event Processing
# =====================================================

async def process_event(event: AuthEvent):
    if not event.timestamp:
        event.timestamp = datetime.now()

    assessment = analyze_risk(event)

    event_data = event.dict()
    event_data["timestamp"] = event.timestamp.isoformat()
    event_data["event_id"] = f"evt_{len(events_store) + 1}"
    event_data.update(assessment)

    events_store.append(event_data)
    user_history[event.user_identifier].append(event_data)

    await broadcast_event(event_data)
    return event_data

async def broadcast_event(event_data: Dict):
    message = {"type": "event", "data": event_data}
    disconnected = []
    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.append(client)
    for client in disconnected:
        connected_clients.remove(client)

async def broadcast_alert(alert: Dict):
    alerts_store.append(alert)
    message = {"type": "alert", "data": alert}
    disconnected = []
    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.append(client)
    for client in disconnected:
        connected_clients.remove(client)

# =====================================================
# WebSocket
# =====================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"✅ Client connected. Total: {len(connected_clients)}")

    try:
        await websocket.send_json({
            "type": "init",
            "data": {
                "recent_events": events_store[-20:],
                "recent_alerts": alerts_store[-10:]
            }
        })

        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print(f"❌ Client disconnected. Total: {len(connected_clients)}")

# =====================================================
# HTTP Endpoints
# =====================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
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
            @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            @keyframes blink { 0%, 50%, 100% { opacity: 1; } 25%, 75% { opacity: 0.3; } }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

            .slide-in { animation: slideIn 0.5s ease-out; }
            .pulse { animation: pulse 2s ease-in-out infinite; }
            .blink { animation: blink 1s ease-in-out infinite; }
            .fade-in { animation: fadeIn 0.3s ease-out; }

            .toast {
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 1000;
                max-width: 400px;
            }
        </style>
    </head>
    <body class="bg-gray-900 text-gray-100">
        <div id="app">
            <!-- Toast Notifications -->
            <div class="toast">
                <div v-for="toast in toasts" :key="toast.id"
                     class="mb-3 p-4 rounded-lg shadow-2xl fade-in"
                     :class="getToastClass(toast.type)">
                    <div class="flex items-start gap-3">
                        <div class="text-2xl">{{ toast.icon }}</div>
                        <div class="flex-1">
                            <div class="font-bold">{{ toast.title }}</div>
                            <div class="text-sm opacity-90">{{ toast.message }}</div>
                        </div>
                    </div>
                </div>
            </div>

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
                                    <span class="text-sm font-medium">{{ connected ? 'LIVE' : 'CONNECTING...' }}</span>
                                </div>
                                <div class="text-xs text-blue-100">{{ stats.total_events }} events</div>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <!-- Alert Banner -->
            <div v-if="recentAlerts.length > 0" class="bg-red-900 border-b border-red-700">
                <div class="container mx-auto px-6 py-3">
                    <div class="flex items-center gap-3">
                        <div class="text-2xl blink">🚨</div>
                        <div class="flex-1">
                            <div class="font-bold">{{ recentAlerts[0].title }}</div>
                            <div class="text-sm text-red-200">{{ recentAlerts[0].description }}</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="container mx-auto px-6 py-6">
                <!-- Stats -->
                <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
                    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                        <div class="text-gray-400 text-xs uppercase">Events</div>
                        <div class="text-3xl font-bold">{{ stats.total_events }}</div>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-4 border border-red-900">
                        <div class="text-gray-400 text-xs uppercase">Critical</div>
                        <div class="text-3xl font-bold text-red-400">{{ stats.critical }}</div>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-4 border border-orange-900">
                        <div class="text-gray-400 text-xs uppercase">High Risk</div>
                        <div class="text-3xl font-bold text-orange-400">{{ stats.high }}</div>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-4 border border-yellow-900">
                        <div class="text-gray-400 text-xs uppercase">Alerts</div>
                        <div class="text-3xl font-bold text-yellow-400">{{ recentAlerts.length }}</div>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-4 border border-green-900">
                        <div class="text-gray-400 text-xs uppercase">Success Rate</div>
                        <div class="text-3xl font-bold text-green-400">{{ stats.success_rate }}%</div>
                    </div>
                </div>

                <!-- Attack Buttons -->
                <div class="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
                    <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                        🎯 Trigger Attack Scenarios
                        <span class="text-sm text-gray-400 font-normal">(Click buttons to see live attacks)</span>
                    </h3>
                    <div class="flex gap-3 flex-wrap">
                        <button @click="triggerAttack('brute_force')"
                                :disabled="attackInProgress"
                                class="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-all transform hover:scale-105">
                            <span v-if="!attackInProgress">🔨 Brute Force Attack</span>
                            <span v-else>⏳ Attacking...</span>
                        </button>
                        <button @click="triggerAttack('impossible_travel')"
                                :disabled="attackInProgress"
                                class="px-6 py-3 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-all transform hover:scale-105">
                            ✈️ Impossible Travel
                        </button>
                        <button @click="triggerAttack('credential_stuffing')"
                                :disabled="attackInProgress"
                                class="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-all transform hover:scale-105">
                            🎯 Credential Stuffing
                        </button>
                    </div>
                </div>

                <!-- Main Grid -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Events (2/3) -->
                    <div class="lg:col-span-2 bg-gray-800 rounded-lg border border-gray-700">
                        <div class="p-4 border-b border-gray-700">
                            <h2 class="text-lg font-bold flex items-center gap-2">
                                <div class="w-2 h-2 rounded-full bg-green-400 pulse"></div>
                                Live Event Stream
                            </h2>
                        </div>
                        <div class="p-4 h-96 overflow-y-auto space-y-2">
                            <div v-for="event in liveEvents" :key="event.event_id"
                                 class="slide-in p-3 rounded-lg border"
                                 :class="getEventClass(event)">
                                <div class="flex justify-between">
                                    <div>
                                        <div class="flex gap-2 mb-1">
                                            <span class="font-mono text-sm">{{ event.user_identifier }}</span>
                                            <span :class="event.status === 'success' ? 'bg-green-600' : 'bg-red-600'"
                                                  class="px-2 py-0.5 rounded text-xs">{{ event.status }}</span>
                                            <span v-if="event.risk_level !== 'low'"
                                                  :class="getRiskBadge(event.risk_level)"
                                                  class="px-2 py-0.5 rounded text-xs font-bold">
                                                {{ event.risk_level.toUpperCase() }}
                                            </span>
                                        </div>
                                        <div class="text-xs text-gray-400">
                                            {{ event.ip_address }} • {{ event.city }}, {{ event.country }}
                                        </div>
                                        <div v-if="event.signals && event.signals.length > 0" class="mt-2 space-y-1">
                                            <div v-for="signal in event.signals" class="text-xs text-yellow-300">
                                                ⚠️ {{ signal.description }}
                                            </div>
                                        </div>
                                    </div>
                                    <div class="text-right">
                                        <div class="text-2xl font-bold" :class="getRiskScoreColor(event.risk_score)">
                                            {{ event.risk_score }}
                                        </div>
                                        <div class="text-xs text-gray-400">{{ formatTime(event.timestamp) }}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Alerts (1/3) -->
                    <div class="bg-gray-800 rounded-lg border border-gray-700">
                        <div class="p-4 border-b border-gray-700">
                            <h2 class="text-lg font-bold">🚨 Security Alerts</h2>
                        </div>
                        <div class="p-4 h-96 overflow-y-auto space-y-3">
                            <div v-for="alert in recentAlerts" :key="alert.alert_id"
                                 class="slide-in p-3 rounded-lg"
                                 :class="getAlertClass(alert.severity)">
                                <div class="font-bold text-sm mb-1">{{ alert.title }}</div>
                                <div class="text-xs opacity-90">{{ alert.description }}</div>
                                <div class="text-xs opacity-75 mt-2">{{ formatTime(alert.timestamp) }}</div>
                            </div>
                            <div v-if="recentAlerts.length === 0" class="text-center text-gray-500 py-8">
                                No alerts yet - Click attack buttons above!
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
                    ws: null,
                    connected: false,
                    stats: { total_events: 0, critical: 0, high: 0, success_rate: 0 },
                    liveEvents: [],
                    recentAlerts: [],
                    toasts: [],
                    attackInProgress: false
                }
            },
            mounted() {
                this.connectWebSocket();
            },
            methods: {
                connectWebSocket() {
                    const wsUrl = `ws://${window.location.host}/ws`;
                    this.ws = new WebSocket(wsUrl);

                    this.ws.onopen = () => {
                        this.connected = true;
                        console.log('✅ Connected to live stream');
                        this.showToast('success', 'Connected', 'Live monitoring active');
                    };

                    this.ws.onmessage = (event) => {
                        const message = JSON.parse(event.data);

                        if (message.type === 'init') {
                            this.liveEvents = message.data.recent_events.reverse();
                            this.recentAlerts = message.data.recent_alerts.reverse();
                            this.updateStats();
                        } else if (message.type === 'event') {
                            this.liveEvents.unshift(message.data);
                            if (this.liveEvents.length > 20) this.liveEvents.pop();
                            this.updateStats();
                        } else if (message.type === 'alert') {
                            this.recentAlerts.unshift(message.data);
                            if (this.recentAlerts.length > 10) this.recentAlerts.pop();
                            this.showToast('error', 'Security Alert!', message.data.title);
                        }
                    };

                    this.ws.onclose = () => {
                        this.connected = false;
                        setTimeout(() => this.connectWebSocket(), 2000);
                    };
                },
                updateStats() {
                    this.stats.total_events = this.liveEvents.length;
                    this.stats.critical = this.liveEvents.filter(e => e.risk_level === 'critical').length;
                    this.stats.high = this.liveEvents.filter(e => e.risk_level === 'high').length;
                    const successful = this.liveEvents.filter(e => e.status === 'success').length;
                    this.stats.success_rate = this.liveEvents.length > 0
                        ? Math.round((successful / this.liveEvents.length) * 100) : 0;
                },
                async triggerAttack(type) {
                    this.attackInProgress = true;
                    console.log(`🚨 Triggering ${type} attack...`);

                    this.showToast('warning', 'Attack Triggered!', `Starting ${type} attack...`);

                    try {
                        const response = await fetch(`/api/attack/${type}`, { method: 'POST' });
                        const result = await response.json();
                        console.log('✅ Attack response:', result);

                        setTimeout(() => {
                            this.attackInProgress = false;
                            this.showToast('info', 'Attack Complete', result.message);
                        }, 3000);
                    } catch (error) {
                        console.error('❌ Attack failed:', error);
                        this.attackInProgress = false;
                        this.showToast('error', 'Error', 'Failed to trigger attack');
                    }
                },
                showToast(type, title, message) {
                    const icons = {
                        success: '✅',
                        error: '🚨',
                        warning: '⚠️',
                        info: 'ℹ️'
                    };

                    const toast = {
                        id: Date.now(),
                        type,
                        icon: icons[type],
                        title,
                        message
                    };

                    this.toasts.push(toast);

                    setTimeout(() => {
                        const index = this.toasts.findIndex(t => t.id === toast.id);
                        if (index > -1) this.toasts.splice(index, 1);
                    }, 4000);
                },
                getToastClass(type) {
                    const classes = {
                        success: 'bg-green-600 text-white',
                        error: 'bg-red-600 text-white',
                        warning: 'bg-orange-600 text-white',
                        info: 'bg-blue-600 text-white'
                    };
                    return classes[type] || 'bg-gray-600 text-white';
                },
                getEventClass(event) {
                    if (event.risk_level === 'critical') return 'bg-red-900/30 border-red-700';
                    if (event.risk_level === 'high') return 'bg-orange-900/30 border-orange-700';
                    if (event.risk_level === 'elevated') return 'bg-yellow-900/30 border-yellow-700';
                    return 'bg-gray-900 border-gray-700';
                },
                getRiskBadge(level) {
                    const badges = {
                        critical: 'bg-red-600 blink',
                        high: 'bg-orange-600',
                        elevated: 'bg-yellow-600',
                        moderate: 'bg-blue-600'
                    };
                    return badges[level] || 'bg-gray-600';
                },
                getRiskScoreColor(score) {
                    if (score >= 80) return 'text-red-400';
                    if (score >= 60) return 'text-orange-400';
                    if (score >= 40) return 'text-yellow-400';
                    return 'text-green-400';
                },
                getAlertClass(severity) {
                    if (severity === 'critical') return 'bg-red-600 text-white';
                    if (severity === 'high') return 'bg-orange-600 text-white';
                    return 'bg-yellow-600 text-white';
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

@app.post("/api/attack/{attack_type}")
async def trigger_attack(attack_type: str):
    """Trigger attack and return immediately"""
    print(f"📡 API: Received {attack_type} attack request")
    asyncio.create_task(simulate_attack(attack_type))
    return {"message": f"Triggering {attack_type} attack - watch the live stream!", "status": "started"}

@app.get("/api/stats")
async def get_stats():
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

@app.on_event("startup")
async def startup():
    asyncio.create_task(generate_normal_traffic())
    asyncio.create_task(random_attack_generator())
    print("✅ Background generators started")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║    SMART LOGIN GUARDIAN - IMPROVED LIVE SOC                      ║
    ╚══════════════════════════════════════════════════════════════════╝

    🌐 Dashboard: http://localhost:8080
    📡 WebSocket:  ws://localhost:8080/ws

    ✅ WORKING FEATURES:
    • Auto-generating traffic every 3-6 seconds
    • Random attacks every 25-40 seconds
    • Click buttons to trigger manual attacks
    • Real-time WebSocket updates
    • Visual toast notifications
    • Button feedback and loading states

    Starting improved demo server...
    """)

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
