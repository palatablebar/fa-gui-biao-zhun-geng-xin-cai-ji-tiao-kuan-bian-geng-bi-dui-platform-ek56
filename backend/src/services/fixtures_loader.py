"""fixture 访问层：把 scripts/fixtures 里的条款正文渲染成可入库的文本。

容器内 `scripts` 包位于 /app/scripts（backend 根），worker 内为 /app/backend/scripts，
两者都在 PYTHONPATH 上；service 只依赖本模块，避免业务代码散布 fixture 细节。
"""
from __future__ import annotations

from datetime import date

from scripts import fixtures


def collectables_for(source_code: str) -> list[dict]:
    items: list[dict] = []
    for entry in fixtures.COLLECTIONS.get(source_code, []):
        item = dict(entry)
        item["raw_text"] = fixtures.render_document(entry["bodies"])
        items.append(item)
    return items


def document_spec(document_key: str) -> dict | None:
    for spec in fixtures.DOCUMENT_SPECS:
        if spec["document_key"] == document_key:
            return spec
    return None


def version_spec(document_key: str, version_label: str) -> dict | None:
    spec = document_spec(document_key)
    if not spec:
        return None
    for version in spec["versions"]:
        if version["version_label"] == version_label:
            return version
    return None


def render(bodies: list[str]) -> str:
    return fixtures.render_document(bodies)


def as_date(value: object) -> date | None:
    return value if isinstance(value, date) else None
