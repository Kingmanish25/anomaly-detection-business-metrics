# Deployment Guide — Anomaly Detection for Business Metrics

---

## Local Setup

### Prerequisites

- Python 3.11+
- (Optional) PostgreSQL 14+ for persistent storage
- (Optional) Redis for alert deduplication

### Install

```bash
git clone https://github.com/Kingmanish25/anomaly-detection-business-metrics.git
cd anomaly-detection-business-metrics

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env: set SLACK_WEBHOOK_URL, PAGERDUTY_ROUTING_KEY if needed
```

### Run

```bash
# API server
uvicorn anomaly_detection.api:app --reload --host 0.0.0.0 --port 8000

# Streamlit dashboard (separate terminal)
streamlit run dashboard/app.py --server.port 8501

# Verify
curl http://localhost:8000/health
```

### Run Tests

```bash
pytest tests/ -v
ruff check src/
```

---

## Docker

### Build

```bash
docker build -t anomaly-detector:latest .
```

### Run API Only

```bash
docker run -d \
  --name anomaly-detector \
  -p 8000:8000 \
  -e LOG_LEVEL=INFO \
  -e SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL}" \
  anomaly-detector:latest
```

---

## Docker Compose (Full Stack)

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build: .
    image: anomaly-detector:latest
    restart: unless-stopped
    command: uvicorn anomaly_detection.api:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: "postgresql://anomaly_user:${DB_PASSWORD}@postgres:5432/anomaly_db"
      REDIS_URL: "redis://redis:6379/0"
      SLACK_WEBHOOK_URL: "${SLACK_WEBHOOK_URL}"
      PAGERDUTY_ROUTING_KEY: "${PAGERDUTY_ROUTING_KEY}"
      LOG_LEVEL: "INFO"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dashboard:
    build: .
    image: anomaly-detector:latest
    restart: unless-stopped
    command: streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
    ports:
      - "8501:8501"
    environment:
      API_BASE_URL: "http://api:8000"
    depends_on:
      - api

  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: anomaly_db
      POSTGRES_USER: anomaly_user
      POSTGRES_PASSWORD: "${DB_PASSWORD}"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U anomaly_user -d anomaly_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"

volumes:
  postgres_data:
  redis_data:
```

```bash
# Create .env
cat > .env << 'EOF'
DB_PASSWORD=strong_password_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
PAGERDUTY_ROUTING_KEY=your_routing_key
EOF

docker compose up --build -d

# Verify all services
curl http://localhost:8000/health
open http://localhost:8501    # Streamlit dashboard
```

---

## Kubernetes

```yaml
# deployment/k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anomaly-detector-api
  namespace: anomaly-detection
spec:
  replicas: 3
  selector:
    matchLabels:
      app: anomaly-detector-api
  template:
    metadata:
      labels:
        app: anomaly-detector-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: api
          image: anomaly-detector:latest
          command: ["uvicorn", "anomaly_detection.api:app", "--host", "0.0.0.0", "--port", "8000"]
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: anomaly-db-secret
                  key: url
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: anomaly-detector-api
  namespace: anomaly-detection
spec:
  selector:
    app: anomaly-detector-api
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: anomaly-detector-hpa
  namespace: anomaly-detection
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: anomaly-detector-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

```bash
kubectl create namespace anomaly-detection
kubectl create secret generic anomaly-db-secret \
  --namespace anomaly-detection \
  --from-literal=url="postgresql://user:password@postgres-svc:5432/anomaly_db"

kubectl apply -f deployment/k8s/
kubectl get pods -n anomaly-detection
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | In-memory | PostgreSQL connection string |
| `REDIS_URL` | No | None | Redis for alert deduplication |
| `SLACK_WEBHOOK_URL` | No | None | Slack incoming webhook URL |
| `PAGERDUTY_ROUTING_KEY` | No | None | PagerDuty Events API v2 key |
| `DEFAULT_WINDOW_SIZE` | No | `30` | Default rolling window (observations) |
| `DEFAULT_ZSCORE_THRESHOLD` | No | `3.5` | Default anomaly flag threshold |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `ALERT_COOLDOWN_SECONDS` | No | `300` | Min seconds between repeat alerts |

---

## Monitoring & Observability

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Key metrics exposed:
# anomaly_detector_requests_total{endpoint, status}
# anomaly_detector_anomalies_detected_total{metric, severity}
# anomaly_detector_request_duration_seconds{endpoint}
# anomaly_detector_alerts_sent_total{channel}
```
