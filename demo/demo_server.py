#!/usr/bin/env python3
"""
Smart Login Guardian - Quick Demo
A minimal working demo showcasing enterprise features
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import uvicorn
import random
import math

app = FastAPI(
    title="Smart Login Guardian - Demo",
    description="Enterprise Identity Threat Detection Platform",
    version="1.0.0-demo"
)

# CORS middleware
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
    user_identifier: str = Field(..., description="Email or username")
    ip_address: str
    country: Optional[str] = "Unknown"
    city: Optional[str] = "Unknown"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_type: Optional[str] = "desktop"
    browser: Optional[str] = "Chrome"
    os: Optional[str] = "Windows"
    authentication_method: str = "password"
    status: str = Field(..., description="success or failed")
    mfa_status: Optional[str] = "not_required"
    timestamp: Optional[datetime] = None

class RiskSignal(BaseModel):
    type: str
    value: int
    weight: int
    description: str

class RiskAssessment(BaseModel):
    event_id: str
    risk_score: int
    risk_level: str
    signals: List[RiskSignal]
    explanation: str
    recommended_action: str

class Detection(BaseModel):
    detection_id: str
    detector_type: str
    severity: str
    title: str
    description: str
    confidence: float
    evidence: Dict[str, Any]

# =====================================================
# In-Memory Storage (Demo Only)
# =====================================================

events_store: List[Dict[str, Any]] = []
risk_assessments_store: List[Dict[str, Any]] = []
detections_store: List[Detection] = []
user_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
ip_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

# Known malicious IPs for demo
MALICIOUS_IPS = {
    "203.0.113.50": "Known brute force attacker",
    "198.51.100.200": "Tor exit node",
    "192.0.2.100": "VPN/Proxy",
}

# =====================================================
# Risk Scoring Engine
# =====================================================

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in km"""
    R = 6371  # Earth's radius in km

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c

def analyze_risk(event: AuthEvent) -> RiskAssessment:
    """Analyze authentication event and calculate risk score"""
    signals = []
    total_score = 0

    # Check IP reputation
    if event.ip_address in MALICIOUS_IPS:
        signal = RiskSignal(
            type="malicious_ip",
            value=30,
            weight=30,
            description=f"IP address {event.ip_address}: {MALICIOUS_IPS[event.ip_address]}"
        )
        signals.append(signal)
        total_score += signal.value

    # Check for failed login attempts
    if event.status == "failed":
        recent_failures = [
            e for e in user_history[event.user_identifier]
            if e["status"] == "failed" and
            (datetime.now() - datetime.fromisoformat(e["timestamp"])).seconds < 300
        ]

        if len(recent_failures) >= 3:
            signal = RiskSignal(
                type="brute_force",
                value=25,
                weight=25,
                description=f"{len(recent_failures) + 1} failed attempts in 5 minutes"
            )
            signals.append(signal)
            total_score += signal.value

    # Check for new country
    user_countries = set([e.get("country") for e in user_history[event.user_identifier]])
    if event.country and event.country not in user_countries and len(user_countries) > 0:
        signal = RiskSignal(
            type="new_country",
            value=20,
            weight=20,
            description=f"First login from {event.country}"
        )
        signals.append(signal)
        total_score += signal.value

    # Check for impossible travel
    if event.latitude and event.longitude and user_history[event.user_identifier]:
        last_event = user_history[event.user_identifier][-1]
        if last_event.get("latitude") and last_event.get("longitude"):
            distance = calculate_distance(
                last_event["latitude"], last_event["longitude"],
                event.latitude, event.longitude
            )
            time_diff = (datetime.now() - datetime.fromisoformat(last_event["timestamp"])).seconds / 3600

            if time_diff > 0:
                speed = distance / time_diff
                if speed > 800:  # Faster than commercial flight
                    signal = RiskSignal(
                        type="impossible_travel",
                        value=35,
                        weight=35,
                        description=f"Travelled {distance:.0f}km in {time_diff:.1f}h (speed: {speed:.0f}km/h)"
                    )
                    signals.append(signal)
                    total_score += signal.value

    # Check for unusual time
    current_hour = datetime.now().hour
    if current_hour < 6 or current_hour > 22:
        signal = RiskSignal(
            type="unusual_time",
            value=10,
            weight=10,
            description=f"Login at unusual hour: {current_hour}:00"
        )
        signals.append(signal)
        total_score += signal.value

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

    # Generate explanation
    if total_score > 50:
        explanation = f"This login is highly suspicious ({total_score}/100 risk score). "
        explanation += "Key concerns: " + ", ".join([s.description for s in signals[:3]])
    elif total_score > 0:
        explanation = f"This login shows some risk indicators ({total_score}/100). "
        explanation += "Detected: " + ", ".join([s.type.replace('_', ' ') for s in signals])
    else:
        explanation = "This login appears normal with no significant risk indicators detected."

    # Recommended action
    if risk_level in ["critical", "high"]:
        recommended_action = "Block login and require additional verification (MFA, security questions)"
    elif risk_level == "elevated":
        recommended_action = "Allow with MFA challenge and notify security team"
    elif risk_level == "moderate":
        recommended_action = "Allow but log for monitoring"
    else:
        recommended_action = "Allow login"

    return RiskAssessment(
        event_id=f"evt_{len(events_store) + 1}",
        risk_score=min(100, total_score),
        risk_level=risk_level,
        signals=signals,
        explanation=explanation,
        recommended_action=recommended_action
    )

