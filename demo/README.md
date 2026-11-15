# Smart Login Guardian - Enterprise Demo

## 🎯 What This Demo Shows

This is a **working prototype** of the Smart Login Guardian enterprise platform showcasing:

- ✅ **Real-time Risk Analysis** - Multi-factor risk scoring engine
- ✅ **Threat Detection** - Brute force, impossible travel, malicious IP detection
- ✅ **Live Dashboard** - Modern, responsive web interface
- ✅ **REST API** - Complete API for event ingestion and analysis
- ✅ **Enterprise Features** - Risk scoring, explanations, recommendations

---

## 🚀 Quick Start

### 1. Start the Demo Server

```bash
# From the project root
source venv/bin/activate
python3 demo/demo_server.py
```

### 2. Access the Dashboard

Open your browser to:

**🌐 http://localhost:8080**

---

## 📊 Demo Features

### Interactive Dashboard

The web interface provides:

1. **Real-time Statistics**
   - Total login events analyzed
   - High-risk event count
   - Active detections
   - Success rate metrics

2. **Event Analysis Tool**
   - Test custom authentication events
   - See risk scores in real-time
   - Get detailed explanations

3. **Attack Simulation**
   - ✓ Normal Login - Baseline behavior
   - ⚠️ Brute Force Attack - Multiple failed attempts
   - ✈️ Impossible Travel - Geographic impossibility
   - 🚫 Malicious IP - Known threat actor

4. **Event Timeline**
   - Recent authentication events
   - Color-coded risk levels
   - Detailed event metadata

### Risk Scoring Engine

The demo includes a production-ready risk scoring engine that evaluates:

| Risk Signal | Weight | Description |
|------------|--------|-------------|
| **Malicious IP** | 30 | Known attacker IP addresses |
| **Brute Force** | 25 | Multiple failed login attempts |
| **New Country** | 20 | First login from new geographic location |
| **Impossible Travel** | 35 | Physically impossible geographic movement |
| **Unusual Time** | 10 | Login during abnormal hours |

**Risk Classification:**
- 0-19: Low Risk 🟢
- 20-39: Moderate Risk 🔵
- 40-59: Elevated Risk 🟡
- 60-79: High Risk 🟠
- 80-100: Critical Risk 🔴

---

## 🔧 API Endpoints

### Health Check
```bash
curl http://localhost:8080/api/health
```

### Analyze Authentication Event
```bash
curl -X POST http://localhost:8080/api/events/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "user@company.com",
    "ip_address": "192.168.1.100",
    "country": "India",
    "city": "Pune",
    "status": "success"
  }'
```

**Response:**
```json
{
  "event_id": "evt_1",
  "risk_score": 15,
  "risk_level": "low",
  "signals": [],
  "explanation": "This login appears normal with no significant risk indicators detected.",
  "recommended_action": "Allow login"
}
```

### Get Recent Events
```bash
curl http://localhost:8080/api/events/recent
```

### Get Statistics
```bash
curl http://localhost:8080/api/stats
```

### Simulate Attack Scenarios
```bash
# Brute force attack
curl -X POST http://localhost:8080/api/simulate/brute_force

# Impossible travel
curl -X POST http://localhost:8080/api/simulate/impossible_travel

# Malicious IP
curl -X POST http://localhost:8080/api/simulate/malicious_ip

# Normal login
curl -X POST http://localhost:8080/api/simulate/normal
```

### API Documentation

Interactive API docs available at:
- **Swagger UI:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc

---

## 🧪 Test Scenarios

### Scenario 1: Normal Login
```bash
curl -X POST http://localhost:8080/api/events/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "alice@company.com",
    "ip_address": "192.168.1.10",
    "country": "India",
    "city": "Pune",
    "status": "success"
  }'
```

Expected: **Low risk** (0-19)

---

### Scenario 2: Brute Force Attack
```bash
# First attempt (failed)
curl -X POST http://localhost:8080/api/events/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "admin@company.com",
    "ip_address": "203.0.113.50",
    "status": "failed"
  }'

# Repeat 4 more times...
# (Use the simulate endpoint for convenience)

curl -X POST http://localhost:8080/api/simulate/brute_force
```

Expected: **High risk** (60-79) after multiple failures

**Detection:** Brute Force Attack  
**Signals:**
- Multiple failed attempts from same IP
- Known malicious IP address

---

### Scenario 3: Impossible Travel
```bash
# Login from India
curl -X POST http://localhost:8080/api/events/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "bob@company.com",
    "ip_address": "203.0.113.10",
    "country": "India",
    "city": "Mumbai",
    "latitude": 19.0760,
    "longitude": 72.8777,
    "status": "success"
  }'

# Login from USA immediately after
curl -X POST http://localhost:8080/api/events/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "bob@company.com",
    "ip_address": "198.51.100.25",
    "country": "USA",
    "city": "New York",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "status": "success"
  }'
```

