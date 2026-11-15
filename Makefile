.PHONY: help dev up down logs clean db-migrate db-reset db-seed test lint build docker-build

# Colors for terminal output
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
BLUE   := $(shell tput -Txterm setaf 4)
RESET  := $(shell tput -Txterm sgr0)

help: ## Show this help message
	@echo '${BLUE}Smart Login Guardian - Makefile Commands${RESET}'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "${GREEN}%-20s${RESET} %s\n", $$1, $$2}'

# =====================================================
# Development Environment
# =====================================================

dev: ## Start development environment
	@echo "${BLUE}Starting Smart Login Guardian development environment...${RESET}"
	docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d
	@echo "${GREEN}Development environment started!${RESET}"
	@echo "${YELLOW}PostgreSQL:${RESET}      localhost:5432"
	@echo "${YELLOW}Redis:${RESET}           localhost:6379"
	@echo "${YELLOW}Redpanda (Kafka):${RESET} localhost:19092"
	@echo "${YELLOW}Redpanda Console:${RESET} http://localhost:8080"
	@echo "${YELLOW}ClickHouse:${RESET}      localhost:8123"
	@echo "${YELLOW}Prometheus:${RESET}      http://localhost:9090"
	@echo "${YELLOW}Grafana:${RESET}         http://localhost:3001 (admin/admin)"
	@echo "${YELLOW}Mailhog:${RESET}         http://localhost:8025"

up: dev ## Alias for dev

down: ## Stop development environment
	@echo "${BLUE}Stopping development environment...${RESET}"
	docker-compose -f infrastructure/docker/docker-compose.dev.yml down

stop: down ## Alias for down

restart: down dev ## Restart development environment

logs: ## Show logs from all services
	docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f

logs-postgres: ## Show PostgreSQL logs
	docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f postgres

logs-redis: ## Show Redis logs
	docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f redis

logs-redpanda: ## Show Redpanda logs
	docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f redpanda

logs-clickhouse: ## Show ClickHouse logs
	docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f clickhouse

clean: ## Remove all containers, volumes, and networks
	@echo "${YELLOW}WARNING: This will remove all data. Continue? [y/N]${RESET}" && read ans && [ $${ans:-N} = y ]
	docker-compose -f infrastructure/docker/docker-compose.dev.yml down -v
	@echo "${GREEN}Environment cleaned!${RESET}"

# =====================================================
# Database Operations
# =====================================================

db-shell: ## Connect to PostgreSQL shell
	docker exec -it slg-postgres psql -U slg_user -d smart_login_guardian

db-migrate: ## Run database migrations
	@echo "${BLUE}Running database migrations...${RESET}"
	# TODO: Implement migration runner (golang-migrate)
	@echo "${YELLOW}Migration runner not yet implemented${RESET}"

db-reset: ## Reset database (drop and recreate)
	@echo "${YELLOW}WARNING: This will delete all data. Continue? [y/N]${RESET}" && read ans && [ $${ans:-N} = y ]
	docker exec -it slg-postgres psql -U slg_user -d postgres -c "DROP DATABASE IF EXISTS smart_login_guardian;"
	docker exec -it slg-postgres psql -U slg_user -d postgres -c "CREATE DATABASE smart_login_guardian;"
	docker exec -it slg-postgres psql -U slg_user -d smart_login_guardian -f /docker-entrypoint-initdb.d/001_initial_schema.sql
	@echo "${GREEN}Database reset complete!${RESET}"

db-seed: ## Seed database with sample data
	@echo "${BLUE}Seeding database...${RESET}"
	# TODO: Implement seed script
	@echo "${YELLOW}Seed script not yet implemented${RESET}"

clickhouse-shell: ## Connect to ClickHouse shell
	docker exec -it slg-clickhouse clickhouse-client --user slg_analytics --password slg_analytics_password --database smart_login_guardian_analytics

redis-cli: ## Connect to Redis CLI
	docker exec -it slg-redis redis-cli -a slg_redis_password

# =====================================================
# Testing
# =====================================================

