"""worker 侧最小配置（业务配置复用 backend/src/config/settings.py）。"""
from __future__ import annotations

import os

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
HEARTBEAT_KEY = "lawdelta:worker:heartbeat"
HEARTBEAT_INTERVAL_SECONDS = 30.0
SWEEP_INTERVAL_SECONDS = 1800.0
