#!/usr/bin/env python3
"""
Smart Login Guardian - COMPLETE DASHBOARD WITH GRAPHS & STATISTICS
Features: Charts, graphs, numbers, ML visualization, analytics
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import asyncio
import random
import math
import numpy as np
from sklearn.ensemble import IsolationForest

app = FastAPI(title="Smart Login Guardian - Dashboard with Graphs", version="5.0.0")

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

# ML Model with Enhanced Tracking
class EnhancedMLDetector:
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100,
            max_samples=256
        )
        self.trained = False
        self.feature_buffer = []
        self.training_events_needed = 30
        self.total_processed = 0
        self.anomalies_detected = 0
        self.feature_names = ["hour_of_day", "day_of_week", "login_frequency", "failure_rate"]

    def extract_features(self, event, history):
        """Extract 4 features for ML model"""
        hour = datetime.now().hour / 24.0
        day = datetime.now().weekday() / 7.0
        freq = min(len(history) / 10.0, 1.0) if history else 0.0
        failures = sum(1 for e in history[-10:] if e.get('status') == 'failed') / 10.0 if history else 0.0
        return np.array([[hour, day, freq, failures]])

    def get_training_progress(self):
        """Get training progress percentage"""
        if self.trained:
            return 100
        return min(100, int((len(self.feature_buffer) / self.training_events_needed) * 100))

    def get_model_stats(self):
        """Get detailed model statistics"""
        return {
            "status": "active" if self.trained else "training",
            "trained": self.trained,
            "training_progress": self.get_training_progress(),
            "events_processed": self.total_processed,
            "anomalies_detected": self.anomalies_detected,
            "training_events_needed": self.training_events_needed,
            "current_buffer_size": len(self.feature_buffer),
            "model_params": {
                "algorithm": "Isolation Forest",
                "n_estimators": 100,
                "contamination": 0.1,
                "features": self.feature_names
            }
        }

    def predict(self, event, history):
        """Predict if event is anomalous"""
        features = self.extract_features(event, history)
        self.total_processed += 1

        if not self.trained:
            self.feature_buffer.append(features[0])
            if len(self.feature_buffer) >= self.training_events_needed:
                X = np.array(self.feature_buffer)
                self.model.fit(X)
                self.trained = True
                print(f"✅ ML Model TRAINED! (on {len(self.feature_buffer)} events)")
            return {
                "anomaly": False,
                "score": 0,
                "confidence": 0,
                "status": "training",
                "features": features[0].tolist()
            }

        # Predict anomaly
        pred = self.model.predict(features)[0]
        score_samples = self.model.score_samples(features)[0]

        # Calculate anomaly score (0-100)
        anomaly_score = max(0, min(100, int((-score_samples) * 20)))

        # Calculate confidence
        confidence = min(100, abs(int(score_samples * 100)))

        is_anomaly = pred == -1
        if is_anomaly:
            self.anomalies_detected += 1

        return {
            "anomaly": is_anomaly,
            "score": anomaly_score,
            "confidence": confidence,
            "status": "active",
            "features": features[0].tolist()
        }

ml_detector = EnhancedMLDetector()

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

USERS = ["alice@company.com", "bob@company.com", "admin@company.com", "ceo@company.com", "john@company.com"]

MALICIOUS_IPS = {
    "203.0.113.50": "Botnet C&C Server",
    "198.51.100.200": "Tor Exit Node",
    "192.0.2.100": "Known VPN Proxy",
}

def analyze_risk(event, history, ml_result):
    """Enhanced risk analysis with ML integration"""
    signals = []
    score = 0

    # IP Reputation Check
    if event['ip_address'] in MALICIOUS_IPS:
        threat_type = MALICIOUS_IPS[event['ip_address']]
        signals.append(f"🚨 Known threat: {threat_type}")
        score += 30

    # Failed Login Check
    if event['status'] == 'failed':
        signals.append("❌ Failed login attempt")
        score += 15

    # Brute Force Detection
    recent_failures = [e for e in history[-10:] if e.get('status') == 'failed']
    if len(recent_failures) >= 3:
        signals.append(f"🔨 Brute force pattern ({len(recent_failures)} failures)")
        score += 25

    # Geographic Anomaly
    user_countries = set(e.get('country') for e in history[-20:] if e.get('country'))
    if event['country'] not in user_countries and len(user_countries) > 0:
        signals.append(f"🌍 New country: {event['country']}")
        score += 20

    # High-risk Country Check
    if event['country'] in ['Russia', 'China', 'North Korea']:
        signals.append(f"⚠️ High-risk region: {event['country']}")
        score += 15

    # ML Anomaly Detection
    if ml_result['status'] == 'active':
        if ml_result['anomaly']:
            signals.append(f"🤖 ML Anomaly Detected (score: {ml_result['score']})")
            score += ml_result['score']
        elif ml_result['score'] > 30:
            signals.append(f"🤖 ML Suspicious (score: {ml_result['score']})")
            score += int(ml_result['score'] * 0.5)

    # Calculate final score
    final_score = min(100, score)

    # Determine severity
    if final_score < 20:
        severity = "low"
    elif final_score < 40:
        severity = "moderate"
    elif final_score < 60:
        severity = "elevated"
    elif final_score < 80:
        severity = "high"
    else:
        severity = "critical"

    return {
        "score": final_score,
        "severity": severity,
        "signals": signals,
        "ml_result": ml_result
    }

async def process_event(event_data):
    """Process authentication event"""
    user = event_data.get('user_identifier')
    history = user_history[user]

    # ML Prediction
    ml_result = ml_detector.predict(event_data, history)

    # Risk Analysis
    risk_analysis = analyze_risk(event_data, history, ml_result)

    # Create event
    event = {
        **event_data,
        'event_id': len(events_store) + 1,
        'timestamp': datetime.now().isoformat(),
        'risk_score': risk_analysis['score'],
        'risk_level': risk_analysis['severity'],
        'signals': risk_analysis['signals'],
        'ml_status': ml_result['status'],
        'ml_anomaly': ml_result['anomaly'],
        'ml_score': ml_result['score'],
        'ml_confidence': ml_result.get('confidence', 0),
        'ml_features': ml_result.get('features', [])
    }

    events_store.append(event)
    user_history[user].append(event)

    # Create alert for high-risk events
    if risk_analysis['severity'] in ['high', 'critical']:
        alert = {
            'title': f"{risk_analysis['severity'].upper()} Risk Login Detected",
            'user': user,
            'score': risk_analysis['score'],
            'signals': risk_analysis['signals'],
            'timestamp': event['timestamp']
        }
        alerts_store.append(alert)

        # Broadcast alert
        for client in connected_clients:
            try:
                await client.send_json({"type": "alert", "data": alert})
            except:
                pass

    # Broadcast event
    for client in connected_clients:
        try:
            await client.send_json({"type": "event", "data": event})
        except:
            pass

    return event

# API Endpoints
@app.get("/")
async def root():
    return HTMLResponse(HTML_CONTENT)

@app.get("/api/stats")
async def get_stats():
    """Get comprehensive system statistics"""
    model_stats = ml_detector.get_model_stats()

    # Calculate statistics
    total_events = len(events_store)
    critical_count = len([e for e in events_store if e.get('risk_level') == 'critical'])
    high_count = len([e for e in events_store if e.get('risk_level') == 'high'])
    elevated_count = len([e for e in events_store if e.get('risk_level') == 'elevated'])
    moderate_count = len([e for e in events_store if e.get('risk_level') == 'moderate'])
    low_count = len([e for e in events_store if e.get('risk_level') == 'low'])

    success_count = len([e for e in events_store if e.get('status') == 'success'])
    failed_count = len([e for e in events_store if e.get('status') == 'failed'])

    # Country distribution
    country_counts = Counter([e.get('country') for e in events_store if e.get('country')])

    # Recent events for timeline (last hour)
    recent_events = []
    if events_store:
        for event in events_store[-50:]:  # Last 50 events
            recent_events.append({
                'timestamp': event['timestamp'],
                'risk_score': event['risk_score']
            })

    return {
        "total_events": total_events,
        "critical_alerts": critical_count,
        "high_alerts": high_count,
        "elevated_alerts": elevated_count,
        "moderate_alerts": moderate_count,
        "low_alerts": low_count,
        "success_logins": success_count,
        "failed_logins": failed_count,
        "success_rate": round((success_count / total_events * 100) if total_events > 0 else 0, 1),
        "failure_rate": round((failed_count / total_events * 100) if total_events > 0 else 0, 1),
        "ml_status": model_stats['status'],
        "ml_processed": model_stats['events_processed'],
        "ml_anomalies": model_stats['anomalies_detected'],
        "ml_training_progress": model_stats['training_progress'],
        "ml_model_stats": model_stats,
        "country_distribution": dict(country_counts.most_common(10)),
        "timeline_data": recent_events[-20:],  # Last 20 for chart
        "risk_distribution": {
            "critical": critical_count,
            "high": high_count,
            "elevated": elevated_count,
            "moderate": moderate_count,
            "low": low_count
        }
    }

@app.get("/api/ml/stats")
async def get_ml_stats():
    """Get detailed ML model statistics"""
    return ml_detector.get_model_stats()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

    # Send initial data
    await websocket.send_json({
        "type": "init",
        "data": {
            "recent_events": events_store[-15:],
            "stats": await get_stats()
        }
    })

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

@app.post("/api/attack/{attack_type}")
async def trigger_attack(attack_type: str):
    """Trigger simulated attack"""
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
                "status": "failed",
                "device": "Unknown",
                "browser": "curl/7.64.1"
            }
            await process_event(event)
            await asyncio.sleep(0.4)

    elif attack_type == "impossible_travel":
        # Login from India
        event1 = {
            "user_identifier": "ceo@company.com",
            "ip_address": "103.1.1.1",
            "country": "India",
            "city": "Mumbai",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "status": "success",
            "device": "iPhone 15",
            "browser": "Safari 17"
        }
        await process_event(event1)

        await asyncio.sleep(1)

        # Login from USA 5 minutes later (impossible!)
        event2 = {
            "user_identifier": "ceo@company.com",
            "ip_address": "192.0.2.1",
            "country": "USA",
            "city": "New York",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "status": "success",
            "device": "MacBook Pro",
            "browser": "Chrome 120"
        }
        await process_event(event2)

    elif attack_type == "credential_stuffing":
        users = ["alice@company.com", "bob@company.com", "john@company.com"]
        for user in users:
            event = {
                "user_identifier": user,
                "ip_address": "198.51.100.200",
                "country": "Russia",
                "city": "Moscow",
                "latitude": 55.7558,
                "longitude": 37.6173,
                "status": "failed",
                "device": "Linux Bot",
                "browser": "Python/3.9"
            }
            await process_event(event)
            await asyncio.sleep(0.3)

    return {"message": f"Attack {attack_type} executed!", "status": "success"}

# Background task to generate traffic
async def generate_traffic():
    """Generate realistic authentication traffic"""
    await asyncio.sleep(3)  # Wait for startup

    while True:
        try:
            # Random user and location
            user = random.choice(USERS)
            loc = random.choice(LOCATIONS)

            # 90% success, 10% fail
            status = "success" if random.random() > 0.1 else "failed"

            # Random IP (mostly normal, sometimes malicious)
            if random.random() > 0.95:
                ip = random.choice(list(MALICIOUS_IPS.keys()))
            else:
                ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

            event = {
                "user_identifier": user,
                "ip_address": ip,
                "country": loc['country'],
                "city": loc['city'],
                "latitude": loc['lat'],
                "longitude": loc['lon'],
                "status": status,
                "device": random.choice(["iPhone 15", "MacBook Pro", "Windows PC", "Android"]),
                "browser": random.choice(["Chrome 120", "Safari 17", "Firefox 121", "Edge 120"])
            }

            await process_event(event)

            # Random delay 3-7 seconds
            await asyncio.sleep(random.uniform(3, 7))
        except Exception as e:
            print(f"Traffic generation error: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(generate_traffic())

# HTML Content with Charts and Graphs
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Login Guardian - Analytics Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.159.0/build/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.159.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }

        @keyframes slideIn {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .slide-in { animation: slideIn 0.3s ease-out; }

        @keyframes glow {
            0%, 100% { box-shadow: 0 0 5px rgba(59, 130, 246, 0.5); }
            50% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.8); }
        }
        .glow { animation: glow 2s ease-in-out infinite; }

        #globe-container { height: 400px; background: linear-gradient(180deg, #0a0e27 0%, #1a1f3a 100%); }

        .stat-card {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            border-color: #3b82f6;
        }

        .number-big {
            font-size: 2.5rem;
            font-weight: 800;
            line-height: 1;
        }
    </style>
</head>
<body class="bg-gray-900 text-white">
    <div id="app" class="container mx-auto p-4">
        <!-- Header -->
        <div class="mb-6 bg-gradient-to-r from-blue-900 to-purple-900 rounded-lg p-6 shadow-2xl">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-bold mb-2">🛡️ Smart Login Guardian Analytics</h1>
                    <p class="text-blue-200">Real-time Threat Detection Dashboard with ML & Charts</p>
                </div>
                <div class="flex items-center gap-4">
                    <div class="text-right">
                        <div class="text-sm text-gray-300">WebSocket</div>
                        <div class="flex items-center gap-2">
                            <div class="w-3 h-3 rounded-full" :class="connected ? 'bg-green-400 pulse' : 'bg-red-400'"></div>
                            <span class="font-mono text-sm">{{ connected ? 'LIVE' : 'OFFLINE' }}</span>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="text-sm text-gray-300">ML Model</div>
                        <div class="flex items-center gap-2">
                            <div class="w-3 h-3 rounded-full" :class="stats.ml_status === 'active' ? 'bg-green-400 pulse' : 'bg-yellow-400 pulse'"></div>
                            <span class="font-mono text-sm uppercase">{{ stats.ml_status }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Key Metrics Row -->
        <div class="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="stat-card rounded-lg p-4">
                <div class="text-gray-400 text-sm mb-1">Total Events</div>
                <div class="number-big text-blue-400">{{ stats.total_events || 0 }}</div>
                <div class="text-xs text-gray-500 mt-2">All authentication events</div>
            </div>

            <div class="stat-card rounded-lg p-4">
                <div class="text-gray-400 text-sm mb-1">Critical Alerts</div>
                <div class="number-big text-red-400">{{ stats.critical_alerts || 0 }}</div>
                <div class="text-xs text-gray-500 mt-2">High-risk threats detected</div>
            </div>

            <div class="stat-card rounded-lg p-4">
                <div class="text-gray-400 text-sm mb-1">Success Rate</div>
                <div class="number-big text-green-400">{{ stats.success_rate || 0 }}%</div>
                <div class="text-xs text-gray-500 mt-2">{{ stats.success_logins || 0 }} successful logins</div>
            </div>

            <div class="stat-card rounded-lg p-4">
                <div class="text-gray-400 text-sm mb-1">ML Anomalies</div>
                <div class="number-big text-purple-400">{{ stats.ml_anomalies || 0 }}</div>
                <div class="text-xs text-gray-500 mt-2">Detected by AI model</div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="mb-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Risk Distribution Chart -->
            <div class="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <h3 class="text-lg font-bold mb-4">📊 Risk Level Distribution</h3>
                <canvas id="riskChart" height="250"></canvas>
            </div>

            <!-- Timeline Chart -->
            <div class="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <h3 class="text-lg font-bold mb-4">📈 Risk Score Timeline (Last 20 Events)</h3>
                <canvas id="timelineChart" height="250"></canvas>
            </div>
        </div>

        <!-- Stats Grid -->
        <div class="mb-6 grid grid-cols-2 md:grid-cols-6 gap-3">
            <div class="bg-gray-800 border border-red-700 rounded-lg p-3 text-center">
                <div class="text-3xl font-bold text-red-400">{{ stats.critical_alerts || 0 }}</div>
                <div class="text-xs text-gray-400 mt-1">Critical</div>
            </div>
            <div class="bg-gray-800 border border-orange-700 rounded-lg p-3 text-center">
                <div class="text-3xl font-bold text-orange-400">{{ stats.high_alerts || 0 }}</div>
                <div class="text-xs text-gray-400 mt-1">High</div>
            </div>
            <div class="bg-gray-800 border border-yellow-700 rounded-lg p-3 text-center">
                <div class="text-3xl font-bold text-yellow-400">{{ stats.elevated_alerts || 0 }}</div>
                <div class="text-xs text-gray-400 mt-1">Elevated</div>
            </div>
            <div class="bg-gray-800 border border-blue-700 rounded-lg p-3 text-center">
                <div class="text-3xl font-bold text-blue-400">{{ stats.moderate_alerts || 0 }}</div>
                <div class="text-xs text-gray-400 mt-1">Moderate</div>
            </div>
            <div class="bg-gray-800 border border-green-700 rounded-lg p-3 text-center">
                <div class="text-3xl font-bold text-green-400">{{ stats.low_alerts || 0 }}</div>
                <div class="text-xs text-gray-400 mt-1">Low</div>
            </div>
            <div class="bg-gray-800 border border-purple-700 rounded-lg p-3 text-center">
                <div class="text-3xl font-bold text-purple-400">{{ stats.ml_training_progress || 0 }}%</div>
                <div class="text-xs text-gray-400 mt-1">ML Trained</div>
            </div>
        </div>

        <!-- Main Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 3D Globe with Attack Buttons -->
            <div class="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                <div class="p-4 border-b border-gray-700">
                    <h2 class="text-lg font-bold mb-4">🌍 Real-time Threat Visualization</h2>
                    <div class="grid grid-cols-3 gap-3">
                        <button @click="triggerAttack('brute_force')"
                                :disabled="attackInProgress"
                                class="px-4 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-all transform hover:scale-105 glow">
                            <div class="text-2xl mb-1">🔨</div>
                            <div class="text-sm">Brute Force</div>
                        </button>
                        <button @click="triggerAttack('impossible_travel')"
                                :disabled="attackInProgress"
                                class="px-4 py-3 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-all transform hover:scale-105 glow">
                            <div class="text-2xl mb-1">✈️</div>
                            <div class="text-sm">Impossible Travel</div>
                        </button>
                        <button @click="triggerAttack('credential_stuffing')"
                                :disabled="attackInProgress"
                                class="px-4 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-all transform hover:scale-105 glow">
                            <div class="text-2xl mb-1">🎯</div>
                            <div class="text-sm">Credential Stuffing</div>
                        </button>
                    </div>
                </div>
                <div id="globe-container"></div>
            </div>

            <!-- Live Events -->
            <div class="bg-gray-800 rounded-lg border border-gray-700">
                <div class="p-4 border-b border-gray-700">
                    <h2 class="text-lg font-bold flex items-center gap-2">
                        <div class="w-2 h-2 rounded-full bg-green-400 pulse"></div>
                        Live Events ({{ recentEvents.length }})
                    </h2>
                </div>
                <div class="p-4 h-[500px] overflow-y-auto space-y-2">
                    <div v-for="event in recentEvents.slice(0, 10)" :key="event.event_id"
                         class="p-3 rounded-lg border slide-in transition-all"
                         :class="getEventClass(event)">
                        <div class="flex justify-between mb-2">
                            <div class="flex-1">
                                <div class="flex items-center gap-2 mb-1">
                                    <span class="font-mono text-sm font-bold">{{ event.user_identifier }}</span>
                                    <span v-if="event.ml_status === 'active'" class="text-xs">🤖</span>
                                    <span v-if="event.ml_anomaly" class="text-xs bg-purple-600 px-2 py-0.5 rounded">ANOMALY</span>
                                </div>
                                <div class="text-xs text-gray-400">
                                    📍 {{ event.city }}, {{ event.country }} • {{ event.ip_address }}
                                </div>
                            </div>
                            <div class="text-right">
                                <div class="text-3xl font-bold" :class="getRiskColor(event.risk_score)">
                                    {{ event.risk_score }}
                                </div>
                                <div class="text-xs text-gray-400 uppercase">{{ event.risk_level }}</div>
                            </div>
                        </div>
                        <div v-if="event.signals && event.signals.length" class="mt-2 space-y-1">
                            <div v-for="signal in event.signals" class="text-xs text-yellow-300">
                                {{ signal }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Toast Notifications -->
        <div class="fixed top-4 right-4 space-y-2 z-50">
            <div v-for="toast in toasts" :key="toast.id"
                 class="bg-gray-800 border-l-4 rounded-lg shadow-2xl p-4 min-w-[300px] slide-in"
                 :class="getToastClass(toast.type)">
                <div class="flex items-start gap-3">
                    <div class="text-2xl">{{ getToastIcon(toast.type) }}</div>
                    <div class="flex-1">
                        <div class="font-bold">{{ toast.title }}</div>
                        <div class="text-sm text-gray-300 mt-1">{{ toast.message }}</div>
                    </div>
                    <button @click="removeToast(toast.id)" class="text-gray-400 hover:text-white">✕</button>
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
                stats: {
                    total_events: 0,
                    critical_alerts: 0,
                    high_alerts: 0,
                    elevated_alerts: 0,
                    moderate_alerts: 0,
                    low_alerts: 0,
                    success_logins: 0,
                    failed_logins: 0,
                    success_rate: 0,
                    failure_rate: 0,
                    ml_status: 'training',
                    ml_processed: 0,
                    ml_anomalies: 0,
                    ml_training_progress: 0,
                    country_distribution: {},
                    timeline_data: [],
                    risk_distribution: {}
                },
                recentEvents: [],
                toasts: [],
                attackInProgress: false,
                ws: null,
                scene: null,
                camera: null,
                renderer: null,
                globe: null,
                markers: [],
                riskChart: null,
                timelineChart: null
            }
        },
        mounted() {
            this.initThreeJS();
            this.connectWebSocket();
            this.animate();
            this.loadStats();
            this.initCharts();
            setInterval(this.loadStats, 3000);
            setInterval(this.updateCharts, 3000);
        },
        methods: {
            initCharts() {
                // Risk Distribution Pie Chart
                const riskCtx = document.getElementById('riskChart').getContext('2d');
                this.riskChart = new Chart(riskCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Critical', 'High', 'Elevated', 'Moderate', 'Low'],
                        datasets: [{
                            data: [0, 0, 0, 0, 0],
                            backgroundColor: [
                                'rgba(239, 68, 68, 0.8)',
                                'rgba(249, 115, 22, 0.8)',
                                'rgba(234, 179, 8, 0.8)',
                                'rgba(59, 130, 246, 0.8)',
                                'rgba(34, 197, 94, 0.8)'
                            ],
                            borderColor: [
                                'rgb(239, 68, 68)',
                                'rgb(249, 115, 22)',
                                'rgb(234, 179, 8)',
                                'rgb(59, 130, 246)',
                                'rgb(34, 197, 94)'
                            ],
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    color: '#9ca3af',
                                    font: { size: 12 }
                                }
                            }
                        }
                    }
                });

                // Timeline Line Chart
                const timelineCtx = document.getElementById('timelineChart').getContext('2d');
                this.timelineChart = new Chart(timelineCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Risk Score',
                            data: [],
                            borderColor: 'rgb(59, 130, 246)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: {
                                    color: '#9ca3af'
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100,
                                ticks: { color: '#9ca3af' },
                                grid: { color: '#374151' }
                            },
                            x: {
                                ticks: { color: '#9ca3af', maxRotation: 45 },
                                grid: { color: '#374151' }
                            }
                        }
                    }
                });
            },
            updateCharts() {
                if (!this.stats.risk_distribution) return;

                // Update Risk Distribution Chart
                const riskDist = this.stats.risk_distribution;
                this.riskChart.data.datasets[0].data = [
                    riskDist.critical || 0,
                    riskDist.high || 0,
                    riskDist.elevated || 0,
                    riskDist.moderate || 0,
                    riskDist.low || 0
                ];
                this.riskChart.update('none');

                // Update Timeline Chart
                if (this.stats.timeline_data && this.stats.timeline_data.length > 0) {
                    const timeline = this.stats.timeline_data;
                    this.timelineChart.data.labels = timeline.map((_, i) => `E${i+1}`);
                    this.timelineChart.data.datasets[0].data = timeline.map(e => e.risk_score);
                    this.timelineChart.update('none');
                }
            },
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

                    const geometry = new THREE.SphereGeometry(2, 64, 64);
                    const material = new THREE.MeshPhongMaterial({
                        color: 0x2233ff,
                        emissive: 0x112244,
                        shininess: 10
                    });
                    this.globe = new THREE.Mesh(geometry, material);
                    this.scene.add(this.globe);

                    const ambient = new THREE.AmbientLight(0x404040, 2);
                    this.scene.add(ambient);

                    const directional = new THREE.DirectionalLight(0xffffff, 1);
                    directional.position.set(5, 3, 5);
                    this.scene.add(directional);

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
                    }, 8000);
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
                    this.showToast('success', 'Connected!', 'WebSocket connection established');
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
                            this.addThreatMarker(msg.data.latitude, msg.data.longitude, msg.data.risk_level);
                        }

                        if (msg.data.risk_level === 'critical') {
                            this.showToast('danger', 'Critical Threat!', `${msg.data.user_identifier} - Score: ${msg.data.risk_score}`);
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
                this.showToast('info', 'Attack Simulation', `Triggering ${type.replace('_', ' ')}...`);

                try {
                    const res = await fetch(`/api/attack/${type}`, { method: 'POST' });
                    const data = await res.json();

                    setTimeout(() => {
                        this.attackInProgress = false;
                        this.showToast('success', 'Attack Complete', data.message);
                    }, 3000);
                } catch (e) {
                    this.attackInProgress = false;
                    this.showToast('danger', 'Error', 'Attack simulation failed');
                }
            },
            getEventClass(event) {
                const base = 'border-l-4';
                if (event.risk_level === 'critical') return base + ' bg-red-900/20 border-red-500';
                if (event.risk_level === 'high') return base + ' bg-orange-900/20 border-orange-500';
                if (event.risk_level === 'elevated') return base + ' bg-yellow-900/20 border-yellow-500';
                if (event.risk_level === 'moderate') return base + ' bg-blue-900/20 border-blue-500';
                return base + ' bg-gray-700/20 border-green-500';
            },
            getRiskColor(score) {
                if (score >= 80) return 'text-red-400';
                if (score >= 60) return 'text-orange-400';
                if (score >= 40) return 'text-yellow-400';
                if (score >= 20) return 'text-blue-400';
                return 'text-green-400';
            },
            showToast(type, title, message) {
                const id = Date.now();
                this.toasts.push({ id, type, title, message });
                setTimeout(() => this.removeToast(id), 5000);
            },
            removeToast(id) {
                this.toasts = this.toasts.filter(t => t.id !== id);
            },
            getToastClass(type) {
                if (type === 'danger') return 'border-red-500';
                if (type === 'warning') return 'border-orange-500';
                if (type === 'success') return 'border-green-500';
                return 'border-blue-500';
            },
            getToastIcon(type) {
                if (type === 'danger') return '🚨';
                if (type === 'warning') return '⚠️';
                if (type === 'success') return '✅';
                return '💡';
            }
        }
    }).mount('#app');
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🚀 SMART LOGIN GUARDIAN - Analytics Dashboard with Graphs")
    print("="*70)
    print("🌐 URL: http://localhost:8080")
    print("📊 Features: Real-time charts, statistics, ML visualization")
    print("📈 Charts: Risk distribution, Timeline, Numbers")
    print("="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
