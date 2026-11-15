#!/usr/bin/env python3
"""
Smart Login Guardian - INTERACTIVE 3D DEMO with Three.js
Real ML-powered threat detection with 3D globe visualization
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import random
import math
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

app = FastAPI(title="Smart Login Guardian - 3D Interactive", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================================
# ML MODELS - Real Scikit-learn Integration
# ==================================================================

class MLAnomalyDetector:
    """Production-grade ML anomaly detection"""

    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_history = []

    def extract_features(self, event: Dict, user_history: List[Dict]) -> np.array:
        """Extract ML features from event"""
        features = []

        # Feature 1: Hour of day (normalized)
        hour = datetime.now().hour
        features.append(hour / 24.0)

        # Feature 2: Day of week (normalized)
        day = datetime.now().weekday()
        features.append(day / 7.0)

        # Feature 3: Login frequency (events per hour)
        recent_events = [e for e in user_history if
                        (datetime.now() - datetime.fromisoformat(e['timestamp'])).seconds < 3600]
        features.append(min(len(recent_events) / 10.0, 1.0))

        # Feature 4: Failed attempt rate
        if user_history:
            failures = sum(1 for e in user_history[-20:] if e.get('status') == 'failed')
            features.append(failures / min(len(user_history[-20:]), 20))
        else:
            features.append(0.0)

        # Feature 5: Geographic diversity
        countries = set(e.get('country', 'Unknown') for e in user_history)
        features.append(min(len(countries) / 5.0, 1.0))

        # Feature 6: IP diversity
        ips = set(e.get('ip_address') for e in user_history)
        features.append(min(len(ips) / 10.0, 1.0))

        return np.array(features).reshape(1, -6)

    def train(self, historical_events: List[Dict]):
        """Train model on historical data"""
        if len(historical_events) < 50:
            return False

        features_list = []
        for event in historical_events:
            user_events = [e for e in historical_events
                          if e['user_identifier'] == event['user_identifier']]
            features = self.extract_features(event, user_events)
            features_list.append(features[0])

        X = np.array(features_list)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True
        return True

    def predict_anomaly(self, event: Dict, user_history: List[Dict]) -> Dict:
        """Predict if event is anomalous"""
        features = self.extract_features(event, user_history)

        if not self.is_trained:
            # Collect features for later training
            self.feature_history.append(features[0])

            if len(self.feature_history) >= 50:
                X = np.array(self.feature_history)
                X_scaled = self.scaler.fit_transform(X)
                self.model.fit(X_scaled)
                self.is_trained = True

            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "ml_confidence": 0.0,
                "status": "training"
            }

        # Scale and predict
        features_scaled = self.scaler.transform(features)
        prediction = self.model.predict(features_scaled)[0]
        score = self.model.score_samples(features_scaled)[0]

        # Normalize score to 0-100
        anomaly_score = max(0, min(100, int((1 - score) * 50)))

        return {
            "is_anomaly": prediction == -1,
            "anomaly_score": anomaly_score,
            "ml_confidence": abs(score),
            "status": "active"
        }

# Initialize ML detector
ml_detector = MLAnomalyDetector()

# ==================================================================
# DATA & STORAGE
# ==================================================================

events_store: List[Dict] = []
alerts_store: List[Dict] = []
connected_clients: List[WebSocket] = []
user_history: Dict[str, List[Dict]] = defaultdict(list)

LOCATIONS = [
    {"country": "India", "city": "Pune", "lat": 18.5204, "lon": 73.8567},
    {"country": "India", "city": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"country": "USA", "city": "New York", "lat": 40.7128, "lon": -74.0060},
    {"country": "USA", "city": "San Francisco", "lat": 37.7749, "lon": -122.4194},
    {"country": "UK", "city": "London", "lat": 51.5074, "lon": -0.1278},
    {"country": "Germany", "city": "Berlin", "lat": 52.5200, "lon": 13.4050},
    {"country": "China", "city": "Beijing", "lat": 39.9042, "lon": 116.4074},
    {"country": "Russia", "city": "Moscow", "lat": 55.7558, "lon": 37.6173},
    {"country": "Brazil", "city": "São Paulo", "lat": -23.5505, "lon": -46.6333},
    {"country": "Japan", "city": "Tokyo", "lat": 35.6762, "lon": 139.6503},
]

USERS = [
    "alice@company.com", "bob@company.com", "charlie@company.com",
    "admin@company.com", "ceo@company.com", "engineer@company.com"
]

MALICIOUS_IPS = {
    "203.0.113.50": "Botnet",
    "198.51.100.200": "Tor",
    "192.0.2.100": "VPN",
}

# ==================================================================
# RISK ANALYSIS with ML
# ==================================================================

def analyze_risk_with_ml(event: Dict) -> Dict:
    """Enhanced risk analysis with ML"""
    signals = []
    rule_score = 0

    # Rule-based signals
    if event['ip_address'] in MALICIOUS_IPS:
        signals.append({
            "type": "malicious_ip",
            "value": 30,
            "description": f"Known threat: {MALICIOUS_IPS[event['ip_address']]}"
        })
        rule_score += 30

    if event['status'] == 'failed':
        recent_failures = [e for e in user_history[event['user_identifier']]
                          if e['status'] == 'failed' and
                          (datetime.now() - datetime.fromisoformat(e['timestamp'])).seconds < 300]
        if len(recent_failures) >= 2:
            signals.append({
                "type": "brute_force",
                "value": 25,
                "description": f"{len(recent_failures) + 1} failed attempts"
            })
            rule_score += 25

    # ML-based anomaly detection
    ml_result = ml_detector.predict_anomaly(event, user_history[event['user_identifier']])

    if ml_result['is_anomaly']:
        signals.append({
            "type": "ml_anomaly",
            "value": ml_result['anomaly_score'],
            "description": f"ML detected anomaly (confidence: {ml_result['ml_confidence']:.2f})"
        })

    # Combined score
    total_score = min(100, rule_score + ml_result['anomaly_score'])

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
        "risk_score": total_score,
        "risk_level": risk_level,
        "signals": signals,
        "ml_status": ml_result['status'],
        "ml_anomaly": ml_result['is_anomaly']
    }

# ==================================================================
# EVENT GENERATION
# ==================================================================

async def generate_normal_traffic():
    """Generate realistic traffic"""
    await asyncio.sleep(3)
    while True:
        try:
            user = random.choice(USERS[:4])
            location = random.choice(LOCATIONS[:5])
            status = "success" if random.random() < 0.85 else "failed"

            event = {
                "user_identifier": user,
                "ip_address": f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                "country": location["country"],
                "city": location["city"],
                "latitude": location["lat"],
                "longitude": location["lon"],
                "device_type": random.choice(["desktop", "mobile", "tablet"]),
                "browser": random.choice(["Chrome", "Firefox", "Safari"]),
                "os": random.choice(["Windows", "macOS", "Linux", "iOS"]),
                "status": status,
                "timestamp": datetime.now().isoformat()
            }

            await process_event(event)
            await asyncio.sleep(random.uniform(4, 7))
        except:
            await asyncio.sleep(1)

async def process_event(event: Dict):
    """Process event with ML"""
    risk = analyze_risk_with_ml(event)

    event_id = f"evt_{len(events_store) + 1}"
    event_data = {
        **event,
        "event_id": event_id,
        "risk_score": risk['risk_score'],
        "risk_level": risk['risk_level'],
        "signals": risk['signals'],
        "ml_status": risk['ml_status'],
        "ml_anomaly": risk['ml_anomaly']
    }

    events_store.append(event_data)
    user_history[event['user_identifier']].append(event_data)

    await broadcast_event(event_data)

    if risk['risk_level'] in ['critical', 'high']:
        alert = {
            "title": f"{'🚨 Critical' if risk['risk_level'] == 'critical' else '⚠️ High'} Risk Login",
            "description": f"{event['user_identifier']} from {event['city']}, {event['country']}",
            "severity": risk['risk_level'],
            "latitude": event['latitude'],
            "longitude": event['longitude'],
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

# ==================================================================
# WEBSOCKET
# ==================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        await websocket.send_json({
            "type": "init",
            "data": {
                "recent_events": events_store[-20:],
                "recent_alerts": alerts_store[-10:],
                "ml_status": "active" if ml_detector.is_trained else "training"
            }
        })

        while True:
            await websocket.receive_text()
            await websocket.send_json({"type": "pong"})
    except:
        connected_clients.remove(websocket)

# ==================================================================
# API
# ==================================================================

@app.post("/api/attack/{attack_type}")
async def trigger_attack(attack_type: str):
    """Trigger attack simulation"""
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

    return {"message": f"Attack {attack_type} triggered"}

@app.get("/api/stats")
async def get_stats():
    """Get statistics"""
    total = len(events_store)
    critical = len([e for e in events_store if e.get('risk_level') == 'critical'])
    ml_trained = ml_detector.is_trained

    return {
        "total_events": total,
        "critical": critical,
        "ml_status": "active" if ml_trained else "training",
        "ml_events_processed": len(ml_detector.feature_history) if not ml_trained else total
    }

# ==================================================================
# THREE.JS INTERACTIVE FRONTEND
# ==================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Login Guardian - 3D Interactive SOC</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.150.1/build/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.150.1/examples/js/controls/OrbitControls.js"></script>
    <style>
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes blink { 0%, 50%, 100% { opacity: 1; } 25%, 75% { opacity: 0.3; } }
        .pulse { animation: pulse 2s infinite; }
        .blink { animation: blink 1s infinite; }
        #globe-container {
            width: 100%;
            height: 600px;
            background: linear-gradient(180deg, #0a0e27 0%, #1a1d35 100%);
            border-radius: 12px;
            position: relative;
        }
    </style>
</head>
<body class="bg-gray-900 text-gray-100">
    <div id="app">
        <!-- Header -->
        <header class="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800 shadow-2xl">
            <div class="container mx-auto px-6 py-4">
                <div class="flex justify-between items-center">
                    <div class="flex items-center gap-4">
                        <div class="text-4xl">🛡️</div>
                        <div>
                            <h1 class="text-2xl font-bold">Smart Login Guardian</h1>
                            <p class="text-blue-100 text-sm">3D Interactive Threat Intelligence</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-6">
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
            </div>
        </header>

        <div class="container mx-auto px-6 py-6">
            <!-- Stats -->
            <div class="grid grid-cols-4 gap-4 mb-6">
                <div class="bg-gray-800 p-4 rounded-lg border border-gray-700">
                    <div class="text-gray-400 text-xs uppercase">Events</div>
                    <div class="text-3xl font-bold">{{ stats.total_events }}</div>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg border border-red-900">
                    <div class="text-gray-400 text-xs uppercase">Critical</div>
                    <div class="text-3xl font-bold text-red-400">{{ stats.critical }}</div>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg border border-purple-900">
                    <div class="text-gray-400 text-xs uppercase">ML Status</div>
                    <div class="text-lg font-bold text-purple-400">{{ stats.ml_status }}</div>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg border border-green-900">
                    <div class="text-gray-400 text-xs uppercase">ML Processed</div>
                    <div class="text-3xl font-bold text-green-400">{{ stats.ml_events_processed }}</div>
                </div>
            </div>

            <!-- 3D Globe -->
            <div class="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold">🌍 Global Threat Map (Interactive)</h2>
                    <button @click="triggerAttack('brute_force')"
                            class="px-4 py-2 bg-red-600 hover:bg-red-700 rounded font-medium">
                        🔨 Simulate Attack
                    </button>
                </div>
                <div id="globe-container"></div>
            </div>

            <!-- Live Events -->
            <div class="bg-gray-800 rounded-lg border border-gray-700">
                <div class="p-4 border-b border-gray-700">
                    <h2 class="text-lg font-bold flex items-center gap-2">
                        <div class="w-2 h-2 rounded-full bg-green-400 pulse"></div>
                        Live Events (ML-Powered)
                    </h2>
                </div>
                <div class="p-4 h-64 overflow-y-auto space-y-2">
                    <div v-for="event in recentEvents" :key="event.event_id"
                         class="p-3 rounded-lg border" :class="getEventClass(event)">
                        <div class="flex justify-between">
                            <div class="flex-1">
                                <div class="font-mono text-sm">{{ event.user_identifier }}</div>
                                <div class="text-xs text-gray-400">
                                    {{ event.city }}, {{ event.country }} • {{ event.ip_address }}
                                </div>
                                <div v-if="event.ml_anomaly" class="mt-1 text-xs text-purple-300">
                                    🤖 ML Anomaly Detected
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
                stats: { total_events: 0, critical: 0, ml_status: 'training', ml_events_processed: 0 },
                recentEvents: [],
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
        },
        methods: {
            initThreeJS() {
                const container = document.getElementById('globe-container');
                this.scene = new THREE.Scene();

                this.camera = new THREE.PerspectiveCamera(
                    60,
                    container.clientWidth / container.clientHeight,
                    0.1,
                    1000
                );
                this.camera.position.z = 5;

                this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
                this.renderer.setSize(container.clientWidth, container.clientHeight);
                this.renderer.setClearColor(0x0a0e27, 1);
                container.appendChild(this.renderer.domElement);

                // Create Earth globe
                const geometry = new THREE.SphereGeometry(2, 64, 64);
                const texture = new THREE.TextureLoader().load(
                    'https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg'
                );
                const material = new THREE.MeshPhongMaterial({ map: texture });
                this.globe = new THREE.Mesh(geometry, material);
                this.scene.add(this.globe);

                // Add lights
                const ambientLight = new THREE.AmbientLight(0x404040, 2);
                this.scene.add(ambientLight);

                const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
                directionalLight.position.set(5, 3, 5);
                this.scene.add(directionalLight);

                // Add orbit controls
                new THREE.OrbitControls(this.camera, this.renderer.domElement);
            },
            addThreatMarker(lat, lon, severity) {
                const phi = (90 - lat) * (Math.PI / 180);
                const theta = (lon + 180) * (Math.PI / 180);

                const x = -2 * Math.sin(phi) * Math.cos(theta);
                const y = 2 * Math.cos(phi);
                const z = 2 * Math.sin(phi) * Math.sin(theta);

                const color = severity === 'critical' ? 0xff0000 :
                             severity === 'high' ? 0xff6600 : 0xffaa00;

                const geometry = new THREE.SphereGeometry(0.05, 16, 16);
                const material = new THREE.MeshBasicMaterial({ color });
                const marker = new THREE.Mesh(geometry, material);

                marker.position.set(x, y, z);
                this.scene.add(marker);
                this.markers.push(marker);

                // Remove marker after animation
                setTimeout(() => {
                    this.scene.remove(marker);
                    this.markers = this.markers.filter(m => m !== marker);
                }, 5000);
            },
            animate() {
                requestAnimationFrame(this.animate);
                if (this.globe) this.globe.rotation.y += 0.001;
                this.renderer.render(this.scene, this.camera);
            },
            connectWebSocket() {
                const wsUrl = `ws://${window.location.host}/ws`;
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    this.connected = true;
                };

                this.ws.onmessage = (event) => {
                    const msg = JSON.parse(event.data);

                    if (msg.type === 'init') {
                        this.recentEvents = msg.data.recent_events.reverse();
                        this.loadStats();
                    } else if (msg.type === 'event') {
                        this.recentEvents.unshift(msg.data);
                        if (this.recentEvents.length > 20) this.recentEvents.pop();

                        if (msg.data.latitude && msg.data.longitude) {
                            this.addThreatMarker(
                                msg.data.latitude,
                                msg.data.longitude,
                                msg.data.risk_level
                            );
                        }

                        this.loadStats();
                    }
                };
            },
            async loadStats() {
                const res = await fetch('/api/stats');
                this.stats = await res.json();
            },
            async triggerAttack(type) {
                await fetch(`/api/attack/${type}`, { method: 'POST' });
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

@app.on_event("startup")
async def startup():
    asyncio.create_task(generate_normal_traffic())
    print("✅ 3D Interactive demo with ML started!")

if __name__ == "__main__":
    import uvicorn
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║    SMART LOGIN GUARDIAN - 3D INTERACTIVE with ML                 ║
    ╚══════════════════════════════════════════════════════════════════╝

    🌍 3D Globe Visualization with Three.js
    🤖 Real ML-Powered Anomaly Detection (Scikit-learn)
    📊 Interactive Threat Intelligence
    🔴 Real-time Attack Visualization

    Features:
    ✅ Three.js 3D rotating Earth
    ✅ Live threat markers on globe
    ✅ Scikit-learn Isolation Forest
    ✅ Real-time ML anomaly detection
    ✅ Interactive controls
    ✅ Auto-training ML model

    Opening: http://localhost:8080
    """)

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
