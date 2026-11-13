#!/bin/bash

# Smart Login Guardian - Deployment Script
# Deploys the application using Docker Compose

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         SMART LOGIN GUARDIAN - DEPLOYMENT                        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration before continuing"
    echo "   Required changes:"
    echo "   - SECRET_KEY"
    echo "   - JWT_SECRET_KEY"
    echo "   - DB_PASSWORD"
    echo "   - ADMIN_EMAIL and ADMIN_PASSWORD"
    read -p "Press Enter after editing .env file to continue..."
fi

echo "🔨 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🌐 Application is running at:"
    echo "   Dashboard:  http://localhost:5000"
    echo "   API:        http://localhost:5000/api/v1"
    echo "   Health:     http://localhost:5000/health"
    echo ""
    echo "📊 Services:"
    docker-compose ps
    echo ""
    echo "📝 View logs:"
    echo "   docker-compose logs -f app"
    echo ""
    echo "🛑 Stop services:"
    echo "   docker-compose down"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ Deployment failed. Check logs:"
    echo "   docker-compose logs"
    exit 1
fi
