"""来源（Source）查询与配置。"""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.constants.log_templates import ACTION_SOURCE_TOGGLE
from src.models.document import Document
from src.models.source import Source
from src.models.user import User
from src.services import audit_service
from src.utils.errors import not_found


_KIND_ORDER = {"national_standard": 0, "regulatory": 1, "local_env": 2}


def list_sources(db: Session) -> list[dict]:
    sources = sorted(
        db.execute(select(Source)).scalars().all(),
        key=lambda source: (_KIND_ORDER.get(source.kind, 9), source.code),
    )
    counts = dict(
        db.execute(
            select(Document.source_id, func.count(Document.id)).group_by(Document.source_id)
        ).all()
    )
    return [serialize(source, version_count=counts.get(source.id, 0)) for source in sources]


def get_source(db: Session, source_id: uuid.UUID) -> Source:
    source = db.get(Source, source_id)
    if source is None:
        raise not_found("来源", source_id)
    return source


def update_source(db: Session, source_id: uuid.UUID, *, actor: User, enabled: bool | None, owner_note: str | None) -> dict:
    source = get_source(db, source_id)
    changes: dict = {}
    if enabled is not None and enabled != source.enabled:
        source.enabled = enabled
        changes["enabled"] = enabled
    if owner_note is not None and owner_note != source.owner_note:
        source.owner_note = owner_note
        changes["owner_note"] = owner_note
    if changes:
        audit_service.record(
            db,
            action=ACTION_SOURCE_TOGGLE,
            actor=actor,
            entity_type="source",
            entity_id=source.id,
            detail=changes,
        )
        db.commit()
    return serialize(source, version_count=_count_versions(db, source.id))


def _count_versions(db: Session, source_id: uuid.UUID) -> int:
    return int(
        db.execute(select(func.count(Document.id)).where(Document.source_id == source_id)).scalar_one()
    )


def serialize(source: Source, version_count: int = 0) -> dict:
    return {
        "id": str(source.id),
        "code": source.code,
        "name": source.name,
        "kind": source.kind,
        "base_url": source.base_url,
        "fetch_cycle": source.fetch_cycle,
        "owner_note": source.owner_note,
        "enabled": source.enabled,
        "version_count": version_count,
        "last_crawled_at": source.last_crawled_at.isoformat() if source.last_crawled_at else None,
        "next_issue_hint": source.next_issue_hint.isoformat() if source.next_issue_hint else None,
    }
