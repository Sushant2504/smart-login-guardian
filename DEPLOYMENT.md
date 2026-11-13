<<<<<<< SEARCH
# Smart Login Guardian - Deployment Guide
=======
# Smart Login Guardian - Production Deployment Guide

Complete guide for deploying Smart Login Guardian as a production SaaS platform.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Deployment Methods](#deployment-methods)
5. [Database Setup](#database-setup)
6. [Security](#security)
7. [Monitoring](#monitoring)
8. [Scaling](#scaling)

## Quick Start

### Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourcompany/smart-login-guardian.git
cd smart-login-guardian

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Deploy
./deploy.sh
```

Your application will be running at `http://localhost:5000`

Default admin credentials:
- Email: See `ADMIN_EMAIL` in `.env`
- Password: See `ADMIN_PASSWORD` in `.env`

**⚠️ IMPORTANT: Change the admin password immediately after first login!**

## Prerequisites

### Required

- **Docker** 20.10+ and **Docker Compose** 2.0+
- OR **Python** 3.9+ (for manual deployment)
- **PostgreSQL** 13+ (production database)
- **Redis** 6+ (for rate limiting and caching)

### Recommended

- **nginx** (reverse proxy)
- **Let's Encrypt** (SSL/TLS certificates)
- **Prometheus** + **Grafana** (monitoring)

## Environment Configuration

### Essential Variables

Edit `.env` file with these critical settings:

```bash
# Security (MUST CHANGE)
SECRET_KEY=your-random-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars
DB_PASSWORD=strong-database-password

# Admin Account
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_PASSWORD=secure-admin-password

# Database
DATABASE_URL=postgresql://guardian:${DB_PASSWORD}@db:5432/guardian

# Domain (for production)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Generate Secure Keys

```python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run this twice to generate `SECRET_KEY` and `JWT_SECRET_KEY`.

## Deployment Methods

### Method 1: Docker Compose (Production-Ready)

**Pros**: Isolated, reproducible, includes database and Redis  
**Best for**: Production deployments, testing

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Method 2: Manual Deployment

**Pros**: Full control, easier debugging  
**Best for**: Development, custom infrastructure

```bash
# Install dependencies
pip install -r requirements-prod.txt

# Set environment variables
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@localhost/guardian
export SECRET_KEY=your-secret-key

# Initialize database
python3 -c "from web.production_app import create_app, db; app = create_app('production'); app.app_context().push(); db.create_all()"

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --worker-class eventlet -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker web.production_app:app
```

### Method 3: Cloud Platform (Heroku, AWS, GCP)

#### Heroku

```bash
# Install Heroku CLI
heroku create smart-login-guardian

# Add PostgreSQL
heroku addons:create heroku-postgresql:standard-0

# Add Redis
heroku addons:create heroku-redis:premium-0

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set JWT_SECRET_KEY=your-jwt-key
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main

# Open application
heroku open
```

#### AWS ECS (Docker)

```bash
# Build and tag image
docker build -t smart-login-guardian:latest .

# Tag for ECR
docker tag smart-login-guardian:latest \
  your-account-id.dkr.ecr.region.amazonaws.com/smart-login-guardian:latest

# Push to ECR
docker push your-account-id.dkr.ecr.region.amazonaws.com/smart-login-guardian:latest

# Deploy to ECS (use AWS Console or CLI)
```

## Database Setup

### PostgreSQL Configuration

```sql
-- Create database
CREATE DATABASE guardian;

-- Create user
CREATE USER guardian WITH PASSWORD 'strong-password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE guardian TO guardian;
```

### Migrations

```bash
# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade

# Rollback
flask db downgrade
```

### Backup & Restore

```bash
# Backup
docker-compose exec db pg_dump -U guardian guardian > backup.sql

# Restore
docker-compose exec -T db psql -U guardian guardian < backup.sql
```

## Security

### Production Checklist

- [ ] Change default admin password
- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Use PostgreSQL (not SQLite) in production
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable firewall (only ports 80, 443, 22)
- [ ] Regular security updates
- [ ] Enable database backups
- [ ] Use environment variables (never commit secrets)

### SSL/TLS with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Monitoring

### Health Check

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-11-08T12:00:00.000000"
}
```

### Logs

```bash
# Docker Compose
docker-compose logs -f app

# Application logs
tail -f /var/log/guardian/app.log

# Access logs
tail -f /var/log/nginx/access.log
```

### Metrics (Prometheus)

Add to `production_app.py`:

```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
```

Metrics available at `http://localhost:5000/metrics`

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  app:
    deploy:
      replicas: 4
    # ...load balancer configuration
```

### Performance Tuning

```bash
# Increase Gunicorn workers
gunicorn -w 8 -b 0.0.0.0:5000 web.production_app:app

# Enable caching
# Add Redis caching layer
```

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_login_events_timestamp ON login_events(timestamp);
CREATE INDEX idx_login_events_risk_score ON login_events(risk_score);
CREATE INDEX idx_login_events_username ON login_events(username);
CREATE INDEX idx_login_events_ip ON login_events(ip_address);

-- Analyze
ANALYZE login_events;
```

## Troubleshooting

### Common Issues

**Database connection error**
```bash
# Check database is running
docker-compose ps db

# Check connection
docker-compose exec app python -c "from web.production_app import create_app, db; app = create_app(); app.app_context().push(); print(db.engine.url)"
```

**WebSocket not connecting**
- Ensure nginx configured for WebSocket (see above)
- Check CORS settings
- Verify firewall allows port 5000

**High memory usage**
```bash
# Limit in docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M
```

## Maintenance

### Regular Tasks

```bash
# Update application
git pull
docker-compose up -d --build

# Cleanup old events (monthly)
docker-compose exec app python -c "from web.production_app import create_app; from guardian import LoginGuardian; app = create_app(); app.app_context().push(); guardian = app.guardian; guardian.cleanup_old_data(30)"

# Database backup (daily)
docker-compose exec db pg_dump -U guardian guardian | gzip > backup-$(date +%Y%m%d).sql.gz
```

### Updates

```bash
# Check for updates
git fetch
git log HEAD..origin/main --oneline

# Update
git pull
docker-compose down
docker-compose up -d --build
```

## Support

- 📧 Email: support@yourcompany.com
- 📖 Documentation: https://docs.yourcompany.com
- 🐛 Issues: https://github.com/yourcompany/smart-login-guardian/issues
- 💬 Community: https://discord.gg/yourserver

---

**Last Updated**: November 2026  
**Version**: 1.0.0
>>>>>>> REPLACE
