"""算法 1b：条款对齐（编号相似 + TF-IDF 余弦 + SimHash 汉明距）。

对齐顺序：
1) 归一文本完全相等 → 直接配对，相似度 1.0（**编号重排不会产生噪声**：条号不参与判等）；
2) 其余候选按 `0.7·TF-IDF 余弦 + 0.3·SimHash 相似` 建相似度矩阵，贪心取最高分配对
   （条号相同时仅给 +0.02 的破平权重，不改变阈值判定）；
3) 未配对的旧条款 = 删除，未配对的新条款 = 新增；
4) 配对但归一文本不完全相同 → 修改；`similarity < 0.86` 记为「实质修改」，
   `0.86 ≤ similarity < 1` 记为「措辞修改」（仍进变更项，避免编辑性变更被静默吞掉）。

复杂度 O(n²)（n ≤ 300 时 < 10ms），结果完全确定（无随机、无外部模型）。
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from src.constants.enums import ChangeType
from src.services.clause_splitter import Clause
from src.utils.textutils import normalize_for_match, shingles, simhash_similarity, simhash, hamming_distance

MATCH_THRESHOLD = 0.55
CHANGE_THRESHOLD = 0.86
EXACT_BONUS = 0.0
NUMBER_BONUS = 0.02


@dataclass
class AlignmentPair:
    old: Clause | None
    new: Clause | None
    similarity: float
    change_type: str
    exact: bool = False

    @property
    def renumbered(self) -> bool:
        if self.old is None or self.new is None:
            return False
        return self.old.number != self.new.number

    def to_dict(self) -> dict:
        return {
            "old_index": self.old.index if self.old else None,
            "new_index": self.new.index if self.new else None,
            "old_label": self.old.label if self.old else "",
            "new_label": self.new.label if self.new else "",
            "old_number": self.old.number if self.old else None,
            "new_number": self.new.number if self.new else None,
            "old_text": self.old.text if self.old else "",
            "new_text": self.new.text if self.new else "",
            "similarity": self.similarity,
            "change_type": self.change_type,
            "renumbered": self.renumbered,
        }


@dataclass
class AlignResult:
    pairs: list[AlignmentPair]
    stats: dict = field(default_factory=dict)

    def changes(self) -> list[AlignmentPair]:
        return [pair for pair in self.pairs if pair.change_type != "unchanged"]


def _bigrams(text: str) -> list[str]:
    """字符二元组 + 数字整词：中文免分词、口径稳定。"""
    normalized = normalize_for_match(text)
    if not normalized:
        return []
    tokens: list[str] = [normalized[index:index + 2] for index in range(max(1, len(normalized) - 1))]
    import re

    tokens.extend(re.findall(r"\d+(?:\.\d+)?%?", normalized))
    return tokens


def _tfidf_vectors(corpus: list[str]) -> list[dict[str, float]]:
    tokenized = [_bigrams(text) for text in corpus]
    doc_count = len(corpus)
    df: Counter[str] = Counter()
    for tokens in tokenized:
        df.update(set(tokens))
    vectors: list[dict[str, float]] = []
    for tokens in tokenized:
        if not tokens:
            vectors.append({})
            continue
        tf = Counter(tokens)
        total = float(len(tokens))
        vector: dict[str, float] = {}
        for token, count in tf.items():
            idf = math.log((1.0 + doc_count) / (1.0 + df[token])) + 1.0
            vector[token] = (count / total) * idf
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
        vectors.append({token: value / norm for token, value in vector.items()})
    return vectors


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(token, 0.0) for token, value in left.items())


def _pair_score(
    left: Clause,
    right: Clause,
    cosine: float,
    left_hash: int,
    right_hash: int,
) -> tuple[float, float]:
    sim_hash_sim = 1.0 - hamming_distance(left_hash, right_hash) / 64.0 if (left_hash and right_hash) else 0.0
    text_sim = 0.7 * cosine + 0.3 * sim_hash_sim
    bonus = NUMBER_BONUS if (left.number is not None and left.number == right.number) else 0.0
    return round(text_sim, 6), round(text_sim + bonus, 6)


def align_clauses(
    old_clauses: list[Clause],
    new_clauses: list[Clause],
    match_threshold: float = MATCH_THRESHOLD,
    change_threshold: float = CHANGE_THRESHOLD,
) -> AlignResult:
    corpus = [clause.text for clause in old_clauses] + [clause.text for clause in new_clauses]
    vectors = _tfidf_vectors(corpus)
    old_vectors = vectors[: len(old_clauses)]
    new_vectors = vectors[len(old_clauses):]
    old_hashes = [simhash(shingles(clause.text)) for clause in old_clauses]
    new_hashes = [simhash(shingles(clause.text)) for clause in new_clauses]

    matched_old: set[int] = set()
    matched_new: set[int] = set()
    pairs: list[AlignmentPair] = []

    # 1) 归一文本完全一致：条号重排在这里被静默吸收
    new_by_norm: dict[str, list[int]] = {}
    for index, clause in enumerate(new_clauses):
        new_by_norm.setdefault(clause.normalized, []).append(index)
    for old_index, clause in enumerate(old_clauses):
        candidates = new_by_norm.get(clause.normalized)
        if not candidates:
            continue
        for new_index in candidates:
            if new_index in matched_new:
                continue
            matched_old.add(old_index)
            matched_new.add(new_index)
            pairs.append(
                AlignmentPair(
                    old=clause,
                    new=new_clauses[new_index],
                    similarity=1.0,
                    change_type="unchanged",
                    exact=True,
                )
            )
            break

    # 2) 相似度矩阵 + 贪心配对
    candidates: list[tuple[float, float, int, int]] = []
    for old_index, old_clause in enumerate(old_clauses):
        if old_index in matched_old:
            continue
        for new_index, new_clause in enumerate(new_clauses):
            if new_index in matched_new:
                continue
            cosine = _cosine(old_vectors[old_index], new_vectors[new_index])
            text_sim, score = _pair_score(
                old_clause, new_clause, cosine, old_hashes[old_index], new_hashes[new_index]
            )
            if text_sim >= match_threshold:
                candidates.append((score, text_sim, old_index, new_index))
    candidates.sort(key=lambda item: (-item[0], item[2], item[3]))

    for _score, text_sim, old_index, new_index in candidates:
        if old_index in matched_old or new_index in matched_new:
            continue
        matched_old.add(old_index)
        matched_new.add(new_index)
        change_type = ChangeType.MODIFIED.value
        pairs.append(
            AlignmentPair(
                old=old_clauses[old_index],
                new=new_clauses[new_index],
                similarity=round(text_sim, 6),
                change_type=change_type,
            )
        )

    # 3) 剩余：删除 / 新增
    for old_index, clause in enumerate(old_clauses):
        if old_index not in matched_old:
            pairs.append(
                AlignmentPair(
                    old=clause,
                    new=None,
                    similarity=0.0,
                    change_type=ChangeType.REMOVED.value,
                )
            )
    for new_index, clause in enumerate(new_clauses):
        if new_index not in matched_new:
            pairs.append(
                AlignmentPair(
                    old=None,
                    new=clause,
                    similarity=0.0,
                    change_type=ChangeType.ADDED.value,
                )
            )

    def sort_key(pair: AlignmentPair) -> tuple[int, int]:
        new_number = pair.new.number if pair.new and pair.new.number is not None else 10_000
        old_number = pair.old.number if pair.old and pair.old.number is not None else 10_000
        return (new_number, old_number)

    pairs.sort(key=sort_key)

    unchanged = sum(1 for pair in pairs if pair.change_type == "unchanged")
    renumbered_pairs = sum(1 for pair in pairs if pair.renumbered)
    renumber_noise_free = all(
        pair.change_type in ("unchanged",) for pair in pairs if pair.exact and pair.renumbered
    )
    modified_pairs = [pair for pair in pairs if pair.change_type == ChangeType.MODIFIED.value]
    stats = {
        "total_old": len(old_clauses),
        "total_new": len(new_clauses),
        "matched": len(matched_old),
        "unchanged": unchanged,
        "modified": len(modified_pairs),
        "substantial_modified": sum(1 for pair in modified_pairs if pair.similarity < change_threshold),
        "wording_modified": sum(1 for pair in modified_pairs if pair.similarity >= change_threshold),
        "added": sum(1 for pair in pairs if pair.change_type == ChangeType.ADDED.value),
        "removed": sum(1 for pair in pairs if pair.change_type == ChangeType.REMOVED.value),
        "renumbered_pairs": renumbered_pairs,
        "renumber_noise_free": renumber_noise_free,
        "change_count": sum(1 for pair in pairs if pair.change_type != "unchanged"),
        "match_threshold": match_threshold,
        "change_threshold": change_threshold,
    }
    return AlignResult(pairs=pairs, stats=stats)
