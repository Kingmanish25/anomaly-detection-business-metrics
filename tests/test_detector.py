import pandas as pd
import pytest

from anomaly_detection.detector import detect_anomalies


def test_spike_detected():
    vals=[100,101,99,100,102,98,101,1000]
    df=pd.DataFrame({"timestamp":pd.date_range("2026-01-01",periods=8,tz="UTC"),"metric":["x"]*8,"value":vals})
    assert bool(detect_anomalies(df,window=7,min_history=5).iloc[-1].is_anomaly)
def test_bad_threshold():
    with pytest.raises(ValueError): detect_anomalies(pd.DataFrame(columns=["timestamp","metric","value"]),threshold=0)
