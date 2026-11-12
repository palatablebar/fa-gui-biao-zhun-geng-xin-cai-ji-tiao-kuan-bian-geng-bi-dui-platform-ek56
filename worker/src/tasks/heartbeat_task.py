"""beat：每 30s 写心跳。"""
from __future__ import annotations

from worker_src.config.celery_app import celery_app
from worker_src.core.heartbeat import beat


@celery_app.task(name="lawdelta.heartbeat")
def heartbeat() -> dict:
    return {"heartbeat_at": beat()}
