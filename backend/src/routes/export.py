from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import change_controller
from src.middlewares.rbac import require_permission
from src.models.user import User

router = APIRouter(tags=["export"])


@router.get("/diffs/{run_id}/export")
def export(
    run_id: uuid.UUID,
    format: str = "md",
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("changes:export")),
) -> Response:
    fmt = "csv" if format.lower() == "csv" else "md"
    return change_controller.export(db, run_id, fmt)
