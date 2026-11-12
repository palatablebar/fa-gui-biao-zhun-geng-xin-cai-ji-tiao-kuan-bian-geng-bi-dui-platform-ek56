"""中文文本工具：归一、数字签名、编辑距离比、SimHash。

只依赖标准库，保证 seed / 容器 / 本地复算逐位一致。
"""
from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher

CN_DIGITS: dict[str, int] = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
}
CN_UNITS: dict[str, int] = {"十": 10, "百": 100, "千": 1000}

_WS_RE = re.compile(r"\s+")
_FW_PUNCT = str.maketrans(
    {
        "\uff0c": ",", "\u3002": ".", "\u3001": ",", "\uff1b": ";", "\uff1a": ":",
        "\uff08": "(", "\uff09": ")", "\u3010": "[", "\u3011": "]",
        "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    }
)
_NUM_RE = re.compile(r"\d+(?:\.\d+)?%?")
_CN_NUM_UNIT_RE = re.compile(r"([零〇一二两三四五六七八九十百千]+)(年|个月|个工作日|日|天|小时|米|万元|元|人|次|%)")


def chinese_to_int(text: str) -> int | None:
    """中文数字转整数：一 → 1，二十三 → 23，一百零五 → 105。"""
    if not text:
        return None
    if text.isdigit():
        return int(text)
    total = 0
    section = 0
    number = 0
    for char in text:
        if char in CN_DIGITS:
            number = CN_DIGITS[char]
        elif char in CN_UNITS:
            unit = CN_UNITS[char]
            if number == 0:
                number = 1
            section += number * unit
            number = 0
        else:
            return None
    total += section + number
    return total


def clause_number_to_int(raw: str) -> int | None:
    """条号字符串（阿拉伯/中文）转整数。"""
    cleaned = (raw or "").strip()
    if not cleaned:
        return None
    if cleaned.isdigit():
        return int(cleaned)
    return chinese_to_int(cleaned)


def normalize_for_match(text: str) -> str:
    """条款正文归一：去空白、统一标点、去掉条号前缀，用于精确匹配与相似度。"""
    if not text:
        return ""
    value = _WS_RE.sub("", text).translate(_FW_PUNCT)
    value = value.replace(";", ",")
    return value.strip(".,;:。，；：、")


def numbers_signature(text: str) -> list[str]:
    """抽出数字/期限/百分比签名，按升序去重（阈值变化检测用）。"""
    normalized = normalize_for_match(text)
    found: set[str] = set()
    for match in _NUM_RE.findall(normalized):
        found.add(match)
    for raw, unit in _CN_NUM_UNIT_RE.findall(normalized):
        value = chinese_to_int(raw)
        if value is not None:
            found.add(f"{value}{unit}")
    return sorted(found)


def edit_ratio(old: str, new: str) -> float:
    """字符编辑距离比：0 = 完全相同，1 = 完全不同。"""
    left = normalize_for_match(old)
    right = normalize_for_match(new)
    if left == right:
        return 0.0
    if not left or not right:
        return 1.0
    return round(1.0 - SequenceMatcher(None, left, right).ratio(), 6)


def similarity(old: str, new: str) -> float:
    """归一后的序列相似度（0..1），用于精确匹配兜底。"""
    left = normalize_for_match(old)
    right = normalize_for_match(new)
    if left == right:
        return 1.0
    if not left or not right:
        return 0.0
    return round(SequenceMatcher(None, left, right).ratio(), 6)


def shingles(text: str, size: int = 3) -> set[str]:
    """字符 n-gram 集合（中文不依赖分词器，避免引入 jieba 词典不稳）。"""
    value = normalize_for_match(text)
    if not value:
        return set()
    if len(value) <= size:
        return {value}
    return {value[index:index + size] for index in range(len(value) - size + 1)}


def simhash(tokens: set[str], bits: int = 64) -> int:
    """确定性 SimHash：md5(token) 决定位权，无随机种子。"""
    if not tokens:
        return 0
    vector = [0] * bits
    for token in sorted(tokens):
        digest = hashlib.md5(token.encode("utf-8")).digest()
        value = int.from_bytes(digest[:8], "big")
        for index in range(bits):
            if value >> index & 1:
                vector[index] += 1
            else:
                vector[index] -= 1
    result = 0
    for index in range(bits):
        if vector[index] > 0:
            result |= 1 << index
    return result


def hamming_distance(left: int, right: int) -> int:
    return bin(left ^ right).count("1")


def simhash_similarity(left_text: str, right_text: str) -> float:
    """SimHash 汉明距换算相似度：1 - d/64。"""
    left = simhash(shingles(left_text))
    right = simhash(shingles(right_text))
    if left == 0 or right == 0:
        return 0.0
    return round(1.0 - hamming_distance(left, right) / 64.0, 6)
