# Smart Login Guardian - Production Architecture

## 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  React + TypeScript Application                          │  │
│  │  - Redux Toolkit (State Management)                      │  │
│  │  - React Router (Navigation)                             │  │
│  │  - Material-UI (Component Library)                       │  │
│  │  - Chart.js + D3.js (Visualizations)                     │  │
│  │  - Socket.IO Client (Real-time)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS/WSS
┌────────────────────────────┴────────────────────────────────────┐
│                      API Gateway / Load Balancer                │
│                      (NGINX / AWS ALB)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                         Backend Layer                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application Server                              │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  API Layer (Routers)                               │ │  │
│  │  │  - /api/v1/auth     (Authentication)               │ │  │
│  │  │  - /api/v1/events   (Event Management)             │ │  │
│  │  │  - /api/v1/alerts   (Alert Management)             │ │  │
│  │  │  - /api/v1/users    (User Management)              │ │  │
│  │  │  - /api/v1/ml       (ML Model Ops)                 │ │  │
│  │  │  - /api/v1/reports  (Reporting)                    │ │  │
│  │  │  - /ws              (WebSocket)                    │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Service Layer (Business Logic)                    │ │  │
│  │  │  - AuthService                                     │ │  │
│  │  │  - EventService                                    │ │  │
│  │  │  - RiskAnalysisService                             │ │  │
│  │  │  - MLDetectionService                              │ │  │
│  │  │  - NotificationService                             │ │  │
│  │  │  - ReportingService                                │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Repository Layer (Data Access)                    │ │  │
│  │  │  - UserRepository                                  │ │  │
│  │  │  - EventRepository                                 │ │  │
│  │  │  - AlertRepository                                 │ │  │
│  │  │  - AnomalyRepository                               │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                       Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  PostgreSQL  │  │    Redis     │  │   ML Model Store     │ │
│  │              │  │              │  │  (S3 / File System)  │ │
│  │  - Users     │  │  - Sessions  │  │                      │ │
│  │  - Events    │  │  - Cache     │  │  - Models (.pkl)     │ │
│  │  - Alerts    │  │  - Queues    │  │  - Metadata          │ │
│  │  - Anomalies │  │  - Rate Lim. │  │  - Versions          │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 **Project Structure**

```
smart-login-guardian/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── config.py               # Configuration management
│   │   ├── database.py             # Database connection
│   │   ├── dependencies.py         # Dependency injection
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── event.py
│   │   │   ├── alert.py
│   │   │   ├── anomaly.py
│   │   │   └── base.py
│   │   │
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── event.py
│   │   │   ├── alert.py
│   │   │   ├── auth.py
│   │   │   └── common.py
│   │   │
│   │   ├── api/                    # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # Route dependencies
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py
│   │   │       ├── events.py
│   │   │       ├── alerts.py
│   │   │       ├── users.py
│   │   │       ├── ml.py
│   │   │       └── reports.py
│   │   │
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── event_service.py
│   │   │   ├── risk_analysis_service.py
│   │   │   ├── ml_detection_service.py
│   │   │   ├── notification_service.py
│   │   │   └── reporting_service.py
│   │   │
│   │   ├── repositories/           # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user_repository.py
│   │   │   ├── event_repository.py
│   │   │   └── alert_repository.py
│   │   │
│   │   ├── core/                   # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── security.py         # JWT, password hashing
│   │   │   ├── cache.py            # Redis cache
│   │   │   ├── logger.py           # Logging config
│   │   │   └── exceptions.py       # Custom exceptions
│   │   │
│   │   ├── ml/                     # ML models
│   │   │   ├── __init__.py
│   │   │   ├── detector.py         # Anomaly detection
│   │   │   ├── features.py         # Feature extraction
│   │   │   ├── trainer.py          # Model training
│   │   │   └── utils.py
│   │   │
│   │   └── utils/                  # Utilities
│   │       ├── __init__.py
│   │       ├── validators.py
│   │       └── helpers.py
│   │
│   ├── alembic/                    # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── tests/                      # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_ml/
│   │
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/             # React components
│   │   │   ├── common/
│   │   │   ├── dashboard/
│   │   │   ├── auth/
│   │   │   └── admin/
│   │   │
│   │   ├── pages/                  # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Events.tsx
│   │   │   └── Admin.tsx
│   │   │
│   │   ├── store/                  # Redux store
│   │   │   ├── index.ts
│   │   │   ├── slices/
│   │   │   └── thunks/
│   │   │
│   │   ├── services/               # API services
│   │   │   ├── api.ts
│   │   │   ├── authService.ts
│   │   │   └── eventService.ts
│   │   │
│   │   ├── hooks/                  # Custom hooks
│   │   ├── utils/                  # Utilities
│   │   ├── types/                  # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── infrastructure/
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.dev.yml
│   │   └── docker-compose.prod.yml
│   │
│   ├── kubernetes/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   │
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       └── security-scan.yml
│
├── docs/
├── scripts/
└── docker-compose.yml
```

## 🔧 **Technology Stack**

### **Backend**
- **Framework**: FastAPI 0.109+
- **ORM**: SQLAlchemy 2.0+
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **ML**: Scikit-learn, NumPy, Pandas
- **Auth**: JWT (PyJWT), bcrypt
- **Validation**: Pydantic 2.0+
- **Migrations**: Alembic
- **Testing**: pytest, pytest-asyncio
- **ASGI Server**: Uvicorn

### **Frontend**
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **State**: Redux Toolkit
- **Routing**: React Router v6
- **UI Library**: Material-UI v5
- **Charts**: Chart.js, D3.js
- **Real-time**: Socket.IO Client
- **HTTP Client**: Axios
- **Testing**: Jest, React Testing Library

