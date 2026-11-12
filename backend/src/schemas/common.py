"""通用请求/响应模型。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorPayload(BaseModel):
    code: str
    message: str
    detail: str = ""
    trace_id: str | None = None


class HealthPayload(BaseModel):
    status: str
    brand: str
    database: bool
    redis: bool
    version: str = "1.0.0"


class ListQuery(BaseModel):
    limit: int = Field(default=30, ge=1, le=200)
