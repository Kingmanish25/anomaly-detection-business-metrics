from fastapi.testclient import TestClient

from anomaly_detection.api import app

c=TestClient(app)
def test_health(): assert c.get("/health").json()["status"]=="ok"
def test_detect():
    vals=[100,101,99,100,102,98,101,1000]
    rows=[{"timestamp":f"2026-01-{i:02d}T00:00:00Z","metric":"x","value":v} for i,v in enumerate(vals,1)]
    r=c.post("/detect",json={"records":rows,"window":7,"min_history":5})
    assert r.status_code==200 and r.json()["count"]==8
