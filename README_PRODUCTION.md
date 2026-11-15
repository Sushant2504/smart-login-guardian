# 🛡️ Smart Login Guardian - Production Application

**Enterprise-grade Identity Threat Detection Platform**

## 🚀 Quick Start (3 Commands)

```bash
# 1. Start all services (PostgreSQL, Redis, Backend)
docker-compose up -d

# 2. Check service status
docker-compose ps

# 3. View logs
docker-compose logs -f backend
```

**Access the application:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

---

## 📋 **What's New - Production Application**

### ✅ **Architecture Enhancements**

- **Layered Architecture**: API → Service → Repository → Database
- **Clean Separation**: Models, Schemas, Services, and APIs are properly separated
- **Dependency Injection**: Proper FastAPI dependencies for database sessions
- **Type Safety**: Full Pydantic schemas with validation
- **Async/Await**: Modern async Python with SQLAlchemy 2.0

### ✅ **Database Layer**

- **PostgreSQL**: Production-grade relational database
- **SQLAlchemy ORM**: Modern async ORM with proper models
- **Alembic Migrations**: Database version control
- **Connection Pooling**: Optimized database connections
- **Proper Indexes**: Performance-optimized queries

### ✅ **Models Created**

1. **User** - Authentication and authorization
   - Email, password hash, role (admin/analyst/viewer)
   - Active status, created/updated timestamps

2. **Event** - Authentication events
   - User identifier, IP, location (country, city, lat/lon)
   - Device, browser, user agent
   - Risk score, risk level, ML anomaly detection
   - Signals (detection reasons)

3. **Alert** - Security alerts
   - Title, description, severity
   - Status (open, acknowledged, resolved)
   - Event relationship, user assignment
   - Resolution tracking

### ✅ **Core Features**

- **JWT Authentication**: Secure token-based auth with access & refresh tokens
- **Password Hashing**: bcrypt for secure password storage
- **Role-Based Access Control (RBAC)**: Admin, Analyst, Viewer, API roles
- **Structured Logging**: JSON logs with structlog
- **Exception Handling**: Custom exceptions with proper HTTP status codes
- **Configuration Management**: Environment-based config with Pydantic
- **Health Checks**: Liveness and readiness endpoints

### ✅ **Infrastructure**

- **Docker Compose**: Local development environment
  - PostgreSQL 15
  - Redis 7
  - Backend API
  - (Frontend ready to add)

- **Multi-Stage Docker Build**:
  - Development: Hot reload, dev dependencies
  - Production: Optimized, minimal, non-root user

- **Docker Volumes**: Persistent data storage
- **Health Checks**: Container-level monitoring
- **Network Isolation**: Custom Docker network

---

## 🏗️ **Project Structure**

```
smart-login-guardian/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── event.py
│   │   │   └── alert.py
│   │   │
│   │   ├── schemas/           # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── event.py
│   │   │   ├── alert.py
│   │   │   └── auth.py
│   │   │
│   │   ├── api/               # API endpoints
│   │   │   └── v1/
│   │   │       ├── auth.py    (TODO)
│   │   │       ├── events.py  (TODO)
│   │   │       └── users.py   (TODO)
│   │   │
│   │   ├── services/          # Business logic (TODO)
│   │   ├── repositories/      # Data access (TODO)
│   │   │
│   │   ├── core/              # Core utilities
│   │   │   ├── security.py    # JWT, password hashing
│   │   │   ├── exceptions.py  # Custom exceptions
│   │   │   └── logger.py      # Logging config
│   │   │
│   │   ├── ml/                # ML models (TODO)
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # DB connection
│   │   └── main.py            # FastAPI app
│   │
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Test suite
│   ├── requirements.txt       # Production dependencies
│   ├── requirements-dev.txt   # Dev dependencies
│   ├── Dockerfile             # Multi-stage Docker build
│   └── .env                   # Environment variables
│
├── frontend/                  # React Frontend (TODO)
│   └── src/
│
├── docker-compose.yml         # Local dev environment
├── ARCHITECTURE.md           # Architecture documentation
└── README_PRODUCTION.md      # This file
```

---

## 🔧 **Development Setup**

### **Prerequisites**

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend)

### **Option 1: Docker (Recommended)**

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build backend
```

### **Option 2: Local Development**

```bash
# 1. Start PostgreSQL and Redis
docker-compose up -d postgres redis

# 2. Install dependencies
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# 3. Run migrations (when ready)
# alembic upgrade head

# 4. Start backend
python app/main.py

# Or with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📝 **API Documentation**

### **Interactive Docs**

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

### **Health Check**

```bash
curl http://localhost:8000/health

{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-11-15T12:00:00",
  "environment": "development"
}
```

---

## 🗄️ **Database**

### **Connection**

```bash
# Connect to PostgreSQL
docker exec -it smart_guardian_db psql -U postgres -d smart_login_guardian

# List tables
\dt

# Describe table
\d events
```

