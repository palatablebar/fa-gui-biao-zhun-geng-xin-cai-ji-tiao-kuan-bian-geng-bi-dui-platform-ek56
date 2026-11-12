"""比对批次：创建 / 查询 / 变更列表。"""
from __future__ import annotations

import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from src.models.user import User
from src.schemas.domain import DiffCreateRequest
from src.services import diff_service


def create_diff(db: Session, payload: DiffCreateRequest, user: User, request: Request) -> dict:
    run = diff_service.create_diff_run(
        db,
        base_version_id=payload.base_version_id,
        target_version_id=payload.target_version_id,
        actor=user,
        trace_id=getattr(request.state, "trace_id", ""),
    )
    return {"run": diff_service.serialize_run(run, db)}


def list_runs(db: Session, document_key: str | None = None, limit: int = 30) -> dict:
    return {"items": diff_service.list_runs(db, document_key=document_key, limit=limit)}


def get_run(db: Session, run_id: uuid.UUID) -> dict:
    run = diff_service.get_run(db, run_id)
    return {"run": diff_service.serialize_run(run, db)}


def list_changes(db: Session, run_id: uuid.UUID, severity: str | None = None) -> dict:
    run = diff_service.get_run(db, run_id)
    changes = diff_service.list_changes(db, run.id, severity=severity)
    return {
        "run": diff_service.serialize_run(run, db),
        "items": changes,
        "total": len(changes),
    }
