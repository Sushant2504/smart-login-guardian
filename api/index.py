#!/usr/bin/env python3
"""
Smart Login Guardian - Vercel Deployment Version
Serverless API with static dashboard
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict
from datetime import datetime
from collections import defaultdict, Counter
import random
import numpy as np
from sklearn.ensemble import IsolationForest
from mangum import Mangum

# Initialize FastAPI
app = FastAPI(title="Smart Login Guardian", version="5.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (will reset on serverless function cold starts)
events_store: List[Dict] = []
alerts_store: List[Dict] = []
user_history: Dict[str, List[Dict]] = defaultdict(list)

# ML Model
class SimpleMLDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
        self.trained = False
        self.feature_buffer = []
        self.training_events_needed = 30
        self.total_processed = 0
        self.anomalies_detected = 0

    def extract_features(self, event, history):
        hour = datetime.now().hour / 24.0
        day = datetime.now().weekday() / 7.0
        freq = min(len(history) / 10.0, 1.0) if history else 0.0
        failures = sum(1 for e in history[-10:] if e.get('status') == 'failed') / 10.0 if history else 0.0
        return np.array([[hour, day, freq, failures]])

    def predict(self, event, history):
        features = self.extract_features(event, history)
        self.total_processed += 1

        if not self.trained:
            self.feature_buffer.append(features[0])
            if len(self.feature_buffer) >= self.training_events_needed:
                X = np.array(self.feature_buffer)
                self.model.fit(X)
                self.trained = True
            return {"anomaly": False, "score": 0, "status": "training", "features": features[0].tolist()}

        pred = self.model.predict(features)[0]
        score_samples = self.model.score_samples(features)[0]
        anomaly_score = max(0, min(100, int((-score_samples) * 20)))

        is_anomaly = pred == -1
        if is_anomaly:
            self.anomalies_detected += 1

        return {
            "anomaly": is_anomaly,
            "score": anomaly_score,
            "status": "active",
            "features": features[0].tolist()
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
]

USERS = ["alice@company.com", "bob@company.com", "admin@company.com", "ceo@company.com"]

MALICIOUS_IPS = {
    "203.0.113.50": "Botnet C&C Server",
    "198.51.100.200": "Tor Exit Node",
}

def analyze_risk(event, history, ml_result):
    signals = []
    score = 0

    if event['ip_address'] in MALICIOUS_IPS:
        threat_type = MALICIOUS_IPS[event['ip_address']]
        signals.append(f"🚨 Known threat: {threat_type}")
        score += 30

    if event['status'] == 'failed':
        signals.append("❌ Failed login attempt")
        score += 15

    recent_failures = [e for e in history[-10:] if e.get('status') == 'failed']
    if len(recent_failures) >= 3:
        signals.append(f"🔨 Brute force pattern ({len(recent_failures)} failures)")
        score += 25

    user_countries = set(e.get('country') for e in history[-20:] if e.get('country'))
    if event['country'] not in user_countries and len(user_countries) > 0:
        signals.append(f"🌍 New country: {event['country']}")
        score += 20

    if event['country'] in ['Russia', 'China']:
        signals.append(f"⚠️ High-risk region: {event['country']}")
        score += 15

    if ml_result['status'] == 'active':
        if ml_result['anomaly']:
            signals.append(f"🤖 ML Anomaly Detected (score: {ml_result['score']})")
            score += ml_result['score']

    final_score = min(100, score)

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

    return {"score": final_score, "severity": severity, "signals": signals, "ml_result": ml_result}

def process_event(event_data):
    user = event_data.get('user_identifier')
    history = user_history[user]

    ml_result = ml_detector.predict(event_data, history)
    risk_analysis = analyze_risk(event_data, history, ml_result)

    event = {
        **event_data,
        'event_id': len(events_store) + 1,
        'timestamp': datetime.now().isoformat(),
        'risk_score': risk_analysis['score'],
        'risk_level': risk_analysis['severity'],
        'signals': risk_analysis['signals'],
        'ml_status': ml_result['status'],
        'ml_anomaly': ml_result['anomaly'],
        'ml_score': ml_result['score']
    }

    events_store.append(event)
    user_history[user].append(event)

    if risk_analysis['severity'] in ['high', 'critical']:
        alert = {
            'title': f"{risk_analysis['severity'].upper()} Risk Login Detected",
            'user': user,
            'score': risk_analysis['score'],
            'timestamp': event['timestamp']
        }
        alerts_store.append(alert)

    return event

# API Endpoints
@app.get("/")
async def root():
    """Serve the dashboard HTML"""
    return HTMLResponse(HTML_CONTENT)

@app.get("/api/stats")
async def get_stats():
    """Get comprehensive statistics"""
    total_events = len(events_store)
    critical_count = len([e for e in events_store if e.get('risk_level') == 'critical'])
    high_count = len([e for e in events_store if e.get('risk_level') == 'high'])
    elevated_count = len([e for e in events_store if e.get('risk_level') == 'elevated'])
    moderate_count = len([e for e in events_store if e.get('risk_level') == 'moderate'])
    low_count = len([e for e in events_store if e.get('risk_level') == 'low'])

    success_count = len([e for e in events_store if e.get('status') == 'success'])
    failed_count = len([e for e in events_store if e.get('status') == 'failed'])

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
        "ml_status": "active" if ml_detector.trained else "training",
        "ml_processed": ml_detector.total_processed,
        "ml_anomalies": ml_detector.anomalies_detected,
        "ml_training_progress": min(100, int((len(ml_detector.feature_buffer) / 30) * 100)),
        "recent_events": events_store[-20:],
        "risk_distribution": {
            "critical": critical_count,
            "high": high_count,
            "elevated": elevated_count,
            "moderate": moderate_count,
            "low": low_count
        }
    }

@app.post("/api/generate-event")
async def generate_event():
    """Generate a single authentication event"""
    user = random.choice(USERS)
    loc = random.choice(LOCATIONS)
    status = "success" if random.random() > 0.1 else "failed"

    if random.random() > 0.95:
        ip = random.choice(list(MALICIOUS_IPS.keys()))
    else:
        ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

    event_data = {
        "user_identifier": user,
        "ip_address": ip,
        "country": loc['country'],
        "city": loc['city'],
        "latitude": loc['lat'],
        "longitude": loc['lon'],
        "status": status,
        "device": random.choice(["iPhone 15", "MacBook Pro", "Windows PC"]),
        "browser": random.choice(["Chrome 120", "Safari 17", "Firefox 121"])
    }

    event = process_event(event_data)
    return JSONResponse(event)

@app.post("/api/attack/brute_force")
async def trigger_brute_force():
    """Simulate brute force attack"""
    events = []
    for i in range(6):
        event_data = {
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
        event = process_event(event_data)
        events.append(event)

    return {"message": "Brute force attack simulated", "events": events}

# HTML Content (Simplified for Vercel)
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Login Guardian - Live on Vercel</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        .pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
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
        }
    </style>
</head>
<body class="bg-gray-900 text-white">
    <div id="app" class="container mx-auto p-4">
        <div class="mb-6 bg-gradient-to-r from-blue-900 to-purple-900 rounded-lg p-6 shadow-2xl">
            <h1 class="text-3xl font-bold mb-2">🛡️ Smart Login Guardian</h1>
            <p class="text-blue-200">Deployed on Vercel - Enterprise Threat Detection</p>
        </div>

        <div class="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="stat-card rounded-lg p-4">
                <div class="text-gray-400 text-sm mb-1">Total Events</div>
                <div class="number-big text-blue-400">{{ stats.total_events || 0 }}</div>
            </div>
            <div class="stat-card rounded-lg p-4">
                <div class="text-gray-400 text-sm mb-1">Critical Alerts</div>
                <div class="number-big text-red-400">{{ stats.critical_alerts || 0 }}</div>
            </div>
            <div class="stat-card rounded-lg p-4">
                <div class="text-gray-400 text-sm mb-1">Success Rate</div>
                <div class="number-big text-green-400">{{ stats.success_rate || 0 }}%</div>
            </div>
            <div class="stat-card rounded-lg p-4">
                <div class="text-gray-400 text-sm mb-1">ML Status</div>
                <div class="number-big text-purple-400 text-xl">{{ stats.ml_status }}</div>
            </div>
        </div>

        <div class="mb-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <h3 class="text-lg font-bold mb-4">📊 Risk Distribution</h3>
                <canvas id="riskChart" height="250"></canvas>
            </div>
            <div class="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <h3 class="text-lg font-bold mb-4">📋 Recent Events</h3>
                <div class="space-y-2 max-h-64 overflow-y-auto">
                    <div v-for="event in recentEvents.slice(0, 5)" :key="event.event_id"
                         class="p-3 rounded border-l-4" :class="getEventClass(event)">
                        <div class="flex justify-between">
                            <div>
                                <div class="font-mono text-sm">{{ event.user_identifier }}</div>
                                <div class="text-xs text-gray-400">{{ event.city }}, {{ event.country }}</div>
                            </div>
                            <div class="text-2xl font-bold" :class="getRiskColor(event.risk_score)">
                                {{ event.risk_score }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button @click="generateEvent"
                    class="px-6 py-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-bold text-lg">
                Generate Event
            </button>
            <button @click="triggerAttack"
                    class="px-6 py-4 bg-red-600 hover:bg-red-700 rounded-lg font-bold text-lg">
                🔨 Simulate Attack
            </button>
            <button @click="loadStats"
                    class="px-6 py-4 bg-green-600 hover:bg-green-700 rounded-lg font-bold text-lg">
                🔄 Refresh
            </button>
        </div>
    </div>

    <script>
    const { createApp } = Vue;

    createApp({
        data() {
            return {
                stats: {},
                recentEvents: [],
                riskChart: null
            }
        },
        mounted() {
            this.loadStats();
            this.initCharts();
            setInterval(this.loadStats, 5000);
        },
        methods: {
            async loadStats() {
                try {
                    const res = await fetch('/api/stats');
                    const data = await res.json();
                    this.stats = data;
                    this.recentEvents = data.recent_events || [];
                    this.updateCharts();
                } catch (e) {
                    console.error('Stats error:', e);
                }
            },
            async generateEvent() {
                await fetch('/api/generate-event', { method: 'POST' });
                await this.loadStats();
            },
            async triggerAttack() {
                await fetch('/api/attack/brute_force', { method: 'POST' });
                setTimeout(() => this.loadStats(), 1000);
            },
            initCharts() {
                const ctx = document.getElementById('riskChart').getContext('2d');
                this.riskChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Critical', 'High', 'Elevated', 'Moderate', 'Low'],
                        datasets: [{
                            data: [0, 0, 0, 0, 0],
                            backgroundColor: ['#ef4444', '#f97316', '#eab308', '#3b82f6', '#22c55e']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: { color: '#9ca3af' }
                            }
                        }
                    }
                });
            },
            updateCharts() {
                if (!this.stats.risk_distribution) return;
                const dist = this.stats.risk_distribution;
                this.riskChart.data.datasets[0].data = [
                    dist.critical || 0,
                    dist.high || 0,
                    dist.elevated || 0,
                    dist.moderate || 0,
                    dist.low || 0
                ];
                this.riskChart.update('none');
            },
            getEventClass(event) {
                const base = 'border-l-4';
                if (event.risk_level === 'critical') return base + ' bg-red-900/20 border-red-500';
                if (event.risk_level === 'high') return base + ' bg-orange-900/20 border-orange-500';
                if (event.risk_level === 'elevated') return base + ' bg-yellow-900/20 border-yellow-500';
                return base + ' bg-gray-700/20 border-green-500';
            },
            getRiskColor(score) {
                if (score >= 80) return 'text-red-400';
                if (score >= 60) return 'text-orange-400';
                if (score >= 40) return 'text-yellow-400';
                return 'text-green-400';
            }
        }
    }).mount('#app');
    </script>
</body>
</html>
"""

# Mangum handler for Vercel
handler = Mangum(app)
