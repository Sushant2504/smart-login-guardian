#!/bin/bash
# Simple demo runner with dependency check

set -e

echo "🛡️  Smart Login Guardian - Starting Demo..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required"
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
python3 -c "import fastapi, pydantic, uvicorn" 2>/dev/null || {
    echo "Installing dependencies..."
    pip3 install -q -r requirements-demo.txt
}

echo "✅ Dependencies ready"
echo ""
echo "🚀 Starting server on http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/api/docs"
echo ""
echo "🔑 Demo Login:"
echo "   Email: admin@example.com"
echo "   Password: Admin123!"
echo ""

# Run demo
python3 demo_enterprise.py
