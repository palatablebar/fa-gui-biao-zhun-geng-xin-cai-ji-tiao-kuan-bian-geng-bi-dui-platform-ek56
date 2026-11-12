"""变更确认、发布、客户视图。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from src.constants import error_codes as codes
from src.constants.enums import Industry, Severity
from src.constants.log_templates import ACTION_CHANGE_CONFIRM, ACTION_CHANGE_PUBLISH
from src.models.change_item import ChangeItem
from src.models.diff_run import DiffRun
from src.models.document import Document
from src.models.user import User
from src.services import audit_service, document_service
from src.services.diff_service import get_run, list_changes, serialize_change, serialize_run
from src.utils.errors import AppError, not_found


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _lock_document_key(db: Session, document_key: str) -> None:
    """按法规串行化发布临界区：并发发布同一 document_key 时后者等前者提交后再判断。

    PostgreSQL 用事务级咨询锁（提交即释放）；其他方言退化为该法规全部版本行的行锁。
    """
    if db.get_bind().dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:document_key, 0))"),
            {"document_key": document_key},
        )
    else:
        db.execute(
            select(Document.id).where(Document.document_key == document_key).with_for_update()
        ).all()


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
    run = db.get(DiffRun, change.diff_run_id)
    if run is not None:
        # 与发布共用同一把法规级锁：避免「确认」与「发布」交错时改了已发布变更的标注
        _lock_document_key(db, run.document_key)
    change = db.execute(
        select(ChangeItem)
        .where(ChangeItem.id == change_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
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

    # 并发安全：先按法规串行（document_key 建批次后不变），再锁批次行——
    # 同一法规的并发发布互斥，同一批次的重复发布串行，后者读到前者已提交的结果。
    _lock_document_key(db, run.document_key)
    run = db.execute(
        select(DiffRun)
        .where(DiffRun.id == run_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
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
            # 幂等口径：重复执行发布不新增、不重复任何变更
            raise AppError(
                codes.ALREADY_PUBLISHED,
                "该批次已发布，重复执行不会新增或重复变更",
                detail=f"published_at={run.published_at.isoformat()}",
            )
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

    # 现行版本只能向前推进：仅当目标版本高于现行版本时才切换现行；
    # 旧批次照常发布为历史说明（保留历史），但不得把现行版本改回去。
    target = db.get(Document, run.target_document_id, populate_existing=True)
    current = document_service.get_current_version(db, run.document_key)
    promoted = False
    if target is not None:
        if current is None:
            target.status = "current"
            promoted = True
        elif current.id != target.id and target.version_no > current.version_no:
            # 先落「旧现行转历史」再立新现行：部分唯一索引不允许两条 current 瞬时共存
            current.status = "superseded"
            db.flush()
            target.status = "current"
            promoted = True
        # 不高于现行的旧批次：不动任何现行状态，只补历史说明
    effective = target if promoted else current
    if effective is not None:
        # 防御历史库残留：同一法规只保留一条 current（部分唯一索引缺失时也成立）
        stale = db.execute(
            select(Document).where(
                Document.document_key == run.document_key,
                Document.status == "current",
                Document.id != effective.id,
            )
        ).scalars().all()
        for document in stale:
            document.status = "superseded"
    is_effective = bool(target is not None and effective is not None and effective.id == target.id)

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
            "promoted": promoted,
            "is_effective": is_effective,
            "current_version_label": effective.version_label if effective else "",
        },
        trace_id=trace_id,
    )
    db.commit()
    return {
        "run": serialize_run(run, db),
        "published_changes": [serialize_change(change) for change in confirmed],
        "promoted": promoted,
        "is_effective": is_effective,
        "current_version_label": effective.version_label if effective else "",
        "current_version_no": effective.version_no if effective else None,
    }


def public_changes(db: Session) -> list[dict]:
    """客户视图：只返回已发布变更，按批次聚合发布说明。

    排序按「法规 + 版本递进」（不看发布动作时间）：旧批次补充发布不会顶到最前；
    「现行」标识取自 documents 唯一 current 行，与文档时间线、导出同源。
    """
    runs = db.execute(select(DiffRun).where(DiffRun.published_at.is_not(None))).scalars().all()
    current_by_key: dict[str, Document] = {}
    for document in db.execute(
        select(Document).where(Document.status == "current").order_by(Document.version_no)
    ).scalars().all():
        # 历史库若残留多条 current，保留版本号最高的一条（与 get_current_version 同口径）
        current_by_key[document.document_key] = document
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
        current = current_by_key.get(run.document_key)
        payload.append(
            {
                "diff_run_id": str(run.id),
                "document_key": run.document_key,
                "title": target.title if target else "",
                "issuer": target.issuer if target else "",
                "base_label": run.stats.get("base_label", ""),
                "target_label": run.stats.get("target_label", ""),
                "target_version_no": target.version_no if target else 0,
                "published_at": run.published_at.isoformat() if run.published_at else None,
                "publish_note": run.publish_note,
                "effective_at": target.effective_at.isoformat() if target and target.effective_at else None,
                "current_version_label": current.version_label if current else "",
                "current_version_no": current.version_no if current else None,
                "is_effective": bool(current is not None and target is not None and current.id == target.id),
                "changes": [serialize_change(change) for change in changes],
                "severity_counts": {
                    level.value: sum(1 for change in changes if change.severity == level.value)
                    for level in Severity
                },
            }
        )
    # 排序主键：法规 → 目标版本号递进（同版本再按发布时间）。旧批次补充发布不会顶到最前，
    # 现行版本所在批次恒在该法规最前；客户列表与导出共用这一口径。
    payload.sort(key=lambda item: item["published_at"] or "", reverse=True)
    payload.sort(key=lambda item: item["target_version_no"], reverse=True)
    payload.sort(key=lambda item: item["document_key"])
    return payload


def export_payload(db: Session, run_id: uuid.UUID) -> tuple[dict, list[dict]]:
    """导出载荷：已发布批次只含已发布变更（与客户视图同一份），并标注同一现行版本。"""
    run = get_run(db, run_id)
    payload = serialize_run(run, db)
    changes = list_changes(db, run.id)
    if run.published_at is not None:
        changes = [change for change in changes if change["published"]]
    current = document_service.get_current_version(db, run.document_key)
    payload["current_version_label"] = current.version_label if current else ""
    payload["current_version_no"] = current.version_no if current else None
    payload["is_effective"] = bool(current is not None and current.id == run.target_document_id)
    return payload, changes
