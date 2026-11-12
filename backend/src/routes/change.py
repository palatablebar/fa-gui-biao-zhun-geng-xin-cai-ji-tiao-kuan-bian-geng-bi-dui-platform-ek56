from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import change_controller
from src.middlewares.rbac import require_permission
from src.models.user import User
from src.schemas.domain import ChangeConfirmRequest, PublishRequest

router = APIRouter(tags=["change"])


@router.get("/changes/pending")
def pending(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("changes:read")),
) -> dict:
    return change_controller.pending_review(db, limit=limit)


@router.post("/changes/{change_id}/confirm")
def confirm(
    change_id: uuid.UUID,
    payload: ChangeConfirmRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("changes:confirm")),
) -> dict:
    return change_controller.confirm(db, change_id, payload, user, request)


@router.post("/diffs/{run_id}/publish")
def publish(
    run_id: uuid.UUID,
    payload: PublishRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("changes:publish")),
) -> dict:
    return change_controller.publish(db, run_id, payload, user, request)
