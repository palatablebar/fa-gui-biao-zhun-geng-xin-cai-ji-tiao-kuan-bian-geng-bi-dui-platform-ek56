"""beat：每 30 分钟巡检来源配置，写一条审计（演示 worker 持续运行）。"""
from __future__ import annotations

from worker_src.config.celery_app import celery_app


@celery_app.task(name="lawdelta.source_sweep")
def source_sweep() -> dict:
    from src.config.database import session_scope
    from src.constants.log_templates import ACTION_SWEEP
    from src.models.source import Source
    from src.services import audit_service

    with session_scope() as db:
        sources = db.query(Source).all()
        audit_service.record(
            db,
            action=ACTION_SWEEP,
            entity_type="source",
            detail={
                "sources": [source.code for source in sources],
                "enabled": [source.code for source in sources if source.enabled],
            },
        )
        count = len(sources)
    return {"swept_sources": count}