### **Infrastructure**
- **Containerization**: Docker, Docker Compose
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack
- **Cloud**: AWS/GCP/Azure
- **IaC**: Terraform

## 🔐 **Security Architecture**

### **Authentication Flow**
```
1. User Login
   ├─> POST /api/v1/auth/login
   ├─> Validate credentials (bcrypt)
   ├─> Generate JWT (access + refresh tokens)
   └─> Return tokens + user info

2. API Request
   ├─> Authorization: Bearer <access_token>
   ├─> Verify JWT signature
   ├─> Check token expiration
   ├─> Extract user claims
   └─> Authorize request

3. Token Refresh
   ├─> POST /api/v1/auth/refresh
   ├─> Verify refresh token
   ├─> Issue new access token
   └─> Return new tokens
```

### **Authorization (RBAC)**
```
Roles:
├─ Admin (Full access)
├─ Analyst (Read + analyze)
├─ Viewer (Read only)
└─ API (Programmatic access)

Permissions:
├─ events:read
├─ events:write
├─ alerts:read
├─ alerts:manage
├─ users:read
├─ users:manage
└─ system:admin
```

## 📊 **Data Models**

### **User**
```python
- id: UUID (PK)
- email: String (unique)
- password_hash: String
- full_name: String
- role: Enum (admin, analyst, viewer)
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime
```

### **Event**
```python
- id: UUID (PK)
- user_identifier: String
- ip_address: String
- country: String
- city: String
- latitude: Float
- longitude: Float
- status: Enum (success, failed)
- device: String
- browser: String
- risk_score: Integer
- risk_level: Enum
- ml_anomaly: Boolean
- ml_score: Float
- created_at: DateTime
```

### **Alert**
```python
- id: UUID (PK)
- event_id: UUID (FK)
- title: String
- severity: Enum
- description: Text
- status: Enum (open, acknowledged, resolved)
- assigned_to: UUID (FK)
- created_at: DateTime
- resolved_at: DateTime
```

## 🔄 **Real-time Event Flow**

```
1. Event Ingestion
   ├─> POST /api/v1/events
   ├─> Validate schema
   ├─> Save to database
   └─> Publish to processing queue

2. Risk Analysis
   ├─> Extract features
   ├─> ML anomaly detection
   ├─> Multi-signal risk scoring
   ├─> Classify severity
   └─> Generate alert (if critical)

3. Notification
   ├─> WebSocket broadcast (real-time)
   ├─> Email notification (critical)
   ├─> Slack webhook (critical)
   └─> SMS alert (emergency)

4. Dashboard Update
   ├─> WebSocket push to connected clients
   ├─> Update statistics
   └─> Refresh visualizations
```

## 🚀 **Deployment Architecture**

### **Production Deployment**
```
┌─────────────────────────────────────┐
│  CloudFront / CDN                   │
│  (Static assets + caching)          │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  Application Load Balancer          │
│  (SSL termination, routing)         │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼─────┐   ┌──────▼─────┐
│  Backend   │   │  Backend   │
│  Instance  │   │  Instance  │
│  (ECS/K8s) │   │  (ECS/K8s) │
└──────┬─────┘   └──────┬─────┘
       │                │
       └───────┬────────┘
               │
   ┌───────────┼───────────┐
   │           │           │
┌──▼────┐  ┌──▼────┐  ┌──▼────┐
│  RDS  │  │ Redis │  │  S3   │
│  PG   │  │ Elasti│  │ Models│
│       │  │ Cache │  │       │
└───────┘  └───────┘  └───────┘
```

## 📈 **Scalability Strategy**

### **Horizontal Scaling**
- Multiple backend instances (auto-scaling)
- Read replicas for PostgreSQL
- Redis cluster for caching
- CDN for static assets

### **Vertical Scaling**
- Database: Increase instance size
- Redis: Memory optimization
- ML Models: GPU acceleration

### **Performance Optimization**
- Database indexing
- Query optimization
- Caching strategy (Redis)
- Connection pooling
- Async I/O (FastAPI)

## 🔍 **Monitoring & Observability**

### **Metrics** (Prometheus)
- Request rate, latency, errors
- Database connection pool
- Cache hit/miss ratio
- ML model performance
- System resources (CPU, memory)

### **Logs** (ELK Stack)
- Application logs (structured JSON)
- Access logs
- Error logs with stack traces
- Audit logs

### **Tracing** (Jaeger)
- Request tracing
- Service dependencies
- Performance bottlenecks

### **Alerts**
- Error rate > threshold
- Response time > SLA
- Database connection failures
- ML model drift
- Security events

## 🧪 **Testing Strategy**

### **Unit Tests** (70% coverage)
- Service layer logic
- Repository methods
- Utility functions
- ML feature extraction

### **Integration Tests**
- API endpoints
- Database operations
- Cache layer
- WebSocket connections

### **E2E Tests**
- User workflows
- Authentication flow
- Event processing pipeline
- Alert generation

### **Performance Tests**
- Load testing (Locust)
- Stress testing
- Database query performance
- Cache effectiveness

## 🔐 **Security Hardening**

### **Application Security**
- Input validation (Pydantic)
- SQL injection protection (ORM)
- XSS prevention (sanitization)
- CSRF tokens
- Rate limiting
- API key rotation

### **Network Security**
- HTTPS only (TLS 1.3)
- CORS configuration
- Security headers
- IP whitelisting (admin endpoints)

### **Data Security**
- Encryption at rest
- Encryption in transit
- Password hashing (bcrypt)
- Secrets management (Vault)
- PII data masking

---

**Built for Production. Scales to Enterprise. Secure by Design.**
