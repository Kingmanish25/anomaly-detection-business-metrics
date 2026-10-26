import io, logging, time
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from anomaly_detection.config import settings
from anomaly_detection.detector import detect_anomalies
from anomaly_detection.validation import normalize_records
log=logging.getLogger("anomaly_api")
app=FastAPI(title="Business Metrics Anomaly Detection API",version="1.0.0")
REQ=Counter("http_requests_total","HTTP requests",["method","path","status"])
LAT=Histogram("http_request_duration_seconds","Request latency",["path"])
OBS=Counter("anomaly_observations_total","Observations scored",["result"])
class DetectRequest(BaseModel):
    records: list[dict] = Field(min_length=1,max_length=100000)
    threshold: float|None=Field(default=None,gt=0,le=100)
    window: int|None=Field(default=None,ge=2,le=365)
    min_history: int|None=Field(default=None,ge=2,le=365)
@app.middleware("http")
async def timing(req: Request, call_next):
    start=time.perf_counter(); status=500
    try:
        res=await call_next(req); status=res.status_code; return res
    finally:
        REQ.labels(req.method,req.url.path,str(status)).inc(); LAT.labels(req.url.path).observe(time.perf_counter()-start)
@app.get("/")
def root(): return {"service":"business-metrics-anomaly-detection","version":"1.0.0","docs":"/docs"}
@app.get("/health")
def health(): return {"status":"ok","environment":settings.app_env}
@app.get("/metrics")
def metrics(): return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
@app.post("/detect")
def detect(payload: DetectRequest):
    try:
        df=normalize_records(payload.records); w=payload.window or settings.window; h=payload.min_history or settings.min_history
        if h>w: raise ValueError("min_history must be <= window")
        out=detect_anomalies(df,payload.threshold or settings.threshold,w,h)
        out["timestamp"]=out.timestamp.astype(str); out=out.astype(object).where(pd.notna(out),None)
        n=int(out.is_anomaly.sum()); OBS.labels("anomaly").inc(n); OBS.labels("normal").inc(len(out)-n)
        log.info("detection_completed count=%s anomalies=%s",len(out),n)
        return {"count":len(out),"anomaly_count":n,"results":out.to_dict("records")}
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
@app.post("/ingest")
async def ingest(file: UploadFile=File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"): raise HTTPException(status_code=400,detail="upload a .csv file")
    content=await file.read(settings.max_upload_bytes+1)
    if len(content)>settings.max_upload_bytes: raise HTTPException(status_code=413,detail="upload too large")
    try:
        df=pd.read_csv(io.BytesIO(content))
        if not {"timestamp","metric","value"}.issubset(df.columns): raise ValueError("CSV requires timestamp, metric, value")
        out=normalize_records(df.where(pd.notna(df),None).to_dict("records")); out["timestamp"]=out.timestamp.astype(str)
        return {"count":len(out),"records":out.to_dict("records")}
    except Exception as exc: raise HTTPException(status_code=422,detail=f"invalid CSV: {exc}") from exc
