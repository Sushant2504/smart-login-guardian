"""
Smart Login Guardian - Simplified Demo Version
This version runs without PostgreSQL/Redis for demonstration
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

# Simple config without pydantic-settings
class SimpleSettings:
    APP_NAME = "Smart Login Guardian"
    APP_VERSION = "2.0.0-demo"
    ENVIRONMENT = "development"
    API_V1_PREFIX = "/api/v1"
    CORS_ORIGINS = ["*"]
    CORS_ALLOW_CREDENTIALS = True

settings = SimpleSettings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print("✓ Running in DEMO mode (no database required)")
    yield
    print("✓ Shutdown complete")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## 🛡️ Enterprise Identity Threat Detection Platform

    **Demo Version** - API Documentation Viewer

    This is a demonstration showing the complete API architecture with 65+ endpoints.

    ### 📊 Available Endpoints:
    - **Authentication** (10 endpoints) - User management, JWT tokens, API keys
    - **Events** (12 endpoints) - Login event processing & analytics
    - **Alerts** (7 endpoints) - Security alert management
    - **Users** (7 endpoints) - User administration
    - **ML** (9 endpoints) - Machine learning operations
    - **Reports** (9 endpoints) - Analytics & compliance reporting
    - **Admin** (11 endpoints) - System administration

    ### 🏗️ Enterprise Features:
    - Multi-layer security (JWT, RBAC, rate limiting)
    - Prometheus metrics & structured logging
    - OpenAPI/Swagger documentation
    - Role-based access control
    - Audit logging capabilities

    ### ⚠️ Note:
    This demo version shows the API structure. Full functionality requires:
    - PostgreSQL database
    - Redis cache
    - Complete service implementation

    See the documentation for deployment instructions.
    """,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint

    Returns the system status and version information.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "mode": "demo",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "message": "API documentation available at /api/docs"
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint

    Welcome message with links to documentation.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mode": "demo",
        "description": "Enterprise Identity Threat Detection Platform",
        "documentation": {
            "interactive": "/api/docs",
            "redoc": "/api/redoc",
            "openapi": "/api/openapi.json"
        },
        "health": "/health",
        "endpoints": {
            "authentication": f"{settings.API_V1_PREFIX}/auth",
            "events": f"{settings.API_V1_PREFIX}/events",
            "alerts": f"{settings.API_V1_PREFIX}/alerts",
            "users": f"{settings.API_V1_PREFIX}/users",
            "ml": f"{settings.API_V1_PREFIX}/ml",
            "reports": f"{settings.API_V1_PREFIX}/reports",
            "admin": f"{settings.API_V1_PREFIX}/admin"
        },
        "note": "This is a demo version showing API architecture. Some endpoints return mock data."
    }

# Import and include API routers (simplified versions)
try:
    from app.api.v1 import api_router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    print("✓ API routers loaded successfully")
except Exception as e:
    print(f"⚠️  API routers not loaded: {e}")
    print("   Running with basic endpoints only")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Smart Login Guardian - Demo Server")
    print("="*60)
    print(f"📡 Starting server at http://localhost:8000")
    print(f"📚 API Documentation: http://localhost:8000/api/docs")
    print(f"🏥 Health Check: http://localhost:8000/health")
    print("="*60 + "\n")

    uvicorn.run(
        "app.main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
