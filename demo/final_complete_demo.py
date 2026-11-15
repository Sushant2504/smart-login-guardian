#!/usr/bin/env python3
"""
Smart Login Guardian - FINAL COMPLETE DEMO
3D Globe + ML + Working Buttons + Complete SOC Dashboard
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Dict
from datetime import datetime
from collections import defaultdict
import asyncio
import random
import math
import numpy as np
from sklearn.ensemble import IsolationForest

app = FastAPI(title="Smart Login Guardian - Complete", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
events_store: List[Dict] = []
alerts_store: List[Dict] = []
connected_clients: List[WebSocket] = []
user_history: Dict[str, List[Dict]] = defaultdict(list)

# ML Model
class SimpleMLDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.trained = False
        self.feature_buffer = []

    def extract_features(self, event, history):
        hour = datetime.now().hour / 24.0
        day = datetime.now().weekday() / 7.0
        freq = min(len(history) / 10.0, 1.0) if history else 0.0
        failures = sum(1 for e in history[-10:] if e.get('status') == 'failed') / 10.0 if history else 0.0
        return np.array([[hour, day, freq, failures]])

    def predict(self, event, history):
        features = self.extract_features(event, history)

        if not self.trained:
            self.feature_buffer.append(features[0])
            if len(self.feature_buffer) >= 30:
                X = np.array(self.feature_buffer)
                self.model.fit(X)
                self.trained = True
                print("✅ ML Model trained!")
            return {"anomaly": False, "score": 0, "status": "training"}

        pred = self.model.predict(features)[0]
        score_samples = self.model.score_samples(features)[0]
        anomaly_score = max(0, min(100, int((1 - score_samples) * 50)))

        return {
            "anomaly": pred == -1,
            "score": anomaly_score,
            "status": "active"
        }

ml_detector = SimpleMLDetector()

# Data
LOCATIONS = [
    {"country": "India", "city": "Pune", "lat": 18.5204, "lon": 73.8567},
    {"country": "India", "city": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"country": "USA", "city": "New York", "lat": 40.7128, "lon": -74.0060},
    {"country": "USA", "city": "San Francisco", "lat": 37.7749, "lon": -122.4194},
    {"country": "UK", "city": "London", "lat": 51.5074, "lon": -0.1278},
    {"country": "Germany", "city": "Berlin", "lat": 52.5200, "lon": 13.4050},
    {"country": "Russia", "city": "Moscow", "lat": 55.7558, "lon": 37.6173},
    {"country": "China", "city": "Beijing", "lat": 39.9042, "lon": 116.4074},
    {"country": "Brazil", "city": "São Paulo", "lat": -23.5505, "lon": -46.6333},
    {"country": "Japan", "city": "Tokyo", "lat": 35.6762, "lon": 139.6503},
]

USERS = ["alice@company.com", "bob@company.com", "admin@company.com", "ceo@company.com"]

MALICIOUS_IPS = {
    "203.0.113.50": "Botnet",
    "198.51.100.200": "Tor",
    "192.0.2.100": "VPN",
}

def analyze_risk(event, history):
    signals = []
    score = 0

    if event['ip_address'] in MALICIOUS_IPS:
        signals.append(f"Known threat: {MALICIOUS_IPS[event['ip_address']]}")
        score += 30

    if event['status'] == 'failed':
        recent_failures = [e for e in history if e['status'] == 'failed'][-5:]
        if len(recent_failures) >= 2:
            signals.append(f"{len(recent_failures) + 1} failed attempts")
            score += 25

    ml_result = ml_detector.predict(event, history)
    if ml_result['anomaly']:
        signals.append(f"ML anomaly detected")
        score += ml_result['score']

    if score >= 80: level = "critical"
    elif score >= 60: level = "high"
    elif score >= 40: level = "elevated"
    elif score >= 20: level = "moderate"
    else: level = "low"

    return {
        "risk_score": min(100, score),
        "risk_level": level,
        "signals": signals,
        "ml_status": ml_result['status']
    }

async def process_event(event):
    history = user_history[event['user_identifier']]
    risk = analyze_risk(event, history)

    event_data = {
        **event,
        "event_id": f"evt_{len(events_store) + 1}",
        "risk_score": risk['risk_score'],
        "risk_level": risk['risk_level'],
        "signals": risk['signals'],
        "ml_status": risk['ml_status']
    }

    events_store.append(event_data)
    user_history[event['user_identifier']].append(event_data)

    await broadcast_event(event_data)

    if risk['risk_level'] in ['critical', 'high']:
        alert = {
            "title": f"{'🚨' if risk['risk_level'] == 'critical' else '⚠️'} {risk['risk_level'].upper()} Risk",
            "description": f"{event['user_identifier']} from {event['city']}",
            "latitude": event.get('latitude'),
            "longitude": event.get('longitude'),
            "timestamp": datetime.now().isoformat()
        }
        await broadcast_alert(alert)

async def broadcast_event(data):
    for client in list(connected_clients):
        try:
            await client.send_json({"type": "event", "data": data})
        except:
            connected_clients.remove(client)

async def broadcast_alert(data):
    alerts_store.append(data)
    for client in list(connected_clients):
        try:
            await client.send_json({"type": "alert", "data": data})
        except:
            connected_clients.remove(client)

async def generate_traffic():
    await asyncio.sleep(3)
    while True:
        try:
            user = random.choice(USERS[:3])
            location = random.choice(LOCATIONS[:5])
            status = "success" if random.random() < 0.85 else "failed"

            event = {
                "user_identifier": user,
                "ip_address": f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                "country": location["country"],
                "city": location["city"],
                "latitude": location["lat"],
                "longitude": location["lon"],
                "device_type": random.choice(["desktop", "mobile"]),
                "browser": random.choice(["Chrome", "Firefox", "Safari"]),
                "os": random.choice(["Windows", "macOS", "Linux"]),
                "status": status,
                "timestamp": datetime.now().isoformat()
            }

            await process_event(event)
            await asyncio.sleep(random.uniform(4, 7))
        except Exception as e:
            print(f"Error in traffic gen: {e}")
            await asyncio.sleep(1)

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
                "ml_status": "active" if ml_detector.trained else "training"
            }
        })

        while True:
            await websocket.receive_text()
    except:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

@app.post("/api/attack/{attack_type}")
async def trigger_attack(attack_type: str):
    """Trigger attack - WORKING VERSION"""
    print(f"🚨 API: Attack {attack_type} triggered!")

    if attack_type == "brute_force":
        for i in range(6):
            event = {
                "user_identifier": "admin@company.com",
                "ip_address": "203.0.113.50",
                "country": "Russia",
                "city": "Moscow",
                "latitude": 55.7558,
                "longitude": 37.6173,
                "device_type": "desktop",
                "browser": "curl",
                "os": "Linux",
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
            await process_event(event)
            await asyncio.sleep(0.4)

    elif attack_type == "impossible_travel":
        # India login
        event1 = {
            "user_identifier": "bob@company.com",
            "ip_address": "203.0.113.10",
            "country": "India",
            "city": "Mumbai",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "device_type": "desktop",
            "browser": "Chrome",
            "os": "Windows",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        await process_event(event1)
        await asyncio.sleep(1)

        # USA login
        event2 = {
            "user_identifier": "bob@company.com",
            "ip_address": "198.51.100.25",
            "country": "USA",
            "city": "New York",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "device_type": "mobile",
            "browser": "Safari",
            "os": "iOS",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        await process_event(event2)

    return {"message": f"Attack {attack_type} executed successfully!", "status": "ok"}

@app.get("/api/stats")
async def get_stats():
    total = len(events_store)
    critical = len([e for e in events_store if e.get('risk_level') == 'critical'])
    return {
        "total_events": total,
        "critical": critical,
        "ml_status": "active" if ml_detector.trained else "training",
        "ml_processed": len(ml_detector.feature_buffer) if not ml_detector.trained else total
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ Smart Login Guardian - 3D SOC</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.150.1/build/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.150.1/examples/js/controls/OrbitControls.js"></script>
    <style>
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        .pulse { animation: pulse 2s infinite; }
        .fade-in { animation: fadeIn 0.3s; }

        #globe-container {
            width: 100%;
            height: 500px;
            background: linear-gradient(180deg, #0a0e27 0%, #1a1d35 100%);
            border-radius: 12px;
            position: relative;
            overflow: hidden;
        }

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
                 :class="toast.type === 'success' ? 'bg-green-600' : toast.type === 'error' ? 'bg-red-600' : 'bg-orange-600'">
                <div class="flex items-start gap-3">
                    <div class="text-2xl">{{ toast.icon }}</div>
                    <div>
                        <div class="font-bold">{{ toast.title }}</div>
                        <div class="text-sm opacity-90">{{ toast.message }}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Header -->
        <header class="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800 shadow-2xl">
            <div class="container mx-auto px-6 py-4">
                <div class="flex justify-between items-center">
                    <div class="flex items-center gap-4">
                        <div class="text-4xl">🛡️</div>
                        <div>
                            <h1 class="text-2xl font-bold">Smart Login Guardian</h1>
                            <p class="text-blue-100 text-sm">3D Interactive Security Operations Center</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="flex items-center gap-2">
                            <div class="w-3 h-3 rounded-full bg-green-400 pulse"></div>
                            <span class="text-sm font-medium">{{ connected ? 'LIVE' : 'CONNECTING' }}</span>
                        </div>
                        <div class="text-xs text-blue-100">
                            ML: {{ stats.ml_status === 'active' ? '✅ Active' : '🔄 Training' }}
                        </div>
                    </div>
                </div>
            </div>
        </header>

        <div class="container mx-auto px-6 py-6">
            <!-- Stats -->
            <div class="grid grid-cols-4 gap-4 mb-6">
                <div class="bg-gray-800 p-4 rounded-lg border border-gray-700">
                    <div class="text-gray-400 text-xs uppercase">Total Events</div>
                    <div class="text-3xl font-bold">{{ stats.total_events }}</div>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg border border-red-900">
                    <div class="text-gray-400 text-xs uppercase">Critical Threats</div>
                    <div class="text-3xl font-bold text-red-400">{{ stats.critical }}</div>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg border border-purple-900">
                    <div class="text-gray-400 text-xs uppercase">ML Status</div>
                    <div class="text-xl font-bold text-purple-400">{{ stats.ml_status.toUpperCase() }}</div>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg border border-green-900">
                    <div class="text-gray-400 text-xs uppercase">ML Events</div>
                    <div class="text-3xl font-bold text-green-400">{{ stats.ml_processed }}</div>
                </div>
            </div>

            <!-- 3D Globe -->
            <div class="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold flex items-center gap-2">
                        🌍 Global Threat Map
                        <span class="text-sm text-gray-400">(Click & Drag to Rotate)</span>
                    </h2>
                    <div class="flex gap-3">
                        <button @click="triggerAttack('brute_force')"
                                :disabled="attackInProgress"
                                class="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-transform transform hover:scale-105">
                            {{ attackInProgress ? '⏳ Attacking...' : '🔨 Brute Force' }}
                        </button>
                        <button @click="triggerAttack('impossible_travel')"
                                :disabled="attackInProgress"
                                class="px-6 py-3 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-transform transform hover:scale-105">
                            ✈️ Impossible Travel
                        </button>
                    </div>
                </div>
                <div id="globe-container"></div>
                <div class="mt-3 text-sm text-gray-400 text-center">
                    Red markers = Critical threats • Orange = High risk • Yellow = Elevated
                </div>
            </div>

            <!-- Live Events -->
            <div class="bg-gray-800 rounded-lg border border-gray-700">
                <div class="p-4 border-b border-gray-700">
                    <h2 class="text-lg font-bold flex items-center gap-2">
                        <div class="w-2 h-2 rounded-full bg-green-400 pulse"></div>
                        Live Authentication Events (ML-Powered)
                    </h2>
                </div>
                <div class="p-4 h-64 overflow-y-auto space-y-2">
                    <div v-for="event in recentEvents" :key="event.event_id"
                         class="p-3 rounded-lg border transition-all" :class="getEventClass(event)">
                        <div class="flex justify-between">
                            <div class="flex-1">
                                <div class="flex items-center gap-2 mb-1">
                                    <span class="font-mono text-sm">{{ event.user_identifier }}</span>
                                    <span v-if="event.ml_status === 'active'" class="text-xs text-purple-300">🤖</span>
                                </div>
                                <div class="text-xs text-gray-400">
                                    {{ event.city }}, {{ event.country }} • {{ event.ip_address }}
                                </div>
                                <div v-if="event.signals && event.signals.length" class="mt-1">
                                    <div v-for="signal in event.signals" class="text-xs text-yellow-300">
                                        ⚠️ {{ signal }}
                                    </div>
                                </div>
                            </div>
                            <div class="text-right">
                                <div class="text-2xl font-bold" :class="getRiskColor(event.risk_score)">
                                    {{ event.risk_score }}
                                </div>
                                <div class="text-xs text-gray-400">{{ formatTime(event.timestamp) }}</div>
                            </div>
                        </div>
                    </div>
                    <div v-if="recentEvents.length === 0" class="text-center text-gray-500 py-8">
                        Waiting for events... Click attack buttons above!
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
                connected: false,
                stats: { total_events: 0, critical: 0, ml_status: 'training', ml_processed: 0 },
                recentEvents: [],
                toasts: [],
                attackInProgress: false,
                ws: null,
                scene: null,
                camera: null,
                renderer: null,
                globe: null,
                markers: []
            }
        },
        mounted() {
            this.initThreeJS();
            this.connectWebSocket();
            this.animate();
            this.loadStats();
        },
        methods: {
            initThreeJS() {
                try {
                    const container = document.getElementById('globe-container');
                    this.scene = new THREE.Scene();

                    this.camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
                    this.camera.position.z = 5;

                    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
                    this.renderer.setSize(container.clientWidth, container.clientHeight);
                    this.renderer.setClearColor(0x0a0e27, 1);
                    container.appendChild(this.renderer.domElement);

                    // Globe
                    const geometry = new THREE.SphereGeometry(2, 64, 64);
                    const material = new THREE.MeshPhongMaterial({
                        color: 0x2233ff,
                        emissive: 0x112244,
                        shininess: 10
                    });
                    this.globe = new THREE.Mesh(geometry, material);
                    this.scene.add(this.globe);

                    // Lights
                    const ambient = new THREE.AmbientLight(0x404040, 2);
                    this.scene.add(ambient);

                    const directional = new THREE.DirectionalLight(0xffffff, 1);
                    directional.position.set(5, 3, 5);
                    this.scene.add(directional);

                    // Controls
                    new THREE.OrbitControls(this.camera, this.renderer.domElement);
                } catch (e) {
                    console.error('Three.js init error:', e);
                }
            },
            addThreatMarker(lat, lon, severity) {
                try {
                    const phi = (90 - lat) * (Math.PI / 180);
                    const theta = (lon + 180) * (Math.PI / 180);

                    const x = -2 * Math.sin(phi) * Math.cos(theta);
                    const y = 2 * Math.cos(phi);
                    const z = 2 * Math.sin(phi) * Math.sin(theta);

                    const color = severity === 'critical' ? 0xff0000 :
                                 severity === 'high' ? 0xff6600 : 0xffaa00;

                    const geometry = new THREE.SphereGeometry(0.08, 16, 16);
                    const material = new THREE.MeshBasicMaterial({ color });
                    const marker = new THREE.Mesh(geometry, material);

                    marker.position.set(x, y, z);
                    this.scene.add(marker);
                    this.markers.push(marker);

                    setTimeout(() => {
                        this.scene.remove(marker);
                        this.markers = this.markers.filter(m => m !== marker);
                    }, 5000);
                } catch (e) {
                    console.error('Marker error:', e);
                }
            },
            animate() {
                requestAnimationFrame(this.animate);
                if (this.globe) this.globe.rotation.y += 0.002;
                if (this.renderer && this.scene && this.camera) {
                    this.renderer.render(this.scene, this.camera);
                }
            },
            connectWebSocket() {
                const wsUrl = `ws://${window.location.host}/ws`;
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    this.connected = true;
                    console.log('✅ Connected');
                };

                this.ws.onmessage = (event) => {
                    const msg = JSON.parse(event.data);

                    if (msg.type === 'init') {
                        this.recentEvents = msg.data.recent_events.reverse();
                        this.loadStats();
                    } else if (msg.type === 'event') {
                        this.recentEvents.unshift(msg.data);
                        if (this.recentEvents.length > 15) this.recentEvents.pop();

                        if (msg.data.latitude && msg.data.longitude) {
                            this.addThreatMarker(msg.data.latitude, msg.data.longitude, msg.data.risk_level);
                        }

                        this.loadStats();
                    } else if (msg.type === 'alert') {
                        this.showToast('warning', 'Security Alert!', msg.data.title);
                    }
                };

                this.ws.onclose = () => {
                    this.connected = false;
                    setTimeout(() => this.connectWebSocket(), 2000);
                };
            },
            async loadStats() {
                try {
                    const res = await fetch('/api/stats');
                    this.stats = await res.json();
                } catch (e) {
                    console.error('Stats error:', e);
                }
            },
            async triggerAttack(type) {
                this.attackInProgress = true;
                console.log(`🚨 Triggering ${type}...`);

                this.showToast('warning', 'Attack Triggered!', `Starting ${type} attack...`);

                try {
                    const res = await fetch(`/api/attack/${type}`, { method: 'POST' });
                    const result = await res.json();
                    console.log('✅ Attack result:', result);

                    setTimeout(() => {
                        this.attackInProgress = false;
                        this.showToast('success', 'Attack Complete', result.message);
                    }, 3000);
                } catch (error) {
                    console.error('❌ Attack failed:', error);
                    this.attackInProgress = false;
                    this.showToast('error', 'Error', 'Attack failed to execute');
                }
            },
            showToast(type, title, message) {
                const icons = { success: '✅', error: '❌', warning: '⚠️' };
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
            getEventClass(event) {
                if (event.risk_level === 'critical') return 'bg-red-900/30 border-red-700';
                if (event.risk_level === 'high') return 'bg-orange-900/30 border-orange-700';
                if (event.risk_level === 'elevated') return 'bg-yellow-900/30 border-yellow-700';
                return 'bg-gray-900 border-gray-700';
            },
            getRiskColor(score) {
                if (score >= 80) return 'text-red-400';
                if (score >= 60) return 'text-orange-400';
                if (score >= 40) return 'text-yellow-400';
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

@app.on_event("startup")
async def startup():
    asyncio.create_task(generate_traffic())
    print("✅ Complete demo with ML and working buttons started!")

if __name__ == "__main__":
    import uvicorn
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║         SMART LOGIN GUARDIAN - FINAL COMPLETE DEMO               ║
    ╚══════════════════════════════════════════════════════════════════╝

    🎯 COMPLETE FEATURES:
    ✅ 3D Globe with Three.js
    ✅ WORKING Attack Buttons with Visual Feedback
    ✅ Real ML (Scikit-learn Isolation Forest)
    ✅ Live Threat Markers on Globe
    ✅ Toast Notifications
    ✅ Auto-Training ML Model
    ✅ Real-time WebSocket
    ✅ Interactive Orbit Controls

    🌐 Opening: http://localhost:8080

    Click the attack buttons - they work now!
    """)

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
