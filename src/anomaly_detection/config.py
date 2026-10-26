import os
from dataclasses import dataclass
@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "local")
    threshold: float = float(os.getenv("ANOMALY_THRESHOLD", "3.5"))
    window: int = int(os.getenv("ROLLING_WINDOW", "14"))
    min_history: int = int(os.getenv("MIN_HISTORY", "7"))
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", "5000000"))
settings = Settings()
