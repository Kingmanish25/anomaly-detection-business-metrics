# Anomaly Detection for Business Metrics — Master Production Guide

> **AI-Powered Business Metrics Anomaly Detection Platform**  
> Real-time statistical and ML-based anomaly detection for operational KPIs

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [System Architecture](#2-system-architecture)
3. [Detection Workflow](#3-detection-workflow)
4. [Installation & Quick Start](#4-installation--quick-start)
5. [Configuration Reference](#5-configuration-reference)
6. [API Reference](#6-api-reference)
7. [Deployment Guide](#7-deployment-guide)
8. [Real-World Use Cases](#8-real-world-use-cases)
9. [Monitoring & Alerting](#9-monitoring--alerting)
10. [Production Checklist](#10-production-checklist)

---

## 1. Product Overview

**Anomaly Detection for Business Metrics** is a production-grade platform for detecting statistical anomalies across business KPIs — revenue, conversion rates, infrastructure metrics, SLA compliance, and more. It combines classical statistical methods with ML-based models to provide explainable alerts with business context.

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-Method Detection** | Isolation Forest, Z-score, IQR, LSTM autoencoder |
| **Real-Time & Batch** | Stream detection for live metrics + batch for historical analysis |
| **Business Context** | Annotates anomalies with probable business causes |
| **Interactive Dashboard** | Streamlit-based visualization with drill-down |
| **Alert Integration** | Webhook/Slack/email notification pipeline |
| **Explainability** | SHAP-based feature attribution for each anomaly |

### Technology Stack

```
Core ML:       scikit-learn, PyTorch / statsmodels
API:           FastAPI
Dashboard:     Streamlit / Plotly
Database:      PostgreSQL (production) / SQLite (development)
Queue:         Redis / in-memory
Deployment:    Docker + Kubernetes
Monitoring:    Prometheus + Grafana
```

---

## 2. System Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                  ANOMALY DETECTION PLATFORM                   │
│                                                               │
│  Data Sources          Ingestion           Detection          │
│  ┌──────────┐         ┌─────────┐         ┌──────────────┐   │
│  │ Time     │──REST──►│ Ingest  │────────►│ Detection    │   │
│  │ Series   │         │ Layer   │         │ Engine       │   │
│  │ APIs     │──Stream►│ (Kafka/ │         │ ┌──────────┐ │   │
│  │ Databases│         │  Redis) │         │ │Isolation │ │   │
│  │ CSVs     │         └─────────┘         │ │Forest    │ │   │
│  └──────────┘                             │ │Z-Score   │ │   │
│                                           │ │IQR       │ │   │
│  ┌───────────────────────────────┐        │ │LSTM AE   │ │   │
│  │         DASHBOARD             │        │ └──────────┘ │   │
│  │  Streamlit + Plotly           │◄───────┤              │   │
│  │  • Real-time metric charts    │        └──────┬───────┘   │
│  │  • Anomaly drill-down         │               │           │
│  │  • Alert management           │       ┌───────▼───────┐   │
│  └───────────────────────────────┘       │  Alert Engine │   │
│                                          │  Slack/Email/ │   │
│  ┌────────────────────────┐              │  Webhook      │   │
│  │   FastAPI REST API     │              └───────────────┘   │
│  │   /ingest /detect      │                                  │
│  │   /anomalies /explain  │                                  │
│  └────────────────────────┘                                  │
└───────────────────────────────────────────────────────────────┘
```

---

## 3. Detection Workflow

```
Raw Metric Data
     │
     ▼
[Data Ingestion] → Validates schema, normalizes timestamps
     │
     ▼
[Feature Engineering] → Rolling stats, lag features, seasonality decomposition
     │
     ▼
[Detection Ensemble]
     ├── Isolation Forest (global outlier)
     ├── Z-Score (statistical deviation)
     ├── IQR (inter-quartile range)
     └── LSTM Autoencoder (temporal pattern)
     │
     ▼
[Ensemble Voting] → Majority/weighted vote → Anomaly Score (0-1)
     │
     ├── Score < threshold → Normal
     │
     └── Score ≥ threshold → [Explainer] → SHAP Attribution
                                  │
                             [Alert Engine] → Slack / Email / Webhook
                                  │
                             [Dashboard Update] → Real-time visualization
                                  │
                             [Database Storage] → Audit log + history
```

---

## 4. Installation & Quick Start

### Prerequisites

```
Python 3.9+, Docker (optional), Redis (optional for streaming)
```

### Install

```bash
git clone https://github.com/Kingmanish25/anomaly-detection-business-metrics.git
cd anomaly-detection-business-metrics
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"   # installs from pyproject.toml
```

### Configure

```bash
cp .env.example .env
# Set: DATABASE_URL, REDIS_URL, SLACK_WEBHOOK_URL, API_KEY
```

### Run Development Server

```bash
# API server
make dev-api
# or: uvicorn src.api.main:app --reload --port 8000

# Dashboard
make dev-dashboard
# or: streamlit run dashboard/app.py --server.port 8501

# Full stack with Docker
docker-compose up -d
```

### Ingest Sample Data

```bash
# Load sample business metrics
python scripts/load_sample_data.py

# Verify ingestion
curl http://localhost:8000/api/v1/metrics/summary
```

---

## 5. Configuration Reference

### `.env` Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | sqlite:///dev.db | Database connection string |
| `REDIS_URL` | ❌ | None | Redis for streaming (optional) |
| `SLACK_WEBHOOK_URL` | ❌ | None | Slack alert channel webhook |
| `ALERT_EMAIL` | ❌ | None | Email alert recipient |
| `API_KEY` | ✅ | — | API authentication key |
| `ANOMALY_THRESHOLD` | ❌ | 0.75 | Detection sensitivity (0-1) |
| `WINDOW_SIZE` | ❌ | 24 | Rolling window size (hours) |
| `BATCH_SIZE` | ❌ | 1000 | Ingestion batch size |

### Detection Algorithm Config (`configs/detection.yaml`)

```yaml
detection:
  ensemble:
    isolation_forest:
      enabled: true
      contamination: 0.05
      weight: 0.3
    zscore:
      enabled: true
      threshold: 3.0
      weight: 0.25
    iqr:
      enabled: true
      k_factor: 1.5
      weight: 0.2
    lstm_autoencoder:
      enabled: true
      threshold_percentile: 95
      weight: 0.25
  voting: weighted_average
  final_threshold: 0.75
```

---

## 6. API Reference

### Endpoints

```
POST   /api/v1/metrics/ingest        Ingest metric data points
GET    /api/v1/metrics/summary       Summary statistics
POST   /api/v1/detect                Run anomaly detection on dataset
GET    /api/v1/anomalies             List detected anomalies
GET    /api/v1/anomalies/{id}        Get anomaly details
GET    /api/v1/anomalies/{id}/explain  SHAP explanation
PUT    /api/v1/anomalies/{id}/label  Label anomaly (true/false positive)
GET    /api/v1/health                Health check
```

### Example: Ingest Metric Data

```bash
curl -X POST http://localhost:8000/api/v1/metrics/ingest \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "daily_revenue",
    "timestamp": "2024-01-15T10:00:00Z",
    "value": 52430.0,
    "dimensions": {
      "region": "us-east",
      "product": "premium"
    }
  }'
```

### Example: Run Detection

```bash
curl -X POST http://localhost:8000/api/v1/detect \
  -H "X-API-Key: your-api-key" \
  -d '{"metric_name": "daily_revenue", "window_hours": 168}'
```

### Example: Get Explanation

```bash
curl http://localhost:8000/api/v1/anomalies/123/explain \
  -H "X-API-Key: your-api-key"

# Response:
{
  "anomaly_id": 123,
  "score": 0.87,
  "top_features": [
    {"feature": "hour_of_day", "shap_value": 0.42},
    {"feature": "day_of_week", "shap_value": 0.28},
    {"feature": "lag_24h_delta", "shap_value": 0.17}
  ],
  "narrative": "Revenue dropped 34% vs same hour yesterday, primarily driven by off-peak timing and weekend effect."
}
```

---

## 7. Deployment Guide

### Docker

```bash
docker build -t anomaly-detection:latest .
docker run -d -p 8000:8000 -p 8501:8501 \
  --env-file .env \
  anomaly-detection:latest
```

### Docker Compose (Full Stack)

```bash
docker-compose up -d
# Starts: API (8000), Dashboard (8501), PostgreSQL (5432), Redis (6379)
```

### Kubernetes (Production)

```bash
# Apply manifests
kubectl apply -f deployment/k8s/ -n monitoring

# Scale horizontally
kubectl scale deployment anomaly-api --replicas=3 -n monitoring

# Check status
kubectl get pods -n monitoring
```

### AWS Deployment

```bash
# ECS Fargate
aws ecs create-cluster --cluster-name anomaly-detection-prod
aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com
docker tag anomaly-detection:latest $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/anomaly-detection:latest
docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/anomaly-detection:latest
```

### GCP Cloud Run

```bash
gcloud run deploy anomaly-detection \
  --image gcr.io/$PROJECT_ID/anomaly-detection:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi --cpu 2 \
  --set-env-vars DATABASE_URL=$DATABASE_URL
```

---

## 8. Real-World Use Cases

### Use Case 1: E-Commerce Revenue Monitoring
**Scenario:** Online retailer monitors hourly revenue across 50 product categories.
**Detection:** LSTM autoencoder detects 3-sigma drop in checkout conversion at 2pm.
**Action:** Auto-alert to engineering team → discovers payment gateway timeout.
**Impact:** Issue resolved in 15 minutes vs 4-hour manual discovery.

### Use Case 2: SaaS Platform Health Monitoring
**Scenario:** SaaS company monitors API latency, error rates, and DAU/MAU ratios.
**Detection:** Isolation Forest flags abnormal error rate cluster in EU region.
**Action:** PagerDuty webhook triggers → on-call engineer investigates CDN issue.

### Use Case 3: Manufacturing OEE (Overall Equipment Effectiveness)
**Scenario:** Factory monitors machine throughput, downtime, and defect rates.
**Detection:** IQR detector catches defect rate spike before shift supervisor notices.
**Action:** Maintenance ticket auto-created → preventative maintenance scheduled.

### Use Case 4: Financial Transaction Surveillance
**Scenario:** Bank monitors daily transaction volumes per branch/ATM.
**Detection:** Z-score flags 10x ATM withdrawal spike at specific location.
**Action:** Fraud team alerted within 2 minutes → card skimmer discovered.

### Use Case 5: Marketing Campaign Performance
**Scenario:** Marketing monitors CTR, CPC, and conversion rates across ad campaigns.
**Detection:** Ensemble detects CTR collapse on Facebook campaigns at campaign launch.
**Action:** Campaign auto-paused via webhook to ad platform → budget saved.

---

## 9. Monitoring & Alerting

### Key Dashboard Metrics

| Panel | Metric | Alert If |
|-------|--------|----------|
| Detection Rate | Anomalies per hour | > 10x baseline |
| False Positive Rate | Labeled false positives / total | > 20% |
| Precision@K | Top-K anomaly quality | < 70% |
| Detection Latency | Time to detect from ingest | > 5 min |
| API Latency | /detect P99 response time | > 2s |
| Model Staleness | Hours since last retrain | > 168h (1 week) |

### Prometheus Scrape Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'anomaly-detection'
    static_configs:
      - targets: ['anomaly-api:8000']
    metrics_path: '/metrics'
```

### Auto-Retraining Trigger

```python
# Schedule weekly model retraining
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(retrain_all_models, trigger="cron", day_of_week="sun", hour=2)
scheduler.start()
```

---

## 10. Production Checklist

- [ ] `DATABASE_URL` pointing to PostgreSQL (not SQLite)
- [ ] `API_KEY` set to cryptographically strong random value
- [ ] Anomaly `ANOMALY_THRESHOLD` calibrated on historical data
- [ ] LSTM autoencoder pre-trained on at least 30 days of data
- [ ] Alert webhooks tested (Slack/email/PagerDuty)
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Prometheus metrics endpoint accessible
- [ ] Grafana dashboard imported from `monitoring/grafana/`
- [ ] False positive labeling workflow established
- [ ] Weekly retraining job scheduled
- [ ] Data retention policy set (default: 90 days)
- [ ] API rate limiting configured (max 1000 req/min)
- [ ] TLS certificate configured for HTTPS
- [ ] Runbooks available in `runbooks/` directory

---

*Anomaly Detection for Business Metrics — Production Guide | Kingmanish25 Portfolio*
