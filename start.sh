#!/bin/bash

# Smart Login Guardian - Easy Startup Script
# Run this script to start the complete platform

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         SMART LOGIN GUARDIAN - STARTUP                          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -q fastapi uvicorn pydantic python-jose passlib[bcrypt] python-multipart email-validator scikit-learn numpy
    echo "✅ Dependencies installed"
fi

# Check what to start
echo ""
echo "Which version do you want to start?"
echo ""
echo "1) 🌍 3D Interactive Demo (RECOMMENDED)"
echo "   - 3D Globe visualization"
echo "   - Machine Learning"
echo "   - Working attack buttons"
echo "   - Port: 8080"
echo ""
echo "2) 🚀 Complete Application"
echo "   - Full authentication"
echo "   - All microservices"
echo "   - Port: 9000"
echo ""
echo "3) 📊 Backend Service Only"
echo "   - API service"
echo "   - Port: 8002"
echo ""

read -p "Enter choice (1-3) [1]: " choice
choice=${choice:-1}

case $choice in
    1)
        echo ""
        echo "🌍 Starting 3D Interactive Demo..."
        echo ""
        echo "✅ Starting on http://localhost:8080"
        echo "✅ Press Ctrl+C to stop"
        echo ""
        python3 demo/final_complete_demo.py
        ;;
    2)
        echo ""
        echo "🚀 Starting Complete Application..."
        echo ""
        echo "✅ Starting on http://localhost:9000"
        echo "✅ Login: admin@demo.com / Demo@123"
        echo "✅ Press Ctrl+C to stop"
        echo ""
        python3 app.py
        ;;
    3)
        echo ""
        echo "📊 Starting Backend Service..."
        echo ""
        echo "✅ Starting on http://localhost:8002"
        echo "✅ API Docs: http://localhost:8002/docs"
        echo "✅ Press Ctrl+C to stop"
        echo ""
        python3 services/backend/main.py
        ;;
    *)
        echo "Invalid choice. Starting default (3D Demo)..."
        python3 demo/final_complete_demo.py
        ;;
esac
