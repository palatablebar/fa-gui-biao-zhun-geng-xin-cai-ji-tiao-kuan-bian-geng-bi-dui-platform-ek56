"""配额/限流阈值（Redis 滑动窗口）。"""
from __future__ import annotations

from src.config.settings import settings

RATE_LIMIT_DIFF_PER_MINUTE = settings.rate_limit_diff_per_minute
RATE_LIMIT_CRAWL_PER_MINUTE = settings.rate_limit_crawl_per_minute
RATE_LIMIT_DEFAULT_PER_MINUTE = settings.rate_limit_default_per_minute

# 单次比对允许的条款上限（超出直接拒绝，避免 O(n^2) 相似度矩阵爆量）
MAX_CLAUSES_PER_DIFF = 600
# 单文档正文上限（字符）
MAX_DOCUMENT_CHARS = 400_000
