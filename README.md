# Anomaly Detection for Business Metrics

> Production-ready FastAPI + Streamlit system for explainable, real-time anomaly detection on business KPIs

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Problem Statement

Business KPIs — revenue, orders, conversion rates, churn, SLA metrics — change constantly. When they change *abnormally*, the right teams must be alerted within minutes, not hours. This system provides:

- **Statistical anomaly detection** using rolling median/MAD baselines (no training required)
- **Explainable scores**: every anomaly flag includes a robust z-score, direction, and severity label
- **Multi-metric support**: plug in any time-series metric with a timestamp
- **Real-time API**: REST endpoint for streaming integration with data pipelines
- **Streamlit dashboard**: operational visibility for non-technical stakeholders
- **Alert routing**: configurable webhooks for Slack, PagerDuty, email

---

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full component diagram and data flow.

```
Metrics Source                API / CLI / Dashboard
(DB, Kafka, webhook)                │
        │                           │
        ▼                           ▼
┌───────────────────────────────────────────────────┐
│              Metrics Ingestion Layer               │
│  Schema validation · Deduplication · Type coerce  │
└────────────────────────┬──────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────┐
│            Statistical Baseline Engine             │
│  Rolling median · MAD · Robust z-score            │
└────────────────────────┬──────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────┐
│             Anomaly Scoring & Flagging             │
│  Threshold gate · Severity (LOW/MED/HIGH/CRITICAL) │
└────────────────────────┬──────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────┐
│                Alert Generation                    │
│  Slack · PagerDuty · Email · Webhook               │
└───────────────────────────────────────────────────┘
```

---

## Quick Start

### Python (3.11+)

```bash
git clone https://github.com/Kingmanish25/anomaly-detection-business-metrics.git
cd anomaly-detection-business-metrics

pip install -e ".[dev]"

# Start API
uvicorn anomaly_detection.api:app --reload --host 0.0.0.0 --port 8000

# Start Streamlit dashboard
streamlit run dashboard/app.py
```

- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501

### Docker

```bash
cp .env.example .env
docker compose up --build
```

---

## API Reference

### `POST /detect`

Detect anomalies in a batch of metric observations.

**Request**
```json
{
  "records": [
    {
      "timestamp": "2024-01-15T14:00:00Z",
      "metric": "daily_revenue",
      "value": 145000.0,
      "source": "stripe"
    }
  ],
  "window_size": 30,
  "threshold_zscore": 3.5
}
```

**Response**
```json
{
  "results": [
    {
      "timestamp": "2024-01-15T14:00:00Z",
      "metric": "daily_revenue",
      "value": 145000.0,
      "baseline_median": 98000.0,
      "robust_zscore": 4.7,
      "is_anomaly": true,
      "direction": "UP",
      "severity": "HIGH",
      "explanation": "Value is 4.7σ above 30-day rolling median (48.0% above baseline)"
    }
  ],
  "anomaly_count": 1,
  "total_records": 1
}
```

### `GET /health`
Liveness check. Returns `{"status": "ok"}`.

### `GET /metrics`
Prometheus-format process metrics.

### `POST /alerts/configure`
Configure alert routing for a metric.

---

## Algorithm

The detector uses **robust statistics** to avoid sensitivity to outliers in the baseline itself:

```
1. For each new observation (metric M, value V, timestamp T):
2. Retrieve past W observations for metric M (rolling window)
3. Compute: baseline = median(past_values)
4. Compute: MAD = median(|past_values - baseline|)
5. Robust z-score = 0.6745 * (V - baseline) / MAD
   (0.6745 normalizes MAD to approximate standard deviation)
6. Flag as anomaly if |robust_z| > threshold (default 3.5)
7. Assign severity:
   - |z| > 5.0 → CRITICAL
   - |z| > 4.0 → HIGH
   - |z| > 3.5 → MEDIUM
   - else      → LOW (not flagged)
```

**Why robust z-score?** Standard z-score is distorted by the very anomalies you're trying to detect. Median/MAD-based scoring is resistant to contamination in the historical window.

---

## Real-World Use Cases

See [`REAL_WORLD_USE_CASES.md`](REAL_WORLD_USE_CASES.md) for full industry scenarios.

1. **Revenue Anomaly Detection** — e-commerce GMV drops, payment gateway failures
2. **Marketing Campaign Monitoring** — conversion rate spikes/drops post-launch
3. **SLA Violation Detection** — API latency and error rate breach detection

---

## Deployment

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for local, Docker, and Kubernetes guides.

---

## Testing

```bash
# Full test suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Lint
ruff check src/ tests/
```

---

## Data Contract

Inputs require:
- `timestamp`: ISO-8601 datetime string
- `metric`: non-empty string identifier
- `value`: finite numeric value
- `source` (optional): string identifier of the data source

Duplicate `(timestamp, metric)` pairs are rejected with a 422 error.

---

## Limitations

- Rolling median/MAD does not model seasonality or trend — use Prophet or STL decomposition for seasonal KPIs
- Window size must be tuned per metric; 30-day default may be too short for weekly-seasonal data
- No persistent database in local demo mode — use PostgreSQL via docker-compose for production
- No authentication enabled by default — deploy behind an authenticated gateway before exposing publicly

See `docs/`, `runbooks/`, and `monitoring/` for production hardening guides.

---

## Project Layout

```text
anomaly-detection-business-metrics/
├── src/anomaly_detection/
│   ├── api.py            # FastAPI app, endpoints
│   ├── detector.py       # Core robust z-score detection
│   ├── baseline.py       # Rolling median/MAD engine
│   ├── alerts.py         # Alert routing (Slack, PagerDuty, email)
│   └── models.py         # Pydantic schemas
├── dashboard/
│   └── app.py            # Streamlit dashboard
├── tests/                # Unit, API, regression, load tests
├── sample_data/          # Synthetic business metrics CSV
├── deployment/           # Kubernetes manifests
├── monitoring/           # Prometheus + Grafana config
├── runbooks/             # Incident response, rollback
├── docs/                 # Architecture, ADRs, threat model
├── ARCHITECTURE.md
├── REAL_WORLD_USE_CASES.md
├── DEPLOYMENT.md
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## License

MIT — see [LICENSE](LICENSE).
