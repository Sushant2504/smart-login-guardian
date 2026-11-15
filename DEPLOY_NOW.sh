#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     🚀 DEPLOYING SMART LOGIN GUARDIAN TO VERCEL                 ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

cd /Users/snadavad/Documents/smart-login-guardian

echo "📁 Project Directory: $(pwd)"
echo ""

# Check if vercel is installed
if command -v vercel &> /dev/null; then
    echo "✅ Vercel CLI found"
    vercel --version
    echo ""
    echo "🚀 Deploying to production..."
    echo ""
    vercel --prod
elif command -v npx &> /dev/null; then
    echo "✅ Using npx to run Vercel"
    echo ""
    echo "🚀 Deploying to production..."
    echo ""
    npx vercel --prod
else
    echo "❌ Neither Vercel CLI nor npx found"
    echo ""
    echo "Please install Node.js and npm first:"
    echo "https://nodejs.org/"
    exit 1
fi
