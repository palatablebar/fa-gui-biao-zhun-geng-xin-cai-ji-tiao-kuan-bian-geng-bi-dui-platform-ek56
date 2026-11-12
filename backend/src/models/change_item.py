"""ChangeItem：条款级变更项（实体 4/4）。"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.config.settings import settings
from src.models.base import Base, TimestampMixin, new_uuid


class ChangeItem(Base, TimestampMixin):
    __tablename__ = "change_items"
    __table_args__ = {"schema": settings.db_schema}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    diff_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{settings.db_schema}.diff_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    clause_no_old: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clause_no_new: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clause_label_old: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    clause_label_new: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    old_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    new_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    similarity: Mapped[float] = mapped_column(nullable=False, default=0)
    edit_ratio: Mapped[float] = mapped_column(nullable=False, default=0)
    keywords: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    industries: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    impact_industries: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    impact_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    publish_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
