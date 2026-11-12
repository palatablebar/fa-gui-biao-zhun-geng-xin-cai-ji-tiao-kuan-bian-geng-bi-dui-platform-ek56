"""变更确认 / 发布 / 客户视图 / 导出 / 审计。"""
from __future__ import annotations

import uuid

from fastapi import Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.models.user import User
from src.schemas.domain import ChangeConfirmRequest, PublishRequest
from src.services import audit_service, change_service, export_service


def pending_review(db: Session, limit: int = 50) -> dict:
    items = change_service.pending_review(db, limit=limit)
    return {"items": items, "total": len(items)}


def confirm(db: Session, change_id: uuid.UUID, payload: ChangeConfirmRequest, user: User, request: Request) -> dict:
    change = change_service.confirm_change(
        db,
        change_id,
        actor=user,
        impact_industries=payload.impact_industries,
        impact_note=payload.impact_note,
        trace_id=getattr(request.state, "trace_id", ""),
    )
    return {"change": change}


def publish(db: Session, run_id: uuid.UUID, payload: PublishRequest, user: User, request: Request) -> dict:
    return change_service.publish_run(
        db,
        run_id,
        actor=user,
        publish_note=payload.publish_note,
        trace_id=getattr(request.state, "trace_id", ""),
    )


def public_changes(db: Session) -> dict:
    items = change_service.public_changes(db)
    return {"items": items, "total": len(items)}


def export(db: Session, run_id: uuid.UUID, fmt: str) -> Response:
    payload, changes = change_service.export_payload(db, run_id)
    filename = export_service.export_filename(payload, fmt)
    if fmt == "md":
        body = export_service.render_markdown(payload, changes)
        media = "text/markdown; charset=utf-8"
    else:
        body = export_service.render_csv(payload, changes)
        media = "text/csv; charset=utf-8"
    return Response(
        content=body,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def audit_log(db: Session, limit: int = 50) -> dict:
    items = audit_service.recent(db, limit=limit)
    return {"items": items, "total": len(items)}
