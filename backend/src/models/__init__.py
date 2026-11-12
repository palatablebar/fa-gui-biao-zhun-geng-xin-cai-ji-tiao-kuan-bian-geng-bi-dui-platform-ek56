"""模型汇总：导入即注册到 Base.metadata。"""
from src.models.audit_log import AuditLog
from src.models.base import Base
from src.models.change_item import ChangeItem
from src.models.diff_run import DiffRun
from src.models.document import Document
from src.models.source import Source
from src.models.user import User

__all__ = [
    "AuditLog",
    "Base",
    "ChangeItem",
    "DiffRun",
    "Document",
    "Source",
    "User",
]
