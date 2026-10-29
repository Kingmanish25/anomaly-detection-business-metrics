# Architecture — Anomaly Detection for Business Metrics

## Overview

A **stateless, horizontally scalable** anomaly detection service. Each API call is self-contained: it receives a batch of metric observations, computes rolling baselines from the provided window, scores anomalies, and returns results. No model training or persistent ML state required.

---

## System Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                 Anomaly Detection for Business Metrics                  │
│                                                                        │
│  Data Sources          Ingestion Layer         Processing              │
│  ─────────────         ───────────────         ──────────              │
│  ┌──────────┐                                                          │
│  │ REST API │──►┐                                                      │
│  └──────────┘   │    ┌─────────────────────┐                          │
│  ┌──────────┐   ├───►│  Schema Validator   │                          │
│  │  Kafka   │──►│    │  (Pydantic v2)      │                          │
│  └──────────┘   │    │  • ISO-8601 ts      │                          │
│  ┌──────────┐   │    │  • finite numeric   │                          │
│  │  CLI     │──►┘    │  • dedup check      │                          │
│  └──────────┘        └──────────┬──────────┘                          │
│  ┌──────────┐                   │                                      │
│  │Streamlit │                   ▼                                      │
│  │Dashboard │        ┌─────────────────────┐                          │
│  └──────────┘        │  Baseline Engine    │                          │
│                       │  • Rolling median  │                          │
│                       │  • MAD computation │                          │
│                       │  • Window: 7-365d  │                          │
│                       └──────────┬──────────┘                          │
│                                  │                                     │
│                                  ▼                                     │
│                       ┌─────────────────────┐                          │
│                       │  Anomaly Scorer     │                          │
│                       │  • Robust z-score   │                          │
│                       │  • Severity rating  │                          │
│                       │  • Direction flag   │                          │
│                       └──────────┬──────────┘                          │
│                                  │                                     │
│             ┌────────────────────┼────────────────────┐               │
│             │                    │                    │               │
│             ▼                    ▼                    ▼               │
│   ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐       │
│   │  API Response    │  │ Alert Router │  │  Audit Log       │       │
│   │  (JSON)          │  │  Slack/PD/   │  │  (JSONL append)  │       │
│   └──────────────────┘  │  Email/Hook  │  └──────────────────┘       │
│                          └──────────────┘                              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
1. INGEST
   Client submits batch: [{timestamp, metric, value, source?}]
   Validator: ISO-8601 parse, finite-numeric check, dedup on (timestamp, metric)

2. BASELINE COMPUTATION
   For each unique metric in batch:
     - Retrieve past W observations (from request context or in-memory cache)
     - Compute rolling median and MAD
     - If window < min_window (default: 7), return score=0, no_baseline flag

3. ANOMALY SCORING
   robust_z = 0.6745 * (value - median) / max(MAD, epsilon)
   Severity assignment:
     |z| > 5.0  → CRITICAL
     |z| > 4.0  → HIGH
     |z| > 3.5  → MEDIUM
     else       → not flagged

4. ALERT ROUTING
   If anomaly AND metric has alert rule configured:
     - Evaluate cooldown (avoid alert storms)
     - Dispatch to configured channels
     - Log alert event to audit JSONL

5. RESPONSE
   Return enriched records: original fields + baseline, zscore, is_anomaly,
   direction, severity, explanation string
```

---

## Component Descriptions

### Schema Validator (`anomaly_detection/models.py`)
- Pydantic v2 models for request/response
- Coerces timestamps to UTC
- Rejects: NaN/Inf values, empty metric names, duplicate (ts, metric) pairs
- Returns structured 422 errors with field-level detail

### Baseline Engine (`anomaly_detection/baseline.py`)
- Pure Python / NumPy — no ML framework dependency
- Sliding window over sorted timestamp order
- Configurable window size per metric (default: 30 observations)
- Returns: `{median, mad, window_size_used, confidence}`

### Anomaly Scorer (`anomaly_detection/detector.py`)
- Stateless function: `score(value, baseline) → AnomalyScore`
- Epsilon guard on MAD=0 (flat signal): returns z=0, no anomaly
- Configurable thresholds per metric (loaded from YAML or DB)

### Alert Router (`anomaly_detection/alerts.py`)
- Pluggable dispatchers: Slack webhook, PagerDuty Events API, SMTP email
- Per-metric cooldown: minimum seconds between repeat alerts for same metric
- Alert deduplication by (metric, severity, direction) within cooldown window
- Async dispatch — never blocks API response

### FastAPI App (`anomaly_detection/api.py`)
- `/detect` — main detection endpoint
- `/health` — liveness
- `/metrics` — Prometheus exposition
- `/alerts/configure` — CRUD for alert rules
- Structured logging with request-id correlation

### Streamlit Dashboard (`dashboard/app.py`)
- Metric selector + time-range picker
- Time-series chart with anomaly markers
- Alert history table
- Real-time mode: auto-refresh every 30s

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|----------|
| Algorithm | Rolling median/MAD | No training; robust to outliers in baseline window |
| Stateless API | No persistent model state | Scales horizontally; idempotent reruns |
| Async alerts | Fire-and-forget via asyncio | Alert latency should not impact API response time |
| Pydantic v2 | Schema validation | Fast, typed, self-documenting API contracts |
| JSONL audit log | Append-only file | Survives partial runs; no DB dependency for audit |
| No auth by default | Plain HTTP | Forces operator to explicitly add auth layer — safer than false sense of security |

---

## Configuration Reference

```yaml
# configs/default.yaml
detection:
  default_window_size: 30         # observations in rolling window
  default_threshold_zscore: 3.5   # anomaly flag threshold
  min_window_size: 7              # min observations for a valid baseline
  epsilon: 1e-8                   # MAD=0 guard

alerts:
  enabled: true
  default_cooldown_seconds: 300   # 5 min between repeat alerts
  channels:
    slack:
      enabled: false
      webhook_url: "${SLACK_WEBHOOK_URL}"
    pagerduty:
      enabled: false
      routing_key: "${PAGERDUTY_ROUTING_KEY}"

api:
  host: "0.0.0.0"
  port: 8000
  log_level: "INFO"
  request_timeout_seconds: 30
```
