"""文档版本（Document）查询与序列化。"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.diff_run import DiffRun
from src.models.document import Document
from src.models.source import Source
from src.services.clause_splitter import split_clauses
from src.utils.errors import not_found


def list_documents(db: Session) -> list[dict]:
    rows = db.execute(select(Document).order_by(Document.document_key, Document.version_no)).scalars().all()
    sources = {source.id: source for source in db.execute(select(Source)).scalars().all()}
    grouped: dict[str, dict] = {}
    for document in rows:
        bucket = grouped.setdefault(
            document.document_key,
            {
                "document_key": document.document_key,
                "title": document.title,
                "issuer": document.issuer,
                "source": sources.get(document.source_id).name if sources.get(document.source_id) else "",
                "source_code": sources.get(document.source_id).code if sources.get(document.source_id) else "",
                "source_id": str(document.source_id),
                "versions": [],
                "current_version": "",
            },
        )
        bucket["versions"].append(serialize_version(document))
        if document.status == "current":
            bucket["current_version"] = document.version_label
    for bucket in grouped.values():
        bucket["versions"].sort(key=lambda item: item["version_no"])
    return list(grouped.values())


def get_document(db: Session, version_id: uuid.UUID) -> Document:
    document = db.get(Document, version_id)
    if document is None:
        raise not_found("文档版本", version_id)
    return document


def get_by_label(db: Session, document_key: str, version_label: str) -> Document | None:
    return db.execute(
        select(Document).where(
            Document.document_key == document_key,
            Document.version_label == version_label,
        )
    ).scalar_one_or_none()


def version_history(db: Session, document_key: str) -> list[DiffRun]:
    return (
        db.execute(
            select(DiffRun).where(DiffRun.document_key == document_key).order_by(DiffRun.created_at.desc())
        )
        .scalars()
        .all()
    )


def serialize_version(document: Document, *, with_clauses: bool = False) -> dict:
    payload = {
        "id": str(document.id),
        "document_key": document.document_key,
        "title": document.title,
        "issuer": document.issuer,
        "source_id": str(document.source_id),
        "version_label": document.version_label,
        "version_no": document.version_no,
        "status": document.status,
        "issued_at": document.issued_at.isoformat() if document.issued_at else None,
        "effective_at": document.effective_at.isoformat() if document.effective_at else None,
        "clause_count": document.clause_count,
        "content_hash": document.content_hash,
        "collected_at": document.collected_at.isoformat() if document.collected_at else None,
    }
    if with_clauses:
        split = split_clauses(document.raw_text)
        payload["clauses"] = [clause.to_dict() for clause in split.clauses]
        payload["parse_issues"] = split.issues
        payload["raw_text"] = document.raw_text
    return payload
