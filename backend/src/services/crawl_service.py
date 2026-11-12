"""采集：从来源维护的待采集清单里落一个新文档版本（离线 fixture，确定性）。

真实系统这里会是 HTTP/PDF 适配器；demo 用 `scripts/fixtures.COLLECTIONS` 模拟
「来源已发布、尚未入库」的新版本，保证同一来源重复采集不会产生重复版本。
"""
from __future__ import annotations

import hashlib

from sqlalchemy.orm import Session

from src.constants import error_codes as codes
from src.constants.limits import MAX_DOCUMENT_CHARS
from src.constants.log_templates import ACTION_CRAWL
from src.models.base import utcnow
from src.models.document import Document
from src.models.source import Source
from src.models.user import User
from src.services import audit_service, document_service
from src.services.clause_splitter import split_clauses
from src.services.document_service import serialize_version
from src.services.fixtures_loader import collectables_for
from src.utils.errors import AppError


def crawl_source(db: Session, source: Source, actor: User, trace_id: str = "") -> dict:
    if not source.enabled:
        raise AppError(codes.SOURCE_DISABLED, detail=f"source={source.code} enabled=false")

    for item in collectables_for(source.code):
        existing = document_service.get_by_label(db, item["document_key"], item["version_label"])
        if existing is not None:
            continue
        raw_text = item["raw_text"]
        if len(raw_text) > MAX_DOCUMENT_CHARS:
            raise AppError(codes.DIFF_TOO_LARGE, detail=f"document chars={len(raw_text)}")
        split = split_clauses(raw_text)
        if not split.clauses:
            raise AppError(codes.DOCUMENT_EMPTY, detail=f"clauses=0 document={item['document_key']}")

        document = Document(
            source_id=source.id,
            document_key=item["document_key"],
            title=item["title"],
            version_label=item["version_label"],
            version_no=item["version_no"],
            issuer=item.get("issuer", ""),
            status="collected",
            issued_at=item.get("issued_at"),
            effective_at=item.get("effective_at"),
            raw_text=raw_text,
            clause_count=len(split.clauses),
            content_hash=hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
            collected_at=utcnow(),
        )
        db.add(document)
        db.flush()
        source.last_crawled_at = utcnow()
        audit_service.record(
            db,
            action=ACTION_CRAWL,
            actor=actor,
            entity_type="document",
            entity_id=document.id,
            detail={
                "source_code": source.code,
                "document_key": document.document_key,
                "version_label": document.version_label,
                "clause_count": document.clause_count,
                "note": item.get("note", ""),
            },
            trace_id=trace_id,
        )
        db.commit()
        return {
            "created": True,
            "source_code": source.code,
            "document_key": document.document_key,
            "version": serialize_version(document),
            "clause_count": document.clause_count,
            "note": item.get("note", ""),
        }

    raise AppError(
        codes.NO_NEW_VERSION,
        detail=f"source={source.code} 无新增版本（已在库版本不会再采集一次）",
    )
