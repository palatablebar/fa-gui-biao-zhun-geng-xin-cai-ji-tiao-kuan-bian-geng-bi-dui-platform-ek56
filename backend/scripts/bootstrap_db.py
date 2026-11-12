"""建表引导：幂等 create_all（容器 entrypoint 第一步）。

demo 场景下用 SQLAlchemy metadata 建表，避免首次启动卡在迁移版本对齐；
正式环境可改用 `alembic upgrade head`（见 backend/migrations/）。
"""
from __future__ import annotations

from sqlalchemy import text

from src.config.database import engine
from src.models import Base


def _ensure_current_unique_index() -> None:
    """为已存在的库补「每部法规至多一个现行版本」硬约束。

    create_all 不会给已存在的表/数据补索引；历史库若残留同一 document_key 的多条
    current（旧版发布回退造成的），先按版本号留最高的一条为现行，再建部分唯一索引。
    """
    from src.config.settings import settings

    schema = settings.db_schema
    with engine.begin() as conn:
        conn.execute(
            text(
                f'''
                WITH ranked AS (
                    SELECT id,
                           row_number() OVER (
                               PARTITION BY document_key
                               ORDER BY version_no DESC, created_at DESC, id
                           ) AS rn
                    FROM "{schema}"."documents"
                    WHERE status = 'current'
                )
                UPDATE "{schema}"."documents" AS d
                SET status = 'superseded'
                FROM ranked
                WHERE d.id = ranked.id AND ranked.rn > 1
                '''
            )
        )
        conn.execute(
            text(
                f'CREATE UNIQUE INDEX IF NOT EXISTS "uq_documents_current_per_key" '
                f'ON "{schema}"."documents" ("document_key") '
                f"WHERE status = 'current'"
            )
        )


def main() -> None:
    from src.config.settings import settings

    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.db_schema}"'))
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "postgresql":
        _ensure_current_unique_index()
    print(f"[bootstrap] schema={settings.db_schema} tables={len(Base.metadata.tables)}", flush=True)


if __name__ == "__main__":
    main()
