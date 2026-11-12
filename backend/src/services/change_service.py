"""变更确认、发布、客户视图。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.constants import error_codes as codes
from src.constants.enums import Industry, Severity
from src.constants.log_templates import ACTION_CHANGE_CONFIRM, ACTION_CHANGE_PUBLISH
from src.models.change_item import ChangeItem
from src.models.diff_run import DiffRun
from src.models.document import Document
from src.models.user import User
from src.services import audit_service
from src.services.diff_service import serialize_change, serialize_run
from src.utils.errors import AppError, not_found


def _now() -> datetime:
    return datetime.now(timezone.utc)


def list_run_changes(db: Session, run_id: uuid.UUID) -> list[dict]:
    changes = db.execute(
        select(ChangeItem)
        .where(ChangeItem.diff_run_id == run_id)
        .order_by(ChangeItem.clause_no_new.nulls_last(), ChangeItem.clause_no_old.nulls_last())
    ).scalars().all()
    return [serialize_change(change) for change in changes]


def pending_review(db: Session, limit: int = 50) -> list[dict]:
    """待确认队列：已成功的批次里、尚未确认的变更。"""
    changes = db.execute(
        select(ChangeItem)
        .join(DiffRun, DiffRun.id == ChangeItem.diff_run_id)
        .where(DiffRun.status == "succeeded", ChangeItem.confirmed.is_(False))
        .order_by(DiffRun.created_at.desc(), ChangeItem.clause_no_new.nulls_last())
        .limit(limit)
    ).scalars().all()
    return [serialize_change(change) for change in changes]


def confirm_change(
    db: Session,
    change_id: uuid.UUID,
    *,
    actor: User,
    impact_industries: list[str],
    impact_note: str,
    trace_id: str = "",
) -> dict:
    change = db.get(ChangeItem, change_id)
    if change is None:
        raise not_found("变更项", change_id)
    if change.published:
        raise AppError(codes.ALREADY_PUBLISHED, "已发布的变更不能再修改影响标注")
    valid = {item.value for item in Industry}
    invalid = [item for item in impact_industries if item not in valid]
    if invalid:
        raise AppError(codes.VALIDATION_ERROR, "行业标签不合法", f"invalid={invalid} valid={sorted(valid)}")
    if not impact_industries:
        raise AppError(codes.VALIDATION_ERROR, "确认变更必须至少标注一个影响行业")

    change.impact_industries = list(dict.fromkeys(impact_industries))
    change.impact_note = impact_note.strip()[:1000]
    change.confirmed = True
    change.confirmed_by = actor.id
    change.confirmed_at = _now()
    audit_service.record(
        db,
        action=ACTION_CHANGE_CONFIRM,
        actor=actor,
        entity_type="change_item",
        entity_id=change.id,
        detail={
            "severity": change.severity,
            "impact_industries": change.impact_industries,
            "impact_note": change.impact_note,
        },
        trace_id=trace_id,
    )
    db.commit()
    return serialize_change(change)


def publish_run(
    db: Session,
    run_id: uuid.UUID,
    *,
    actor: User,
    publish_note: str,
    trace_id: str = "",
) -> dict:
    run = db.get(DiffRun, run_id)
    if run is None:
        raise not_found("比对批次", run_id)
    if run.status != "succeeded":
        raise AppError(codes.DIFF_NOT_READY, detail=f"status={run.status}")

    confirmed = db.execute(
        select(ChangeItem).where(
            ChangeItem.diff_run_id == run.id,
            ChangeItem.confirmed.is_(True),
            ChangeItem.published.is_(False),
        )
    ).scalars().all()
    if not confirmed:
        if run.published_at is not None:
            raise AppError(codes.ALREADY_PUBLISHED, detail=f"published_at={run.published_at.isoformat()}")
        raise AppError(codes.CHANGE_NOT_CONFIRMED, "本批次没有已确认的变更，不能发布")

    stamp = _now()
    for change in confirmed:
        change.published = True
        change.published_at = stamp
        change.publish_note = (publish_note or "").strip()[:1000]

    # 已发布批次允许「补充发布」新确认的变更（publish_note 以最新一次为准）
    run.published_at = stamp
    run.published_by = actor.id
    run.publish_note = (publish_note or "").strip()[:1000]

    target = db.get(Document, run.target_document_id)
    if target is not None:
        previous = db.execute(
            select(Document).where(
                Document.document_key == target.document_key,
                Document.status == "current",
                Document.id != target.id,
            )
        ).scalars().all()
        for document in previous:
            document.status = "superseded"
        target.status = "current"

    audit_service.record(
        db,
        action=ACTION_CHANGE_PUBLISH,
        actor=actor,
        entity_type="diff_run",
        entity_id=run.id,
        detail={
            "document_key": run.document_key,
            "published_changes": len(confirmed),
            "severity": {level.value: sum(1 for c in confirmed if c.severity == level.value) for level in Severity},
            "publish_note": run.publish_note,
        },
        trace_id=trace_id,
    )
    db.commit()
    return {
        "run": serialize_run(run, db),
        "published_changes": [serialize_change(change) for change in confirmed],
    }


def public_changes(db: Session) -> list[dict]:
    """客户视图：只返回已发布变更，按批次聚合发布说明。"""
    runs = db.execute(
        select(DiffRun).where(DiffRun.published_at.is_not(None)).order_by(DiffRun.published_at.desc())
    ).scalars().all()
    payload: list[dict] = []
    for run in runs:
        changes = db.execute(
            select(ChangeItem)
            .where(ChangeItem.diff_run_id == run.id, ChangeItem.published.is_(True))
            .order_by(ChangeItem.clause_no_new.nulls_last(), ChangeItem.clause_no_old.nulls_last())
        ).scalars().all()
        if not changes:
            continue
        target = db.get(Document, run.target_document_id)
        payload.append(
            {
                "diff_run_id": str(run.id),
                "document_key": run.document_key,
                "title": target.title if target else "",
                "issuer": target.issuer if target else "",
                "base_label": run.stats.get("base_label", ""),
                "target_label": run.stats.get("target_label", ""),
                "published_at": run.published_at.isoformat() if run.published_at else None,
                "publish_note": run.publish_note,
                "effective_at": target.effective_at.isoformat() if target and target.effective_at else None,
                "changes": [serialize_change(change) for change in changes],
                "severity_counts": {
                    level.value: sum(1 for change in changes if change.severity == level.value)
                    for level in Severity
                },
            }
        )
    return payload
