# Anomaly Detection for Business Metrics
FastAPI + Streamlit reference application for explainable business time-series anomaly detection.

## Run
Python 3.11+: `pip install -e ".[dev]"`, then `uvicorn anomaly_detection.api:app --reload` and `streamlit run dashboard/app.py`.
Docker: copy `.env.example` to `.env`, then `docker compose up --build`.
API docs: http://localhost:8000/docs. Dashboard: http://localhost:8501.

## Contract and algorithm
Inputs require ISO-8601 `timestamp`, nonblank `metric`, finite numeric `value`; optional `source`. Duplicate timestamp/metric pairs are rejected. Uses past-only rolling median/MAD, emits baseline, robust z-score, anomaly flag, direction and severity. Validate on labeled historical data before business use; synthetic demo data does not establish production accuracy.

## Safety and operations
This demo has no authentication and no durable storage. Do not expose publicly or upload confidential data. Production requires authentication/authorization, TLS, rate limits, managed secrets, durable storage, backups, and load/security review. See `docs/`, `monitoring/`, and `runbooks/`.
