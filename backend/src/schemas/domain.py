"""业务域请求模型（响应由 service 的 serialize_* 构造，字段固定）。"""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, field_validator

from src.constants.enums import Industry


class DiffCreateRequest(BaseModel):
    base_version_id: uuid.UUID
    target_version_id: uuid.UUID


class ChangeConfirmRequest(BaseModel):
    impact_industries: list[str] = Field(default_factory=list)
    impact_note: str = Field(default="", max_length=1000)

    @field_validator("impact_industries")
    @classmethod
    def check_industries(cls, value: list[str]) -> list[str]:
        valid = {item.value for item in Industry}
        invalid = [item for item in value if item not in valid]
        if invalid:
            raise ValueError(f"行业标签不合法: {invalid}，可选 {sorted(valid)}")
        return value


class PublishRequest(BaseModel):
    publish_note: str = Field(default="", max_length=1000)


class SourceUpdateRequest(BaseModel):
    enabled: bool | None = None
    owner_note: str | None = Field(default=None, max_length=400)