test: ## Run all tests
	@echo "${BLUE}Running tests...${RESET}"
	cd services/auth-service && go test -v -race -coverprofile=coverage.out ./...
	cd services/ingestion-service && go test -v -race -coverprofile=coverage.out ./...
	cd services/risk-engine && python -m pytest tests/ -v --cov
	cd services/detection-service && python -m pytest tests/ -v --cov
	@echo "${GREEN}All tests passed!${RESET}"

test-auth: ## Run authentication service tests
	cd services/auth-service && go test -v -race -coverprofile=coverage.out ./...

test-ingestion: ## Run ingestion service tests
	cd services/ingestion-service && go test -v -race -coverprofile=coverage.out ./...

test-risk: ## Run risk engine tests
	cd services/risk-engine && python -m pytest tests/ -v --cov

test-detection: ## Run detection service tests
	cd services/detection-service && python -m pytest tests/ -v --cov

test-integration: ## Run integration tests
	@echo "${BLUE}Running integration tests...${RESET}"
	# TODO: Implement integration tests
	@echo "${YELLOW}Integration tests not yet implemented${RESET}"

# =====================================================
# Linting & Code Quality
# =====================================================

lint: ## Run linters
	@echo "${BLUE}Running linters...${RESET}"
	cd services/auth-service && golangci-lint run
	cd services/ingestion-service && golangci-lint run
	cd services/risk-engine && pylint **/*.py
	cd services/detection-service && pylint **/*.py
	cd apps/web && npm run lint

lint-fix: ## Fix linting issues
	@echo "${BLUE}Fixing linting issues...${RESET}"
	cd services/auth-service && golangci-lint run --fix
	cd services/ingestion-service && golangci-lint run --fix
	cd services/risk-engine && black . && isort .
	cd services/detection-service && black . && isort .
	cd apps/web && npm run lint:fix

# =====================================================
# Build
# =====================================================

build: ## Build all services
	@echo "${BLUE}Building all services...${RESET}"
	cd services/auth-service && go build -o ../../bin/auth-service ./cmd/server
	cd services/ingestion-service && go build -o ../../bin/ingestion-service ./cmd/server
	cd apps/api-gateway && go build -o ../../bin/api-gateway ./cmd/server
	@echo "${GREEN}Build complete!${RESET}"

build-auth: ## Build authentication service
	cd services/auth-service && go build -o ../../bin/auth-service ./cmd/server

build-ingestion: ## Build ingestion service
	cd services/ingestion-service && go build -o ../../bin/ingestion-service ./cmd/server

build-gateway: ## Build API gateway
	cd apps/api-gateway && go build -o ../../bin/api-gateway ./cmd/server

docker-build: ## Build Docker images
	@echo "${BLUE}Building Docker images...${RESET}"
	docker build -f services/auth-service/Dockerfile -t slg-auth-service:latest .
	docker build -f services/ingestion-service/Dockerfile -t slg-ingestion-service:latest .
	docker build -f apps/api-gateway/Dockerfile -t slg-api-gateway:latest .
	docker build -f apps/web/Dockerfile -t slg-web:latest .
	@echo "${GREEN}Docker images built!${RESET}"

# =====================================================
# Frontend
# =====================================================

web-dev: ## Start Next.js development server
	cd apps/web && npm run dev

web-build: ## Build Next.js production bundle
	cd apps/web && npm run build

web-install: ## Install frontend dependencies
	cd apps/web && npm install

# =====================================================
# Services
# =====================================================

run-auth: ## Run authentication service locally
	cd services/auth-service && go run ./cmd/server

run-ingestion: ## Run ingestion service locally
	cd services/ingestion-service && go run ./cmd/server

run-gateway: ## Run API gateway locally
	cd apps/api-gateway && go run ./cmd/server

run-risk: ## Run risk engine locally
	cd services/risk-engine && python -m uvicorn app.main:app --reload --port 8001

run-detection: ## Run detection service locally
	cd services/detection-service && python -m uvicorn app.main:app --reload --port 8002

# =====================================================
# Utilities
# =====================================================

