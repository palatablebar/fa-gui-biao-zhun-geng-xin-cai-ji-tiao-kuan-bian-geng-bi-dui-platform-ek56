"""worker Celery 应用：消费 lawdelta.run_diff，beat 负责心跳与来源巡检。"""
from __future__ import annotations

from celery import Celery
from celery.schedules import schedule

from worker_src.config.settings import (
    HEARTBEAT_INTERVAL_SECONDS,
    REDIS_URL,
    SWEEP_INTERVAL_SECONDS,
)

celery_app = Celery(
    "lawdelta-worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "worker_src.tasks.diff_task",
        "worker_src.tasks.heartbeat_task",
        "worker_src.tasks.sweep_task",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1,
    task_acks_late=False,
    broker_transport_options={"socket_connect_timeout": 5, "socket_timeout": 5},
    beat_schedule={
        "worker-heartbeat": {
            "task": "lawdelta.heartbeat",
            "schedule": schedule(run_every=HEARTBEAT_INTERVAL_SECONDS),
        },
        "source-sweep": {
            "task": "lawdelta.source_sweep",
            "schedule": schedule(run_every=SWEEP_INTERVAL_SECONDS),
        },
    },
)
