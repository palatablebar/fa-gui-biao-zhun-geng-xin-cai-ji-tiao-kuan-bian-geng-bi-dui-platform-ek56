"""Document：法规文档版本（实体 2/4）。

一行 = 一个版本文本；`document_key` 相同即同一部法规，版本号唯一。
`documents` 计数 = 不同 document_key 数；`versions` 计数 = 行数。
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.config.settings import settings
from src.models.base import Base, TimestampMixin, new_uuid, utcnow


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("document_key", "version_label", name="uq_document_version"),
        # 硬约束：同一部法规至多一个现行版本（并发发布的最后兜底，业务侧另做单调推进判断）
        Index(
            "uq_documents_current_per_key",
            "document_key",
            unique=True,
            postgresql_where=text("status = 'current'"),
            sqlite_where=text("status = 'current'"),
        ),
        {"schema": settings.db_schema},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{settings.db_schema}.sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    version_label: Mapped[str] = mapped_column(String(20), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    issuer: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="current", index=True)
    issued_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    clause_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
