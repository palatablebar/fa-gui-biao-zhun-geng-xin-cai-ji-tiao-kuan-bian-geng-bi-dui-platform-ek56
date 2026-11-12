"""幂等演示数据入口：`python -m scripts.seed_demo`（容器启动 SEED_DEMO=true 自动跑一次）。

自然键：
  Source.code / Document(document_key, version_label) / DiffRun(base_document_id, target_document_id)
  / User.email

期望结果（首次）：
  3 来源 / 2 部法规 / 6 个版本 / 2 次比对 / 9 条变更（3 重大 + 4 一般 + 2 编辑性）
  / 3 个账号；其中一次比对是「编号重排版」→ 0 条变更（证明编号重排不产生噪声）。
重复执行只打印 SEED_SKIPPED，末尾 SEED_SUMMARY 行逐字一致，供幂等校验。
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select

from src.config.database import session_scope
from src.constants.enums import DiffRunStatus, Severity
from src.constants.log_templates import ACTION_DIFF_RUN
from src.models.change_item import ChangeItem
from src.models.diff_run import DiffRun
from src.models.document import Document
from src.models.source import Source
from src.models.user import User
from src.services import audit_service
from src.services.clause_splitter import split_clauses
from src.services.diff_service import ALGORITHM_VERSION, execute_diff_run_in_session
from src.utils.password import hash_password
from scripts import fixtures

CREATED = 0
SKIPPED = 0
LABEL = "lawdelta"

SEED_CRAWL_STAMP = datetime(2026, 11, 10, 6, 30, tzinfo=timezone.utc)


def _log(kind: str, entity: str, key: str) -> None:
    global CREATED, SKIPPED
    if kind == "SEED_CREATED":
        CREATED += 1
    else:
        SKIPPED += 1
    print(f"{kind} entity={entity} key={key}", flush=True)


def _created(entity: str, key: str) -> None:
    _log("SEED_CREATED", entity, key)


def _skipped(entity: str, key: str) -> None:
    _log("SEED_SKIPPED", entity, key)


# ------------------------------------------------------------------ 账号 ----


def seed_users(db) -> dict[str, User]:
    users: dict[str, User] = {}
    for email, display_name, role in fixtures.DEMO_USERS:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password(fixtures.DEMO_PASSWORD),
                display_name=display_name,
                role=role,
                is_active=True,
            )
            db.add(user)
            db.flush()
            _created("User", email)
        else:
            _skipped("User", email)
        users[role] = user
    return users


# ------------------------------------------------------------------ 来源 ----


def seed_sources(db) -> dict[str, Source]:
    sources: dict[str, Source] = {}
    for spec in fixtures.DEMO_SOURCES:
        source = db.execute(select(Source).where(Source.code == spec["code"])).scalar_one_or_none()
        if source is None:
            source = Source(
                code=spec["code"],
                name=spec["name"],
                kind=spec["kind"],
                base_url=spec["base_url"],
                fetch_cycle=spec["fetch_cycle"],
                owner_note=spec["owner_note"],
                enabled=spec["enabled"],
                last_crawled_at=SEED_CRAWL_STAMP,
                next_issue_hint=spec.get("next_issue_hint"),
            )
            db.add(source)
            db.flush()
            _created("Source", spec["code"])
        else:
            _skipped("Source", spec["code"])
        sources[spec["code"]] = source
    return sources


# -------------------------------------------------------------- 文档版本 ----


def seed_documents(db, sources: dict[str, Source]) -> dict[tuple[str, str], Document]:
    documents: dict[tuple[str, str], Document] = {}
    for spec in fixtures.DOCUMENT_SPECS:
        source = sources[spec["source_code"]]
        for version in spec["versions"]:
            key = (spec["document_key"], version["version_label"])
            existing = db.execute(
                select(Document).where(
                    Document.document_key == spec["document_key"],
                    Document.version_label == version["version_label"],
                )
            ).scalar_one_or_none()
            if existing is not None:
                _skipped("Document", f"{key[0]}@{key[1]}")
                documents[key] = existing
                continue
            raw_text = fixtures.render_document(version["bodies"])
            split = split_clauses(raw_text)
            document = Document(
                source_id=source.id,
                document_key=spec["document_key"],
                title=spec["title"],
                issuer=spec["issuer"],
                version_label=version["version_label"],
                version_no=version["version_no"],
                status=version["status"],
                issued_at=version["issued_at"],
                effective_at=version["effective_at"],
                raw_text=raw_text,
                clause_count=len(split.clauses),
                content_hash=hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
                collected_at=SEED_CRAWL_STAMP,
            )
            db.add(document)
            db.flush()
            _created("Document", f"{key[0]}@{key[1]}")
            documents[key] = document
    return documents


# ---------------------------------------------------------------- 比对批次 ----


def seed_diff_run(
    db,
    spec: dict,
    documents: dict[tuple[str, str], Document],
    users: dict[str, User],
) -> tuple[DiffRun, bool]:
    base = documents[(spec["document_key"], spec["base_version"])]
    target = documents[(spec["document_key"], spec["target_version"])]
    run = db.execute(
        select(DiffRun).where(
            DiffRun.base_document_id == base.id,
            DiffRun.target_document_id == target.id,
        )
    ).scalar_one_or_none()
    if run is not None:
        _skipped("DiffRun", f"{spec['document_key']} {base.version_label}->{target.version_label}")
        return run, False

    run = DiffRun(
        document_key=spec["document_key"],
        base_document_id=base.id,
        target_document_id=target.id,
        requested_by=users[spec["requested_by"].split("@")[0]].id
        if spec["requested_by"].split("@")[0] in users
        else users["analyst"].id,
        status=DiffRunStatus.QUEUED.value,
        algorithm_version=ALGORITHM_VERSION,
        stats={
            "base_label": base.version_label,
            "target_label": target.version_label,
            "base_clause_count": base.clause_count,
            "target_clause_count": target.clause_count,
            "seeded": True,
        },
        severity_counts={},
    )
    db.add(run)
    db.flush()
    audit_service.record(
        db,
        action=ACTION_DIFF_RUN,
        actor=users["analyst"],
        entity_type="diff_run",
        entity_id=run.id,
        detail={"document_key": run.document_key, "base": base.version_label, "target": target.version_label},
    )
    db.commit()
    execute_diff_run_in_session(db, run)
    db.refresh(run)
    _created("DiffRun", f"{spec['document_key']} {base.version_label}->{target.version_label}")
    return run, True


def seed_review_and_publish(db, run: DiffRun, spec: dict, users: dict[str, User]) -> None:
    """确认 2 条并写影响行业，然后发布（幂等）。"""
    from src.services.change_service import confirm_change, publish_run

    if spec.get("publish") and run.published_at is not None:
        _skipped("Review", f"run={run.id} already-published")
        return

    for confirm_spec in spec.get("confirm", []):
        severity = confirm_spec["severity"]
        candidate = db.execute(
            select(ChangeItem)
            .where(
                ChangeItem.diff_run_id == run.id,
                ChangeItem.severity == severity,
                ChangeItem.confirmed.is_(False),
            )
            .order_by(ChangeItem.clause_no_new.nulls_last(), ChangeItem.clause_no_old.nulls_last())
        ).scalars().first()
        if candidate is None:
            _skipped("Review", f"run={run.id} severity={severity}")
            continue
        confirm_change(
            db,
            candidate.id,
            actor=users["analyst"],
            impact_industries=confirm_spec["impact_industries"],
            impact_note=confirm_spec["impact_note"],
        )
        _created("Review", f"change={candidate.id} severity={severity}")

    if spec.get("publish"):
        confirmed = db.execute(
            select(ChangeItem).where(
                ChangeItem.diff_run_id == run.id,
                ChangeItem.confirmed.is_(True),
                ChangeItem.published.is_(False),
            )
        ).scalars().all()
        if confirmed:
            publish_run(
                db,
                run.id,
                actor=users["admin"],
                publish_note=spec.get("publish_note", ""),
            )
            _created("Publish", f"run={run.id} changes={len(confirmed)}")
        else:
            _skipped("Publish", f"run={run.id}")


# -------------------------------------------------------------------- 汇总 ----


def summary_counts(db) -> dict[str, int]:
    return {
        "brand": LABEL,  # type: ignore[dict-item]
        "sources": int(db.execute(select(func.count(Source.id))).scalar_one()),
        "documents": int(db.execute(select(func.count(func.distinct(Document.document_key)))).scalar_one()),
        "versions": int(db.execute(select(func.count(Document.id))).scalar_one()),
        "diffruns": int(db.execute(select(func.count(DiffRun.id))).scalar_one()),
        "changes": int(db.execute(select(func.count(ChangeItem.id))).scalar_one()),
        "users": int(db.execute(select(func.count(User.id))).scalar_one()),
    }


def format_summary(counts: dict[str, Any]) -> str:
    """固定的键与顺序：brand sources documents versions diffruns changes users。"""
    return (
        f"SEED_SUMMARY brand={counts['brand']} sources={counts['sources']} "
        f"documents={counts['documents']} versions={counts['versions']} "
        f"diffruns={counts['diffruns']} changes={counts['changes']} users={counts['users']}"
    )


def seed_all() -> dict[str, Any]:
    with session_scope() as db:
        users = seed_users(db)
        sources = seed_sources(db)
        documents = seed_documents(db, sources)

        for spec in fixtures.SEED_DIFF_SPECS:
            run, created = seed_diff_run(db, spec, documents, users)
            if created:
                seed_review_and_publish(db, run, spec, users)

        db.flush()
        counts = summary_counts(db)
        severity = dict(
            db.execute(
                select(ChangeItem.severity, func.count(ChangeItem.id)).group_by(ChangeItem.severity)
            ).all()
        )
        print(
            "SEED_SEVERITY "
            + " ".join(
                f"{level.value}={severity.get(level.value, 0)}"
                for level in (Severity.MAJOR, Severity.GENERAL, Severity.EDITORIAL)
            ),
            flush=True,
        )
        print(format_summary(counts), flush=True)
        return {"created": CREATED, "skipped": SKIPPED, "counts": counts}


if __name__ == "__main__":
    result = seed_all()
    print(f"SEED_DONE created={result['created']} skipped={result['skipped']}", flush=True)
    sys.exit(0)