# =====================================================
# API Endpoints
# =====================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the demo dashboard"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Smart Login Guardian - Enterprise Demo</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body class="bg-gray-50">
        <div id="app" class="min-h-screen">
            <!-- Header -->
            <header class="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
                <div class="container mx-auto px-6 py-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <h1 class="text-3xl font-bold">🛡️ Smart Login Guardian</h1>
                            <p class="text-blue-100 mt-1">Enterprise Identity Threat Detection Platform</p>
                        </div>
                        <div class="text-right">
                            <div class="text-sm text-blue-100">Live Demo</div>
                            <div class="text-xl font-semibold">{{ stats.total_events }} Events Analyzed</div>
                        </div>
                    </div>
                </div>
            </header>

            <!-- Stats Dashboard -->
            <div class="container mx-auto px-6 py-8">
                <!-- Quick Stats -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <div class="text-gray-500 text-sm font-medium">Total Logins</div>
                        <div class="text-3xl font-bold text-gray-800 mt-2">{{ stats.total_events }}</div>
                        <div class="text-green-600 text-sm mt-1">↑ Real-time</div>
                    </div>
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <div class="text-gray-500 text-sm font-medium">High Risk</div>
                        <div class="text-3xl font-bold text-red-600 mt-2">{{ stats.high_risk }}</div>
                        <div class="text-red-600 text-sm mt-1">Requires attention</div>
                    </div>
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <div class="text-gray-500 text-sm font-medium">Detections</div>
                        <div class="text-3xl font-bold text-orange-600 mt-2">{{ stats.detections }}</div>
                        <div class="text-orange-600 text-sm mt-1">Active threats</div>
                    </div>
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <div class="text-gray-500 text-sm font-medium">Success Rate</div>
                        <div class="text-3xl font-bold text-green-600 mt-2">{{ stats.success_rate }}%</div>
                        <div class="text-green-600 text-sm mt-1">Authentication success</div>
                    </div>
                </div>

                <!-- Test Event Form -->
                <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                    <h2 class="text-xl font-bold text-gray-800 mb-4">🧪 Test Authentication Event</h2>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">User Email</label>
                            <input v-model="testEvent.user_identifier" type="email"
                                   class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                   placeholder="user@example.com">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">IP Address</label>
                            <input v-model="testEvent.ip_address" type="text"
                                   class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                   placeholder="192.168.1.1">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Country</label>
                            <input v-model="testEvent.country" type="text"
                                   class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                   placeholder="India">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">City</label>
                            <input v-model="testEvent.city" type="text"
                                   class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                   placeholder="Pune">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
                            <select v-model="testEvent.status"
                                    class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
                                <option value="success">Success</option>
                                <option value="failed">Failed</option>
                            </select>
                        </div>
                        <div class="flex items-end">
                            <button @click="testLogin"
                                    class="w-full bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 font-medium">
                                Analyze Login
                            </button>
                        </div>
                    </div>

                    <!-- Quick Test Scenarios -->
                    <div class="mt-4 flex gap-2 flex-wrap">
                        <button @click="simulateScenario('normal')"
                                class="px-4 py-2 bg-green-100 text-green-700 rounded-lg text-sm hover:bg-green-200">
                            ✓ Normal Login
                        </button>
                        <button @click="simulateScenario('brute_force')"
                                class="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm hover:bg-red-200">
                            ⚠️ Brute Force Attack
                        </button>
                        <button @click="simulateScenario('impossible_travel')"
                                class="px-4 py-2 bg-orange-100 text-orange-700 rounded-lg text-sm hover:bg-orange-200">
                            ✈️ Impossible Travel
                        </button>
                        <button @click="simulateScenario('malicious_ip')"
                                class="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg text-sm hover:bg-purple-200">
                            🚫 Malicious IP
                        </button>
                    </div>
                </div>

                <!-- Recent Events -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-bold text-gray-800 mb-4">📊 Recent Authentication Events</h2>
                    <div class="overflow-x-auto">
                        <table class="w-full">
                            <thead class="bg-gray-50 border-b">
                                <tr>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-200">
                                <tr v-for="event in recentEvents" :key="event.event_id"
                                    :class="getRiskRowClass(event.risk_level)">
                                    <td class="px-4 py-3 text-sm">{{ formatTime(event.timestamp) }}</td>
                                    <td class="px-4 py-3 text-sm font-medium">{{ event.user_identifier }}</td>
                                    <td class="px-4 py-3 text-sm font-mono">{{ event.ip_address }}</td>
                                    <td class="px-4 py-3 text-sm">{{ event.city }}, {{ event.country }}</td>
                                    <td class="px-4 py-3 text-sm">
                                        <span :class="event.status === 'success' ? 'text-green-600' : 'text-red-600'">
                                            {{ event.status }}
                                        </span>
                                    </td>
                                    <td class="px-4 py-3 text-sm">
                                        <span :class="getRiskBadgeClass(event.risk_level)"
                                              class="px-2 py-1 rounded-full text-xs font-medium">
                                            {{ event.risk_level }}
                                        </span>
                                    </td>
                                    <td class="px-4 py-3 text-sm font-bold">
                                        <span :class="getRiskScoreClass(event.risk_score)">
                                            {{ event.risk_score }}/100
                                        </span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <script>
        const { createApp } = Vue;

        createApp({
            data() {
                return {
                    stats: {
                        total_events: 0,
                        high_risk: 0,
                        detections: 0,
                        success_rate: 0
                    },
                    recentEvents: [],
                    testEvent: {
                        user_identifier: 'demo@company.com',
                        ip_address: '192.168.1.100',
                        country: 'India',
                        city: 'Pune',
                        status: 'success'
                    }
                }
            },
            mounted() {
                this.loadStats();
                this.loadRecentEvents();
                setInterval(() => this.loadStats(), 3000);
                setInterval(() => this.loadRecentEvents(), 3000);
            },
            methods: {
                async loadStats() {
                    const response = await fetch('/api/stats');
                    this.stats = await response.json();
                },
                async loadRecentEvents() {
                    const response = await fetch('/api/events/recent');
                    this.recentEvents = await response.json();
                },
                async testLogin() {
                    const response = await fetch('/api/events/analyze', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(this.testEvent)
                    });
                    const result = await response.json();
                    await this.loadStats();
                    await this.loadRecentEvents();

                    alert(`Risk Assessment\\n\\nRisk Score: ${result.risk_score}/100\\nRisk Level: ${result.risk_level}\\n\\n${result.explanation}\\n\\nRecommendation: ${result.recommended_action}`);
                },
                async simulateScenario(scenario) {
                    const response = await fetch(`/api/simulate/${scenario}`, {method: 'POST'});
                    await this.loadStats();
                    await this.loadRecentEvents();
                },
                getRiskBadgeClass(level) {
                    const classes = {
                        'critical': 'bg-red-100 text-red-800',
                        'high': 'bg-orange-100 text-orange-800',
                        'elevated': 'bg-yellow-100 text-yellow-800',
                        'moderate': 'bg-blue-100 text-blue-800',
                        'low': 'bg-green-100 text-green-800'
                    };
                    return classes[level] || 'bg-gray-100 text-gray-800';
                },
                getRiskRowClass(level) {
                    if (level === 'critical') return 'bg-red-50';
                    if (level === 'high') return 'bg-orange-50';
                    return '';
                },
                getRiskScoreClass(score) {
                    if (score >= 80) return 'text-red-600';
                    if (score >= 60) return 'text-orange-600';
                    if (score >= 40) return 'text-yellow-600';
                    return 'text-green-600';
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

@app.post("/api/events/analyze")
async def analyze_event(event: AuthEvent):
    """Analyze an authentication event"""
    if not event.timestamp:
        event.timestamp = datetime.now()

    # Analyze risk
    assessment = analyze_risk(event)

    # Store event
    event_data = event.dict()
    event_data["timestamp"] = event.timestamp.isoformat()
    event_data["event_id"] = assessment.event_id
    event_data["risk_score"] = assessment.risk_score
    event_data["risk_level"] = assessment.risk_level

    events_store.append(event_data)
    user_history[event.user_identifier].append(event_data)
    ip_history[event.ip_address].append(event_data)

    # Store assessment
    assessment_data = assessment.dict()
    risk_assessments_store.append(assessment_data)

    return assessment

@app.get("/api/events/recent")
async def get_recent_events():
    """Get recent authentication events"""
    return events_store[-20:][::-1]

@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics"""
    total = len(events_store)
    high_risk = len([e for e in events_store if e.get("risk_level") in ["high", "critical"]])
    successful = len([e for e in events_store if e.get("status") == "success"])

    return {
        "total_events": total,
        "high_risk": high_risk,
        "detections": len(detections_store),
        "success_rate": round((successful / total * 100) if total > 0 else 0, 1)
    }

@app.post("/api/simulate/{scenario}")
async def simulate_scenario(scenario: str):
    """Simulate different attack scenarios"""

    if scenario == "normal":
        event = AuthEvent(
            user_identifier="alice@company.com",
            ip_address="192.168.1.10",
            country="India",
            city="Pune",
            latitude=18.5204,
            longitude=73.8567,
            status="success"
        )
        await analyze_event(event)

    elif scenario == "brute_force":
        for i in range(5):
            event = AuthEvent(
                user_identifier="admin@company.com",
                ip_address="203.0.113.50",
                country="Unknown",
                city="Unknown",
                status="failed"
            )
            await analyze_event(event)

    elif scenario == "impossible_travel":
        # Login from India
        event1 = AuthEvent(
            user_identifier="bob@company.com",
            ip_address="203.0.113.10",
            country="India",
            city="Mumbai",
            latitude=19.0760,
            longitude=72.8777,
            status="success"
        )
        await analyze_event(event1)

        # Login from USA 5 minutes later
        event2 = AuthEvent(
            user_identifier="bob@company.com",
            ip_address="198.51.100.25",
            country="USA",
            city="New York",
            latitude=40.7128,
            longitude=-74.0060,
            status="success"
        )
        await analyze_event(event2)

    elif scenario == "malicious_ip":
        event = AuthEvent(
            user_identifier="victim@company.com",
            ip_address="198.51.100.200",
            country="Russia",
            city="Moscow",
            status="success"
        )
        await analyze_event(event)

    return {"message": f"Simulated {scenario} scenario"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Smart Login Guardian Demo",
        "version": "1.0.0-demo",
        "events_analyzed": len(events_store)
    }

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║         SMART LOGIN GUARDIAN - ENTERPRISE DEMO                    ║
    ╚══════════════════════════════════════════════════════════════════╝

    🌐 Dashboard: http://localhost:8080
    📡 API Docs:  http://localhost:8080/docs
    🔒 Status:    Active

    Starting demo server...
    """)

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