### **Migrations** (TODO)

```bash
# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🧪 **Testing**

```bash
cd backend

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api/test_auth.py

# Run with verbose output
pytest -v
```

---

## 🔐 **Security**

### **Environment Variables**

**IMPORTANT**: Change these in production!

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file
SECRET_KEY=<generated-key>
```

### **Password Requirements**

- Minimum 8 characters
- Hashed with bcrypt
- Stored securely in database

### **JWT Tokens**

- Access token: 30 minutes (default)
- Refresh token: 7 days (default)
- HS256 algorithm

---

## 📊 **Monitoring**

### **Docker Health Checks**

```bash
# Check container health
docker ps
docker inspect smart_guardian_backend | grep Health -A 10
```

### **Logs**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

---

## 🚢 **Production Deployment**

### **Docker Production Build**

```bash
# Build production image
docker build --target production -t smart-guardian:latest ./backend

# Run in production mode
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=<prod-db-url> \
  -e SECRET_KEY=<prod-secret> \
  smart-guardian:latest
```

### **Environment Variables for Production**

```bash
APP_NAME=Smart Login Guardian
ENVIRONMENT=production
DEBUG=False

DATABASE_URL=postgresql://user:pass@prod-db:5432/db
REDIS_URL=redis://prod-redis:6379/0

SECRET_KEY=<strong-secret-key-32+-chars>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

CORS_ORIGINS=https://app.example.com
SENTRY_DSN=<sentry-dsn>
```

---

## 🎯 **Next Steps**

### **Phase 1: API Implementation** (In Progress)

- [ ] Implement authentication routes (`/api/v1/auth`)
- [ ] Create event management routes (`/api/v1/events`)
- [ ] Add alert management routes (`/api/v1/alerts`)
- [ ] User management routes (`/api/v1/users`)
- [ ] ML model operations (`/api/v1/ml`)

### **Phase 2: Services & Business Logic**

- [ ] AuthService - Login, registration, token management
- [ ] EventService - Event processing and risk analysis
- [ ] RiskAnalysisService - Multi-signal risk scoring
- [ ] MLDetectionService - Anomaly detection
- [ ] NotificationService - Email, Slack, SMS alerts

### **Phase 3: Frontend**

- [ ] React + TypeScript setup
- [ ] Redux state management
- [ ] Material-UI components
- [ ] Authentication flow
- [ ] Dashboard with charts
- [ ] Real-time updates (WebSocket)

### **Phase 4: Advanced Features**

- [ ] Redis caching layer
- [ ] WebSocket for real-time updates
- [ ] Email notifications (SMTP)
- [ ] Slack webhooks
- [ ] CSV/PDF exports
- [ ] Scheduled reports

### **Phase 5: Production Readiness**

- [ ] Comprehensive test suite (80%+ coverage)
- [ ] Performance optimization
- [ ] Security audit
- [ ] CI/CD pipeline
- [ ] Kubernetes deployment
- [ ] Monitoring & alerting

---

## 🛠️ **Common Tasks**

### **Add a New Model**

1. Create model in `backend/app/models/`
2. Create schema in `backend/app/schemas/`
3. Create migration: `alembic revision --autogenerate -m "Add model"`
4. Apply migration: `alembic upgrade head`

### **Add a New API Endpoint**

1. Create router in `backend/app/api/v1/`
2. Implement service logic in `backend/app/services/`
3. Add repository methods in `backend/app/repositories/`
4. Include router in `main.py`
5. Write tests in `backend/tests/`

### **Update Dependencies**

```bash
cd backend

# Update requirements.txt
pip freeze > requirements.txt

# Rebuild Docker image
docker-compose up -d --build backend
```

---

## 📚 **Documentation**

- **Architecture**: See `ARCHITECTURE.md`
- **API Docs**: http://localhost:8000/api/docs
- **Attack Detection**: See `ATTACK_DETECTION_EXPLAINED.md`
- **ML Model**: See `ML_MODEL_VERIFICATION.md`
- **Deployment**: See `VERCEL_DEPLOYMENT.md` and `GITHUB_VERCEL_SETUP.md`

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Write tests
4. Make your changes
5. Run tests: `pytest`
6. Commit: `git commit -m "feat: description"`
7. Push and create PR

---

## 📄 **License**

MIT License - See LICENSE file

---

## 🎉 **Current Status**

✅ **Production-Grade Architecture** - Implemented  
✅ **Database Models & Schemas** - Complete  
✅ **Configuration Management** - Complete  
✅ **Security Layer** - JWT, Password Hashing  
✅ **Docker Setup** - Development Ready  
✅ **Logging & Error Handling** - Implemented  

🔄 **In Progress** - API Endpoints, Services, Frontend  
⏳ **Todo** - Tests, Monitoring, Production Deployment  

---

**Ready for development!** 🚀

Start with: `docker-compose up -d`
