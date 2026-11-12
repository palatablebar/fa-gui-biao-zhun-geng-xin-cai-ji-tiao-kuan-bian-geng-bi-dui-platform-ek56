"""documents: 每部法规至多一个现行版本

修复历史数据：旧版发布逻辑会把已发布过的低版本重新标为 current，导致同一
document_key 出现多条 current。按版本号保留最高的一条为现行，其余转历史，
再建部分唯一索引作为并发发布的最后兜底。

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-12
"""
from __future__ import annotations

from alembic import op

from src.config.settings import settings

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    schema = settings.db_schema
    bind.exec_driver_sql(
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
    bind.exec_driver_sql(
        f'CREATE UNIQUE INDEX IF NOT EXISTS "uq_documents_current_per_key" '
        f'ON "{schema}"."documents" ("document_key") WHERE status = \'current\''
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    bind.exec_driver_sql(
        f'DROP INDEX IF EXISTS "{settings.db_schema}"."uq_documents_current_per_key"'
    )
