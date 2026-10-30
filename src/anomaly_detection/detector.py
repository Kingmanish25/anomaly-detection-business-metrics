import numpy as np
import pandas as pd


def detect_anomalies(frame, threshold=3.5, window=14, min_history=7):
    if threshold <= 0: raise ValueError("threshold must be greater than zero")
    if window < 2 or min_history < 2 or min_history > window: raise ValueError("require window >= min_history >= 2")
    missing={"timestamp","metric","value"}-set(frame.columns)
    if missing: raise ValueError(f"missing columns: {sorted(missing)}")
    if frame.empty: return frame.assign(baseline=[],robust_z=[],is_anomaly=[],direction=[],severity=[])
    out=frame.copy()
    out["timestamp"]=pd.to_datetime(out.timestamp,utc=True,errors="raise")
    out["value"]=pd.to_numeric(out.value,errors="raise")
    if not np.isfinite(out.value.to_numpy(dtype=float)).all(): raise ValueError("values must be finite")
    out=out.sort_values(["metric","timestamp"]).reset_index(drop=True)
    baselines=[]; scores=[]
    for _,g in out.groupby("metric",sort=False):
        prior=g.value.shift(1)
        med=prior.rolling(window,min_periods=min_history).median()
        mad=(prior-med).abs().rolling(window,min_periods=min_history).median()
        floor=np.maximum(med.abs().fillna(0)*1e-9,1e-9)
        denom=(1.4826*mad).where(mad>0,floor)
        baselines.extend(med.tolist()); scores.extend(((g.value-med)/denom).tolist())
    out["baseline"]=baselines; out["robust_z"]=scores
    out["is_anomaly"]=out.robust_z.abs().ge(threshold)&out.baseline.notna()
    out["direction"]=np.select([out.value>out.baseline,out.value<out.baseline],["high","low"],default="normal")
    out.loc[~out.is_anomaly,"direction"]="normal"
    out["severity"]=np.select([out.robust_z.abs().ge(threshold*2),out.is_anomaly],["critical","warning"],default="normal")
    return out
