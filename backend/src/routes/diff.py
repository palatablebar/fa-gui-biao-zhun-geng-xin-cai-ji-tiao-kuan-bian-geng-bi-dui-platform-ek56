from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import diff_controller
from src.middlewares.rate_limit import rate_limit
from src.middlewares.rbac import require_permission
from src.models.user import User
from src.schemas.domain import DiffCreateRequest

router = APIRouter(tags=["diff"])


@router.get("/diffs")
def list_runs(
    document_key: str | None = None,
    limit: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("diffs:read")),
) -> dict:
    return diff_controller.list_runs(db, document_key=document_key, limit=limit)


@router.post("/diffs", dependencies=[rate_limit("diff")])
def create_diff(
    payload: DiffCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("diffs:run")),
) -> dict:
    return diff_controller.create_diff(db, payload, user, request)


@router.get("/diffs/{run_id}")
def get_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("diffs:read")),
) -> dict:
    return diff_controller.get_run(db, run_id)


@router.get("/diffs/{run_id}/changes")
def list_changes(
    run_id: uuid.UUID,
    severity: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("changes:read")),
) -> dict:
    return diff_controller.list_changes(db, run_id, severity=severity)
