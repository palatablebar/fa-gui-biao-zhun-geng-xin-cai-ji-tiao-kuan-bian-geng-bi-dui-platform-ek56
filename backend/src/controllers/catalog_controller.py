"""来源 / 文档版本：查询、配置、采集。"""
from __future__ import annotations

import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from src.models.user import User
from src.schemas.domain import SourceUpdateRequest
from src.services import crawl_service, document_service, source_service


def list_sources(db: Session) -> dict:
    return {"items": source_service.list_sources(db)}


def update_source(db: Session, source_id: uuid.UUID, payload: SourceUpdateRequest, user: User) -> dict:
    source = source_service.update_source(
        db,
        source_id,
        actor=user,
        enabled=payload.enabled,
        owner_note=payload.owner_note,
    )
    return {"source": source}


def crawl_source(db: Session, source_id: uuid.UUID, user: User, request: Request) -> dict:
    source = source_service.get_source(db, source_id)
    return crawl_service.crawl_source(db, source, user, trace_id=getattr(request.state, "trace_id", ""))


def list_documents(db: Session) -> dict:
    return {"items": document_service.list_documents(db)}


def get_version(db: Session, version_id: uuid.UUID) -> dict:
    document = document_service.get_document(db, version_id)
    payload = document_service.serialize_version(document, with_clauses=True)
    payload["diff_history"] = [
        {
            "id": str(run.id),
            "base_label": run.stats.get("base_label", ""),
            "target_label": run.stats.get("target_label", ""),
            "status": run.status,
            "change_count": run.change_count,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }
        for run in document_service.version_history(db, document.document_key)
    ]
    return {"version": payload}
