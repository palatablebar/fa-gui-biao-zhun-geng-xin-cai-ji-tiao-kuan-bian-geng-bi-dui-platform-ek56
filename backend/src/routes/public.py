from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import change_controller
from src.middlewares.rbac import require_permission
from src.models.user import User

router = APIRouter(tags=["public"])


@router.get("/public/changes")
def public_changes(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("public:read")),
) -> dict:
    return change_controller.public_changes(db)
