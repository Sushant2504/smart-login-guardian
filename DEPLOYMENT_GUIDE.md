# 🚀 Smart Login Guardian - Complete Deployment Guide

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Production](#kubernetes-production)
5. [Security Configuration](#security-configuration)
6. [Monitoring & Observability](#monitoring--observability)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Quick Start

### Option 1: One-Command Start (Recommended for Demo)
```bash
chmod +x start.sh
./start.sh
# Select option 1 for 3D Interactive Demo
# Open http://localhost:8080
```

### Option 2: Manual Start
```bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic python-jose passlib scikit-learn numpy
python3 demo/final_complete_demo.py
```

---

## 💻 Local Development

### Prerequisites
- Python 3.11+
- pip or poetry
- Git

### Setup Steps
```bash
# 1. Clone repository
git clone <repository-url>
cd smart-login-guardian

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements-prod.txt

# 4. Copy environment template
cp .env.example .env

# 5. Edit .env with your settings
nano .env

# 6. Run application
python3 app.py
```

### Running Individual Services
```bash
# Authentication Service (Port 8001)
python3 services/auth-service/main.py

# Backend Service (Port 8002)
python3 services/backend/main.py

# Complete Application (Port 9000)
python3 app.py

# Interactive 3D Demo (Port 8080)
python3 demo/final_complete_demo.py
```

---

## 🐳 Docker Deployment

### Development Environment
```bash
# Start all services
docker-compose up -d

# Services started:
# - PostgreSQL (5432)
# - Redis (6379)
# - Redpanda/Kafka (19092)
# - ClickHouse (8123, 9000)
# - Backend API (8000)
# - Prometheus (9091)
# - Grafana (3000)

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Stop and remove volumes (CAUTION: Data loss!)
docker-compose down -v
```

### Production Environment
```bash
# 1. Set environment variables
export POSTGRES_PASSWORD=<strong-password>
export SECRET_KEY=$(openssl rand -hex 32)
export GRAFANA_PASSWORD=<admin-password>

# 2. Start production stack
docker-compose -f docker-compose.prod.yml up -d

# 3. Check health
docker-compose -f docker-compose.prod.yml ps

# 4. View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Building Custom Image
```bash
# Build
docker build -f Dockerfile.prod -t smart-login-guardian:1.0.0 .

# Run
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e SECRET_KEY=... \
  smart-login-guardian:1.0.0

# Push to registry
docker tag smart-login-guardian:1.0.0 your-registry/smart-login-guardian:1.0.0
docker push your-registry/smart-login-guardian:1.0.0
```

---

## ☸️ Kubernetes Production

### Prerequisites
- Kubernetes cluster (v1.25+)
- kubectl configured
- Persistent Volume provisioner
- Ingress controller (nginx/traefik)
- Cert-manager (for TLS)

### Deployment Steps

#### 1. Create Namespace
```bash
kubectl create namespace smart-login-guardian
kubectl config set-context --current --namespace=smart-login-guardian
```

#### 2. Create Secrets
```bash
# Generate secrets
export SECRET_KEY=$(openssl rand -hex 32)
export DB_PASSWORD=$(openssl rand -base64 24)

# Create Kubernetes secrets
kubectl create secret generic smart-login-guardian-secrets \
  --from-literal=database-url="postgresql://postgres:${DB_PASSWORD}@postgres:5432/smart_login_guardian" \
  --from-literal=redis-url="redis://redis:6379/0" \
  --from-literal=secret-key="${SECRET_KEY}" \
  --from-literal=jwt-secret="${SECRET_KEY}" \
  -n smart-login-guardian
```

#### 3. Deploy Database (PostgreSQL)
```bash
# Create PostgreSQL StatefulSet
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  ports:
  - port: 5432
  clusterIP: None
  selector:
    app: postgres
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: smart_login_guardian
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: smart-login-guardian-secrets
              key: database-password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 20Gi
EOF
```

#### 4. Deploy Redis
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  ports:
  - port: 6379
  selector:
    app: redis
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
EOF
```

#### 5. Deploy Application
```bash
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

#### 6. Deploy Ingress (with TLS)
```bash
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: smart-login-guardian-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/websocket-services: smart-login-guardian-backend
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: slg-tls-secret
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: smart-login-guardian-backend
            port:
              number: 8000
EOF
```

#### 7. Verify Deployment
```bash
# Check pods
kubectl get pods

# Check services
kubectl get svc

# Check ingress
kubectl get ingress

# View logs
kubectl logs -f deployment/smart-login-guardian-backend

# Port-forward for testing
kubectl port-forward svc/smart-login-guardian-backend 8000:8000
```

---

## 🔐 Security Configuration

### SSL/TLS Setup

#### Using Cert-Manager
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Secrets Management

#### Using Sealed Secrets
```bash
# Install sealed-secrets
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create sealed secret
kubeseal --format=yaml < secret.yaml > sealed-secret.yaml
kubectl apply -f sealed-secret.yaml
```

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
spec:
  podSelector:
    matchLabels:
      app: smart-login-guardian
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

---

## 📊 Monitoring & Observability

### Prometheus Metrics
```bash
# Access metrics
curl http://localhost:8000/metrics

# Example metrics:
# - slg_events_total
# - slg_risk_scores
# - slg_detection_duration_seconds
# - slg_api_requests_total
```

### Grafana Dashboards
```bash
# Access Grafana
http://localhost:3000

# Default credentials:
# Username: admin
# Password: (from environment variable)

# Import dashboards:
# - Dashboard ID: 15759 (Node Exporter)
# - Dashboard ID: 12708 (FastAPI)
# - Custom: infrastructure/grafana/dashboards/smart-login-guardian.json
```

### Logging
```bash
# View application logs
kubectl logs -f deployment/smart-login-guardian-backend

# View all container logs
kubectl logs -f deployment/smart-login-guardian-backend --all-containers=true

# View previous container logs
kubectl logs deployment/smart-login-guardian-backend --previous
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check database service
kubectl get svc postgres
kubectl describe svc postgres

# Test connection
kubectl run -it --rm debug --image=postgres:15-alpine --restart=Never -- \
  psql -h postgres -U postgres -d smart_login_guardian

# Check logs
kubectl logs statefulset/postgres
```

#### 2. Redis Connection Failed
```bash
# Check Redis
kubectl get pods -l app=redis
kubectl logs deployment/redis

# Test connection
kubectl run -it --rm debug --image=redis:7-alpine --restart=Never -- \
  redis-cli -h redis ping
```

#### 3. High Memory Usage
```bash
# Check resource usage
kubectl top pods
kubectl top nodes

# Describe pod for details
kubectl describe pod <pod-name>

# Adjust resources in deployment.yaml
resources:
  limits:
    memory: "2Gi"
    cpu: "1000m"
  requests:
    memory: "512Mi"
    cpu: "250m"
```

#### 4. WebSocket Not Working
```bash
# Ensure Ingress has WebSocket annotations
nginx.ingress.kubernetes.io/websocket-services: smart-login-guardian-backend
nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"

# Check backend logs for WebSocket connections
kubectl logs -f deployment/smart-login-guardian-backend | grep -i websocket
```

#### 5. Pods Crashing (CrashLoopBackOff)
```bash
# Check pod status
kubectl get pods
kubectl describe pod <pod-name>

# View logs
kubectl logs <pod-name>
kubectl logs <pod-name> --previous

# Common fixes:
# - Check secrets exist: kubectl get secrets
# - Verify environment variables
# - Check resource limits
# - Ensure dependencies are ready
```

### Performance Tuning

```bash
# Scale horizontally
kubectl scale deployment smart-login-guardian-backend --replicas=5

# Configure HPA
kubectl autoscale deployment smart-login-guardian-backend \
  --cpu-percent=70 \
  --min=3 \
  --max=10

# Verify HPA
kubectl get hpa
```

---

## 📞 Support Resources

**Documentation:**
- Architecture: `/docs/ARCHITECTURE.md`
- API Reference: `http://localhost:8000/docs`
- README: `/README_COMPLETE.md`

**Monitoring:**
- Health Check: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9091`
- Grafana: `http://localhost:3000`

**Logs:**
```bash
# Application logs
docker-compose logs -f backend

# Kubernetes logs
kubectl logs -f deployment/smart-login-guardian-backend
```

---

## ✅ Pre-Deployment Checklist

- [ ] All tests passing (`pytest tests/ -v`)
- [ ] Security scan completed (`trivy fs .`)
- [ ] Environment variables configured
- [ ] Secrets generated and stored securely
- [ ] Database schema initialized
- [ ] Backup strategy configured
- [ ] Monitoring dashboards ready
- [ ] SSL/TLS certificates configured
- [ ] DNS records configured
- [ ] Firewall rules configured
- [ ] Rate limiting configured
- [ ] CORS settings verified
- [ ] Log aggregation configured
- [ ] Alert rules configured
- [ ] Runbook documented
- [ ] Team trained

---

**Deployment Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** 2026-11-15