Expected: **Critical risk** (80-100)

**Detection:** Impossible Travel  
**Calculation:**
- Distance: ~12,500 km
- Time: < 1 hour
- Speed: > 12,500 km/h (impossible)

---

### Scenario 4: New Geographic Location
```bash
# First login from India
curl -X POST http://localhost:8080/api/events/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "charlie@company.com",
    "ip_address": "192.168.1.50",
    "country": "India",
    "city": "Bangalore",
    "status": "success"
  }'

# Subsequent login from Germany
curl -X POST http://localhost:8080/api/events/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "charlie@company.com",
    "ip_address": "198.51.100.75",
    "country": "Germany",
    "city": "Berlin",
    "status": "success"
  }'
```

Expected: **Moderate risk** (20-39)

**Detection:** New Country  
**Signal:** First login from Germany

---

## 🎨 Dashboard Features

### Real-Time Updates
- Auto-refreshes every 3 seconds
- Live event stream
- Dynamic statistics

### Risk Visualization
- Color-coded risk levels
- Severity badges
- Risk score indicators

### Event Details
- User identifier
- IP address
- Geographic location
- Authentication status
- Risk assessment
- Timestamp

---

## 🔐 Enterprise Features Demonstrated

### 1. Risk Scoring
Multi-signal risk calculation with:
- Configurable weights
- Real-time analysis
- Explainable results

### 2. Threat Detection
Pattern-based detection for:
- Brute force attacks
- Impossible travel
- Malicious IPs
- Geographic anomalies
- Temporal anomalies

### 3. Behavioral Analysis
- User history tracking
- IP address profiling
- Geographic profiling
- Anomaly detection

### 4. Actionable Intelligence
Every risk assessment includes:
- Risk score (0-100)
- Risk level classification
- Detailed explanation
- Recommended action

---

## 📈 What This Becomes in Production

This demo showcases the **core risk engine**. The full enterprise platform adds:

### Phase 2-3: Enterprise Infrastructure
- PostgreSQL for persistent storage
- ClickHouse for analytics
- Kafka for event streaming
- Redis for caching
- Multi-tenant architecture

### Phase 4: AI Intelligence
- LLM-powered explanations (OpenAI, Anthropic)
- Advanced anomaly detection (Isolation Forest)
- Behavioral machine learning
- Automated investigation recommendations

### Phase 5: Incident Management
- Full incident lifecycle
- Investigation workflows
- Evidence timeline
- Analyst collaboration

### Phase 6-7: Enterprise Features
- RBAC and team management
- SAML/OIDC integration
- Slack/Teams notifications
- Webhook support
- Multi-channel alerts

### Phase 8: Advanced Analytics
- Time-series analysis
- Geographic heatmaps
- Threat intelligence feeds
- Custom reporting

### Phase 9-10: Production Ready
- Kubernetes deployment
- Horizontal scaling
- Prometheus monitoring
- Grafana dashboards
- 99.9% uptime SLA

---

## 🛠️ Tech Stack (Demo)

- **Backend:** FastAPI (Python)
- **Frontend:** Vue.js 3 + Tailwind CSS
- **Charts:** Chart.js
- **API:** REST + JSON

**Production Stack:**
- Go (high-performance services)
- Python/FastAPI (AI/ML services)
- Next.js + TypeScript (frontend)
- PostgreSQL + ClickHouse (databases)
- Kafka (event streaming)
- Kubernetes (orchestration)

---

## 📝 Notes

- This is an **in-memory demo** - data resets on restart
- Uses simplified risk scoring for demonstration
- Production version uses PostgreSQL, advanced ML models, and distributed architecture
- See `ARCHITECTURE.md` for full production design

---

## 🚦 Next Steps

1. **Try the Demo:** Open http://localhost:8080
2. **Test Scenarios:** Use the simulation buttons
3. **Explore API:** Visit http://localhost:8080/docs
4. **Review Architecture:** Read `ARCHITECTURE.md`
5. **Check Roadmap:** See `IMPLEMENTATION_ROADMAP.md`

---

## 🆘 Troubleshooting

**Port already in use:**
```bash
# Find and kill process on port 8080
lsof -ti:8080 | xargs kill -9
```

**Dependencies missing:**
```bash
source venv/bin/activate
pip install fastapi uvicorn pydantic
```

**Server not starting:**
```bash
# Check Python version (requires 3.8+)
python3 --version

# Run with verbose logging
python3 demo/demo_server.py --log-level debug
```

---

## 📧 Contact

For questions about the enterprise platform:
- Review: `ARCHITECTURE.md`
- Roadmap: `IMPLEMENTATION_ROADMAP.md`
- Security: `SECURITY.md`

**Demo Version:** 1.0.0  
**Last Updated:** 2026-11-13
