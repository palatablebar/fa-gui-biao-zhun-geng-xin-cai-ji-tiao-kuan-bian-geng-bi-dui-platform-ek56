from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import catalog_controller
from src.middlewares.auth import get_current_user
from src.middlewares.rate_limit import rate_limit
from src.middlewares.rbac import require_permission
from src.models.user import User
from src.schemas.domain import SourceUpdateRequest

router = APIRouter(tags=["catalog"])


@router.get("/sources")
def list_sources(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("sources:read")),
) -> dict:
    return catalog_controller.list_sources(db)


@router.patch("/sources/{source_id}")
def update_source(
    source_id: uuid.UUID,
    payload: SourceUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("sources:write")),
) -> dict:
    return catalog_controller.update_source(db, source_id, payload, user)


@router.post("/sources/{source_id}/crawl", dependencies=[rate_limit("crawl")])
def crawl_source(
    source_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("sources:crawl")),
) -> dict:
    return catalog_controller.crawl_source(db, source_id, user, request)


@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("documents:read")),
) -> dict:
    return catalog_controller.list_documents(db)


@router.get("/documents/{version_id}")
def get_version(
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("documents:read")),
) -> dict:
    return catalog_controller.get_version(db, version_id)