format: ## Format all code
	@echo "${BLUE}Formatting code...${RESET}"
	cd services/auth-service && go fmt ./...
	cd services/ingestion-service && go fmt ./...
	cd apps/api-gateway && go fmt ./...
	cd services/risk-engine && black . && isort .
	cd services/detection-service && black . && isort .
	cd apps/web && npm run format
	@echo "${GREEN}Code formatted!${RESET}"

install-tools: ## Install development tools
	@echo "${BLUE}Installing development tools...${RESET}"
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	go install github.com/golang-migrate/migrate/v4/cmd/migrate@latest
	pip install black isort pylint pytest pytest-cov
	@echo "${GREEN}Tools installed!${RESET}"

check-deps: ## Check for dependency updates
	@echo "${BLUE}Checking for updates...${RESET}"
	cd services/auth-service && go list -u -m all
	cd apps/web && npm outdated

generate: ## Generate code (protobufs, mocks, etc.)
	@echo "${BLUE}Generating code...${RESET}"
	# TODO: Implement code generation
	@echo "${YELLOW}Code generation not yet implemented${RESET}"

docs: ## Generate documentation
	@echo "${BLUE}Generating documentation...${RESET}"
	# TODO: Implement documentation generation
	@echo "${YELLOW}Documentation generation not yet implemented${RESET}"

# =====================================================
# Monitoring
# =====================================================

prometheus: ## Open Prometheus UI
	open http://localhost:9090

grafana: ## Open Grafana UI
	open http://localhost:3001

redpanda-console: ## Open Redpanda Console
	open http://localhost:8080

mailhog: ## Open Mailhog UI
	open http://localhost:8025

# =====================================================
# Status
# =====================================================

status: ## Show status of all services
	@echo "${BLUE}Service Status:${RESET}"
	@docker-compose -f infrastructure/docker/docker-compose.dev.yml ps

health: ## Check health of all services
	@echo "${BLUE}Health Checks:${RESET}"
	@echo "${YELLOW}PostgreSQL:${RESET}"
	@docker exec slg-postgres pg_isready -U slg_user -d smart_login_guardian || echo "  ❌ Not ready"
	@echo "${YELLOW}Redis:${RESET}"
	@docker exec slg-redis redis-cli -a slg_redis_password ping || echo "  ❌ Not ready"
	@echo "${YELLOW}ClickHouse:${RESET}"
	@curl -s http://localhost:8123/ping || echo "  ❌ Not ready"

# =====================================================
# Information
# =====================================================

info: ## Show environment information
	@echo "${BLUE}Smart Login Guardian - Environment Information${RESET}"
	@echo ""
	@echo "${GREEN}Infrastructure:${RESET}"
	@echo "  PostgreSQL:       localhost:5432"
	@echo "  Redis:            localhost:6379"
	@echo "  Redpanda (Kafka): localhost:19092"
	@echo "  ClickHouse:       localhost:8123"
	@echo ""
	@echo "${GREEN}Web Interfaces:${RESET}"
	@echo "  Redpanda Console: http://localhost:8080"
	@echo "  Prometheus:       http://localhost:9090"
	@echo "  Grafana:          http://localhost:3001"
	@echo "  Mailhog:          http://localhost:8025"
	@echo ""
	@echo "${GREEN}Credentials:${RESET}"
	@echo "  PostgreSQL:  slg_user / slg_password_dev_only"
	@echo "  Redis:       slg_redis_password"
	@echo "  ClickHouse:  slg_analytics / slg_analytics_password"
	@echo "  Grafana:     admin / admin"

version: ## Show version information
	@echo "${BLUE}Smart Login Guardian${RESET}"
	@echo "Version: 1.0.0-alpha"
	@echo "Build: $(shell git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
	@echo "Go: $(shell go version 2>/dev/null || echo 'not installed')"
	@echo "Node: $(shell node --version 2>/dev/null || echo 'not installed')"
	@echo "Python: $(shell python --version 2>/dev/null || echo 'not installed')"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo 'not installed')"

.DEFAULT_GOAL := help
