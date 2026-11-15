#!/bin/bash

# Smart Login Guardian - Production Application Startup Script

set -e

echo "🛡️  Smart Login Guardian - Starting Production Application"
echo "======================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose not found. Please install Docker Compose.${NC}"
    exit 1
fi

# Display menu
echo ""
echo -e "${BLUE}Select deployment option:${NC}"
echo "1) Start all services (PostgreSQL + Redis + Backend API)"
echo "2) Start database only (PostgreSQL + Redis)"
echo "3) Stop all services"
echo "4) View logs"
echo "5) Rebuild and restart"
echo "6) Check service status"
echo "7) Clean up (remove containers and volumes)"
echo ""
read -p "Enter choice [1-7]: " choice

case $choice in
    1)
        echo -e "${BLUE}🚀 Starting all services...${NC}"
        docker-compose up -d
        echo ""
        echo -e "${GREEN}✅ Services started successfully!${NC}"
        echo ""
        echo -e "${BLUE}Access points:${NC}"
        echo "  • API: http://localhost:8000"
        echo "  • API Docs: http://localhost:8000/api/docs"
        echo "  • Health Check: http://localhost:8000/health"
        echo "  • PostgreSQL: localhost:5432"
        echo "  • Redis: localhost:6379"
        echo ""
        echo -e "${YELLOW}📝 View logs with: docker-compose logs -f backend${NC}"
        ;;

    2)
        echo -e "${BLUE}🗄️  Starting database services...${NC}"
        docker-compose up -d postgres redis
        echo ""
        echo -e "${GREEN}✅ Database services started!${NC}"
        echo "  • PostgreSQL: localhost:5432"
        echo "  • Redis: localhost:6379"
        ;;

    3)
        echo -e "${BLUE}🛑 Stopping all services...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ All services stopped.${NC}"
        ;;

    4)
        echo -e "${BLUE}📋 Showing logs (Ctrl+C to exit)...${NC}"
        docker-compose logs -f
        ;;

    5)
        echo -e "${BLUE}🔄 Rebuilding and restarting...${NC}"
        docker-compose down
        docker-compose up -d --build
        echo -e "${GREEN}✅ Services rebuilt and restarted!${NC}"
        ;;

    6)
        echo -e "${BLUE}📊 Service Status:${NC}"
        docker-compose ps
        echo ""
        echo -e "${BLUE}🏥 Health Checks:${NC}"
        echo -n "Backend API: "
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Healthy${NC}"
        else
            echo -e "${RED}❌ Unhealthy${NC}"
        fi
        ;;

    7)
        echo -e "${YELLOW}⚠️  This will remove all containers and volumes!${NC}"
        read -p "Are you sure? (y/N): " confirm
        if [ "$confirm" == "y" ] || [ "$confirm" == "Y" ]; then
            echo -e "${BLUE}🧹 Cleaning up...${NC}"
            docker-compose down -v
            echo -e "${GREEN}✅ Cleanup complete!${NC}"
        else
            echo "Cancelled."
        fi
        ;;

    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done! 🎉${NC}"
