from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import change_controller
from src.middlewares.rbac import require_permission
from src.models.user import User

router = APIRouter(tags=["audit"])


@router.get("/audit")
def audit_log(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("audit:read")),
) -> dict:
    return change_controller.audit_log(db, limit=limit)
