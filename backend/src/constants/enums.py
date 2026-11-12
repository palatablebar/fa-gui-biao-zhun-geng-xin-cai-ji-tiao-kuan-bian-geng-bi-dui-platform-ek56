"""共享枚举（后端定义）。

前端对应文件：frontend/src/constants/enums.ts（两份必须一致，README 列出全部出现位置）。
"""
from __future__ import annotations

from enum import Enum


class SourceKind(str, Enum):
    """来源类型。"""

    NATIONAL_STANDARD = "national_standard"      # 国家标准全文公开系统
    REGULATORY = "regulatory"                    # 市场监管总局规章
    LOCAL_ENV = "local_env"                      # 地方生态环境厅文件


class DocumentStatus(str, Enum):
    """文档版本状态。"""

    CURRENT = "current"          # 当前生效版本
    SUPERSEDED = "superseded"    # 历史版本
    COLLECTED = "collected"      # 刚采集、未比对


class DiffRunStatus(str, Enum):
    """比对批次状态。"""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ChangeType(str, Enum):
    """条款级变更类型。"""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class Severity(str, Enum):
    """变更影响等级（算法输出）。"""

    MAJOR = "major"          # 重大
    GENERAL = "general"      # 一般
    EDITORIAL = "editorial"  # 编辑性
    UNPARSED = "unparsed"    # 解析失败/空条文


class Industry(str, Enum):
    """影响行业标签。"""

    MANUFACTURING = "manufacturing"      # 制造
    MEDICAL = "medical"                  # 医疗
    ENVIRONMENTAL = "environmental"      # 环保


CHANGE_TYPE_LABELS: dict[str, str] = {
    ChangeType.ADDED.value: "新增",
    ChangeType.REMOVED.value: "删除",
    ChangeType.MODIFIED.value: "修改",
}

SEVERITY_LABELS: dict[str, str] = {
    Severity.MAJOR.value: "重大",
    Severity.GENERAL.value: "一般",
    Severity.EDITORIAL.value: "编辑性",
    Severity.UNPARSED.value: "解析失败",
}

INDUSTRY_LABELS: dict[str, str] = {
    Industry.MANUFACTURING.value: "制造",
    Industry.MEDICAL.value: "医疗",
    Industry.ENVIRONMENTAL.value: "环保",
}

SOURCE_KIND_LABELS: dict[str, str] = {
    SourceKind.NATIONAL_STANDARD.value: "国家标准全文公开系统",
    SourceKind.REGULATORY.value: "市场监管总局规章库",
    SourceKind.LOCAL_ENV.value: "地方生态环境厅文件",
}
