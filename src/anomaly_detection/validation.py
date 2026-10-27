import math

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MetricRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timestamp: str
    metric: str = Field(min_length=1, max_length=100)
    value: float
    source: str | None = Field(default=None, max_length=100)
    @field_validator("timestamp")
    @classmethod
    def timestamp_ok(cls, v):
        try: return pd.to_datetime(v, utc=True, errors="raise").isoformat()
        except Exception as exc: raise ValueError("timestamp must be ISO-8601") from exc
    @field_validator("metric")
    @classmethod
    def metric_ok(cls, v):
        v=v.strip()
        if not v: raise ValueError("metric cannot be blank")
        return v
    @field_validator("value")
    @classmethod
    def value_ok(cls, v):
        if not math.isfinite(v): raise ValueError("value must be finite")
        return v
def normalize_records(records):
    if not records: raise ValueError("at least one record is required")
    df=pd.DataFrame([MetricRecord.model_validate(x).model_dump() for x in records])
    df["timestamp"]=pd.to_datetime(df.timestamp,utc=True)
    if df.duplicated(["timestamp","metric"]).any(): raise ValueError("duplicate (timestamp, metric) pairs")
    return df.sort_values(["metric","timestamp"]).reset_index(drop=True)
