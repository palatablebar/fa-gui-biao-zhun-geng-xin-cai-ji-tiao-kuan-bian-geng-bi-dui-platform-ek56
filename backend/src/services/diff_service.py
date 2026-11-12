"""比对批次编排：建批次 → 切分 → 对齐 → 判级 → 落 ChangeItem。

计算全部在后端/worker（算法见 clause_splitter / clause_aligner / change_classifier），
前端只展示接口回传的数字。
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.database import session_scope
from src.config.settings import settings
from src.constants import error_codes as codes
from src.constants.enums import CHANGE_TYPE_LABELS, SEVERITY_LABELS, DiffRunStatus, Severity
from src.constants.limits import MAX_CLAUSES_PER_DIFF
from src.constants.log_templates import ACTION_DIFF_FAIL, ACTION_DIFF_RUN
from src.models.change_item import ChangeItem
from src.models.diff_run import DiffRun
from src.models.document import Document
from src.models.user import User
from src.services import audit_service
from src.services.change_classifier import classify_change
from src.services.clause_aligner import align_clauses
from src.services.clause_splitter import split_clauses
from src.utils.errors import AppError, not_found

ALGORITHM_VERSION = "1.0.0"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_diff_run(
    db: Session,
    *,
    base_version_id: uuid.UUID,
    target_version_id: uuid.UUID,
    actor: User,
    trace_id: str = "",
) -> DiffRun:
    base = db.get(Document, base_version_id)
    target = db.get(Document, target_version_id)
    if base is None:
        raise not_found("文档版本", base_version_id)
    if target is None:
        raise not_found("文档版本", target_version_id)
    if base.document_key != target.document_key:
        raise AppError(codes.VALIDATION_ERROR, "左右版本不属于同一部法规", f"{base.document_key} vs {target.document_key}")
    if base.id == target.id or base.version_no == target.version_no:
        raise AppError(codes.SAME_VERSION, detail=f"{base.version_label} == {target.version_label}")

    existing = db.execute(
        select(DiffRun)
        .where(
            DiffRun.base_document_id == base.id,
            DiffRun.target_document_id == target.id,
            DiffRun.status == DiffRunStatus.SUCCEEDED.value,
        )
        .order_by(DiffRun.created_at.desc())
    ).scalars().first()
    if existing is not None:
        return existing

    run = DiffRun(
        document_key=base.document_key,
        base_document_id=base.id,
        target_document_id=target.id,
        requested_by=actor.id,
        status=DiffRunStatus.QUEUED.value,
        algorithm_version=ALGORITHM_VERSION,
        stats={
            "base_label": base.version_label,
            "target_label": target.version_label,
            "base_clause_count": base.clause_count,
            "target_clause_count": target.clause_count,
        },
        severity_counts={},
    )
    db.add(run)
    db.flush()
    audit_service.record(
        db,
        action=ACTION_DIFF_RUN,
        actor=actor,
        entity_type="diff_run",
        entity_id=run.id,
        detail={
            "document_key": run.document_key,
            "base": base.version_label,
            "target": target.version_label,
        },
        trace_id=trace_id,
    )
    db.commit()

    _dispatch(run, db)
    db.refresh(run)
    return run


def _dispatch(run: DiffRun, db: Session) -> None:
    """投递给 Celery worker；broker 不可用时退化为同步执行（不让主流程卡死）。"""
    try:
        from src.config.celery_app import TASK_RUN_DIFF, celery_app

        celery_app.send_task(TASK_RUN_DIFF, args=[str(run.id)])
        return
    except Exception as exc:  # noqa: BLE001 - 任何 broker 异常都退化为同步
        run.stats = {**run.stats, "dispatch": "inline_fallback", "dispatch_error": str(exc)[:200]}
        db.commit()
    execute_diff_run_in_session(db, run)


def execute_diff_run(run_id: uuid.UUID | str) -> None:
    """worker 入口：独立 session 执行一次比对。"""
    with session_scope() as db:
        run = db.get(DiffRun, uuid.UUID(str(run_id)))
        if run is None:
            return
        if run.status == DiffRunStatus.SUCCEEDED.value:
            return
        execute_diff_run_in_session(db, run)


def execute_diff_run_in_session(db: Session, run: DiffRun) -> DiffRun:
    if run.status == DiffRunStatus.SUCCEEDED.value:
        return run
    run.status = DiffRunStatus.RUNNING.value
    run.started_at = _now()
    db.commit()

    try:
        base = db.get(Document, run.base_document_id)
        target = db.get(Document, run.target_document_id)
        if base is None or target is None:
            raise AppError(codes.NOT_FOUND, "版本已被删除")

        split_base = split_clauses(base.raw_text)
        split_target = split_clauses(target.raw_text)
        if not split_base.clauses or not split_target.clauses:
            raise AppError(codes.DOCUMENT_EMPTY, detail="条款切分为空")
        if len(split_base.clauses) > MAX_CLAUSES_PER_DIFF or len(split_target.clauses) > MAX_CLAUSES_PER_DIFF:
            raise AppError(codes.DIFF_TOO_LARGE)

        aligned = align_clauses(
            split_base.clauses,
            split_target.clauses,
            match_threshold=settings.align_match_threshold,
            change_threshold=settings.align_change_threshold,
        )

        severity_counts = {level.value: 0 for level in Severity}
        change_items: list[ChangeItem] = []
        for pair in aligned.pairs:
            if pair.change_type == "unchanged":
                continue
            old_text = pair.old.text if pair.old else ""
            new_text = pair.new.text if pair.new else ""
            classified = classify_change(pair.change_type, old_text, new_text)
            severity_counts[classified.severity] = severity_counts.get(classified.severity, 0) + 1
            change_items.append(
                ChangeItem(
                    diff_run_id=run.id,
                    change_type=pair.change_type,
                    severity=classified.severity,
                    clause_no_old=pair.old.number if pair.old else None,
                    clause_no_new=pair.new.number if pair.new else None,
                    clause_label_old=pair.old.label if pair.old else "",
                    clause_label_new=pair.new.label if pair.new else "",
                    old_text=old_text,
                    new_text=new_text,
                    similarity=pair.similarity,
                    edit_ratio=classified.edit_ratio,
                    keywords=classified.keywords,
                    industries=classified.industries,
                    reason=classified.reason,
                )
            )

        severity_counts[Severity.UNPARSED.value] = split_base.unparsed_count + split_target.unparsed_count
        db.add_all(change_items)

        run.stats = {
            **aligned.stats,
            "base_label": base.version_label,
            "target_label": target.version_label,
            "base_clause_count": len(split_base.clauses),
            "target_clause_count": len(split_target.clauses),
            "base_hash": base.content_hash,
            "target_hash": target.content_hash,
            "unparsed_old": split_base.unparsed_count,
            "unparsed_new": split_target.unparsed_count,
            "severity": severity_counts,
            "algorithm_version": ALGORITHM_VERSION,
        }
        run.severity_counts = severity_counts
        run.change_count = len(change_items)
        run.status = DiffRunStatus.SUCCEEDED.value
        run.finished_at = _now()
        db.commit()
        return run
    except Exception as exc:  # noqa: BLE001 - 批次失败要落库可查
        db.rollback()
        failed = db.get(DiffRun, run.id)
        if failed is not None:
            failed.status = DiffRunStatus.FAILED.value
            failed.error_message = str(exc)[:500]
            failed.finished_at = _now()
            audit_service.record(
                db,
                action=ACTION_DIFF_FAIL,
                entity_type="diff_run",
                entity_id=failed.id,
                detail={"error": str(exc)[:300]},
            )
            db.commit()
        raise


def get_run(db: Session, run_id: uuid.UUID) -> DiffRun:
    run = db.get(DiffRun, run_id)
    if run is None:
        raise not_found("比对批次", run_id)
    return run


def list_runs(db: Session, document_key: str | None = None, limit: int = 30) -> list[dict]:
    query = select(DiffRun).order_by(DiffRun.created_at.desc()).limit(limit)
    if document_key:
        query = query.where(DiffRun.document_key == document_key)
    runs = db.execute(query).scalars().all()
    return [serialize_run(run, db) for run in runs]


def serialize_run(run: DiffRun, db: Session | None = None) -> dict:
    base = db.get(Document, run.base_document_id) if db else None
    target = db.get(Document, run.target_document_id) if db else None
    payload = {
        "id": str(run.id),
        "document_key": run.document_key,
        "title": target.title if target else "",
        "base_version_id": str(run.base_document_id),
        "target_version_id": str(run.target_document_id),
        "base_label": base.version_label if base else run.stats.get("base_label", ""),
        "target_label": target.version_label if target else run.stats.get("target_label", ""),
        "status": run.status,
        "algorithm_version": run.algorithm_version,
        "stats": run.stats,
        "severity_counts": run.severity_counts,
        "change_count": run.change_count,
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "published_at": run.published_at.isoformat() if run.published_at else None,
        "publish_note": run.publish_note,
    }
    return payload


def serialize_change(change: ChangeItem) -> dict:
    return {
        "id": str(change.id),
        "diff_run_id": str(change.diff_run_id),
        "change_type": change.change_type,
        "change_type_label": CHANGE_TYPE_LABELS.get(change.change_type, change.change_type),
        "severity": change.severity,
        "severity_label": SEVERITY_LABELS.get(change.severity, change.severity),
        "clause_no_old": change.clause_no_old,
        "clause_no_new": change.clause_no_new,
        "clause_label_old": change.clause_label_old,
        "clause_label_new": change.clause_label_new,
        "old_text": change.old_text,
        "new_text": change.new_text,
        "similarity": round(float(change.similarity or 0), 4),
        "edit_ratio": round(float(change.edit_ratio or 0), 4),
        "keywords": change.keywords or [],
        "industries": change.industries or [],
        "reason": change.reason,
        "confirmed": change.confirmed,
        "confirmed_at": change.confirmed_at.isoformat() if change.confirmed_at else None,
        "impact_industries": change.impact_industries or [],
        "impact_note": change.impact_note,
        "published": change.published,
        "published_at": change.published_at.isoformat() if change.published_at else None,
        "publish_note": change.publish_note,
    }


def list_changes(db: Session, run_id: uuid.UUID, *, severity: str | None = None, only_change_type: bool = True) -> list[dict]:
    query = select(ChangeItem).where(ChangeItem.diff_run_id == run_id)
    if severity:
        query = query.where(ChangeItem.severity == severity)
    query = query.order_by(ChangeItem.clause_no_new.nulls_last(), ChangeItem.clause_no_old.nulls_last())
    changes = db.execute(query).scalars().all()
    if only_change_type:
        changes = [change for change in changes if change.change_type != "unchanged"]
    return [serialize_change(change) for change in changes]
