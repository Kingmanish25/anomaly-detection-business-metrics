import pytest
from anomaly_detection.validation import normalize_records
def test_duplicate_rejected():
    row={"timestamp":"2026-01-01T00:00:00Z","metric":"x","value":1}
    with pytest.raises(ValueError,match="duplicate"): normalize_records([row,row])
