"""比对任务：真正的切分 + 对齐 + 判级在 backend services 里执行（前后端算力分离）。"""
from __future__ import annotations

from worker_src.config.celery_app import celery_app


@celery_app.task(name="lawdelta.run_diff", bind=True, max_retries=0)
def run_diff(self, run_id: str) -> dict:
    from src.services.diff_service import execute_diff_run

    execute_diff_run(run_id)
    return {"run_id": run_id, "status": "executed"}
