"""算法 1a：条款切分。

输入：法规全文（纯文本，`第X条` 起头，可带 `（一）` 款）。
输出：Clause 列表 + 解析问题列表（空条文/无条头/重复条号 → 计入 unparsed）。

条头正则同时接受中文数字与阿拉伯数字；条号重排不会影响切分（编号只做定位与展示）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.utils.textutils import normalize_for_match

ARTICLE_RE = re.compile(r"第\s*([一二三四五六七八九十百千零〇两0-9]{1,8})\s*条")
SUB_ITEM_RE = re.compile(r"^\s*[（(]\s*([一二三四五六七八九十]{1,4})\s*[）)]")
_PREFIX_SYMBOLS = "　 \t:：、.。"


@dataclass
class Clause:
    """一条条款。`label` 保留原文条号（第四条），`number` 为整数条号。"""

    index: int
    label: str
    number: int | None
    text: str
    sub_items: list[str] = field(default_factory=list)

    @property
    def normalized(self) -> str:
        return normalize_for_match(self.text)

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "label": self.label,
            "number": self.number,
            "text": self.text,
            "sub_items": self.sub_items,
            "char_count": len(self.text),
        }


@dataclass
class SplitResult:
    clauses: list[Clause]
    issues: list[dict]
    preamble: str = ""

    @property
    def unparsed_count(self) -> int:
        return len(self.issues)


_CN_DIGITS = "零一二三四五六七八九"


def int_to_chinese(value: int) -> str:
    """1..999 整数转中文数字（条号展示用）。"""
    if value <= 0 or value >= 1000:
        return str(value)
    if value < 10:
        return _CN_DIGITS[value]
    if value < 100:
        tens, ones = divmod(value, 10)
        head = "十" if tens == 1 else f"{_CN_DIGITS[tens]}十"
        return head if ones == 0 else f"{head}{_CN_DIGITS[ones]}"
    hundreds, rest = divmod(value, 100)
    head = f"{_CN_DIGITS[hundreds]}百"
    if rest == 0:
        return head
    if rest < 10:
        return f"{head}零{_CN_DIGITS[rest]}"
    return f"{head}{int_to_chinese(rest)}"


def _clean_block(text: str) -> str:
    lines = [line.strip().strip(_PREFIX_SYMBOLS) for line in text.splitlines()]
    kept = [line for line in lines if line]
    return "\n".join(kept).strip()


def _extract_sub_items(block: str) -> list[str]:
    items: list[str] = []
    for line in block.splitlines():
        if SUB_ITEM_RE.match(line.strip()):
            items.append(line.strip())
    return items


def split_clauses(raw_text: str) -> SplitResult:
    """切分条款。空文本/无条头返回单条 unparsed。"""
    raw = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not raw.strip():
        return SplitResult(
            clauses=[],
            issues=[{"reason": "empty_document", "detail": "正文为空", "clause_label": ""}],
        )

    matches = list(ARTICLE_RE.finditer(raw))
    if not matches:
        return SplitResult(
            clauses=[],
            issues=[{"reason": "no_article_header", "detail": "未识别到「第X条」条头", "clause_label": ""}],
            preamble=_clean_block(raw)[:200],
        )

    preamble = _clean_block(raw[: matches[0].start()])[:200]
    clauses: list[Clause] = []
    issues: list[dict] = []

    for order, match in enumerate(matches):
        number_raw = match.group(1)
        from src.utils.textutils import clause_number_to_int

        number = clause_number_to_int(number_raw)
        start = match.end()
        end = matches[order + 1].start() if order + 1 < len(matches) else len(raw)
        block = _clean_block(raw[start:end])
        label = f"第{number_raw}条"
        if not block:
            issues.append({"reason": "empty_clause", "detail": f"{label} 正文为空", "clause_label": label})
            continue
        if number is None:
            issues.append({"reason": "clause_number_unparsed", "detail": f"条号无法解析: {number_raw}", "clause_label": label})
        clauses.append(
            Clause(
                index=len(clauses),
                label=label,
                number=number,
                text=block,
                sub_items=_extract_sub_items(block),
            )
        )

    if not clauses:
        issues.append({"reason": "empty_document", "detail": "全部条款正文为空", "clause_label": ""})
    return SplitResult(clauses=clauses, issues=issues, preamble=preamble)
