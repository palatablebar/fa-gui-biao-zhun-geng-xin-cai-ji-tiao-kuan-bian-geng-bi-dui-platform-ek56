"""worker 心跳：Redis 键 + 时间戳，healthcheck 与后端运维面板共用。"""
from __future__ import annotations

import time

import redis

from worker_src.config.settings import HEARTBEAT_KEY, REDIS_URL


def beat() -> float:
    stamp = time.time()
    try:
        client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        client.set(HEARTBEAT_KEY, f"{stamp:.3f}")
    except Exception:  # noqa: BLE001 - 心跳失败不阻塞任务
        pass
    return stamp
