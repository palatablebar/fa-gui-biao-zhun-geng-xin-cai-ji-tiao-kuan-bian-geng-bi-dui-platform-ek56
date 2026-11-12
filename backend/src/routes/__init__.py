"""路由总装配。"""
from fastapi import APIRouter

from src.routes import audit, auth, catalog, change, diff, export, health, public

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(catalog.router)
api_router.include_router(diff.router)
api_router.include_router(change.router)
api_router.include_router(public.router)
api_router.include_router(export.router)
api_router.include_router(audit.router)

__all__ = ["api_router"]
