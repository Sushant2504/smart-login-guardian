#!/bin/bash

echo "🚀 Testing Smart Login Guardian API startup..."
echo ""

cd /Users/snadavad/Documents/smart-login-guardian/backend

# Try to start the app without database (will show import errors if any)
source ../venv/bin/activate

echo "✓ Virtual environment activated"
echo "✓ Testing app imports..."

python3 << 'PYEOF'
import sys
sys.path.insert(0, '/Users/snadavad/Documents/smart-login-guardian/backend')

try:
    print("\n📦 Checking imports...")
    from app import main
    print("✅ Main module imported successfully!")
    
    from app.api.v1 import auth, events, alerts, users, ml, reports, admin
    print("✅ All API routers imported successfully!")
    
    from app.middleware import (
        RequestLoggingMiddleware,
        RateLimitMiddleware, 
        MetricsMiddleware,
        SecurityHeadersMiddleware
    )
    print("✅ All middleware imported successfully!")
    
    from app.services import (
        alert_service,
        user_service,
        ml_service,
        report_service,
        admin_service
    )
    print("✅ All services imported successfully!")
    
    print("\n✨ Application structure is valid!")
    print("\n📊 Summary:")
    print("  - 7 API Routers: ✅")
    print("  - 4 Middleware Components: ✅")
    print("  - 5 Service Modules: ✅")
    print("  - Security Infrastructure: ✅")
    
    print("\n⚠️  NOTE: To fully run the app, you need:")
    print("  1. Start PostgreSQL database")
    print("  2. Start Redis")
    print("  3. Set DATABASE_URL in .env")
    print("  4. Run: uvicorn app.main:app --reload")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

PYEOF

