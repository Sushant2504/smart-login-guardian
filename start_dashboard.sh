#!/bin/bash

# Smart Login Guardian - Dashboard Launcher
# Quick start script for the 3D web dashboard

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║        🛡️  SMART LOGIN GUARDIAN - 3D DASHBOARD  🛡️                ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

echo "📦 Checking dependencies..."

# Check if required packages are installed
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Flask not found. Installing dependencies..."
    pip3 install -r requirements.txt
else
    echo "✅ Dependencies OK"
fi

echo ""
echo "🚀 Starting Smart Login Guardian Dashboard..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Dashboard URL: http://localhost:5000"
echo ""
echo "  Features:"
echo "    🌍 3D Globe Visualization"
echo "    📊 Real-time Analytics"
echo "    🚨 Threat Intelligence"
echo "    🎯 Attack Simulations"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the server
cd web
python3 app.py
