"""算法 2：变更分类与影响等级。

输入：对齐后的条款对（旧文本/新文本/变更类型）。
输出：`重大 / 一般 / 编辑性 / unparsed` + 行业标签 + 命中的关键词 + 可读理由。

口径（全部落库，可复现）：
  edit_ratio    = 1 − SequenceMatcher(归一旧文本, 归一新文本).ratio()
  keyword_delta = 新旧文本在各关键词组上的出现差异（新增或消失的组）
  number_delta  = 数字签名集合变化（19.5% → 21%、一年 → 两年、3 天 → 5 天）

判决：
  新增/删除条款：含 罚款/责令(penalty) 或 资质/许可证(qualification) → 重大；否则 一般。
  修改条款：新引入 penalty / qualification / repeal → 重大；
            edit_ratio ≥ 0.08 或 number_delta 或 任一组关键词增减 → 一般；
            否则 → 编辑性（仅措辞/标点级差异）。
  空条文或解析失败 → unparsed（计入解析问题数，不进入发布）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.constants.enums import ChangeType, Industry, Severity
from src.utils.textutils import edit_ratio, normalize_for_match, numbers_signature

KEYWORD_GROUPS: dict[str, tuple[str, ...]] = {
    "mandatory": ("应当", "应", "必须", "禁止", "不得", "严禁", "须"),
    "penalty": ("罚款", "处罚", "责令", "停产", "吊销", "追究", "没收", "通报"),
    "deadline": ("期限", "之日起", "个工作日内", "日内", "届满", "逾期"),
    "qualification": ("资质", "许可证", "持证", "上岗", "资格证书", "备案", "执业", "检验检测机构"),
    "repeal": ("废止", "删除", "停止执行", "不再适用", "取消"),
    "scope": ("适用于", "不适用", "适用范围", "范围内"),
    "record": ("记录", "留存", "台账", "档案", "保存"),
}

KEYWORD_LABELS: dict[str, str] = {
    "mandatory": "强制性义务",
    "penalty": "罚则",
    "deadline": "期限",
    "qualification": "资质准入",
    "repeal": "废止",
    "scope": "适用范围",
    "record": "记录留档",
}

INDUSTRY_KEYWORDS: dict[str, tuple[str, ...]] = {
    Industry.MANUFACTURING.value: (
        "危险化学品", "动火", "受限空间", "高处作业", "特种作业", "临时用电",
        "生产", "储存", "使用", "作业票", "机械", "粉尘", "安全生产",
    ),
    Industry.MEDICAL.value: (
        "医疗", "药品", "疫苗", "消毒", "诊疗", "医疗机构", "病区", "制药", "临床",
    ),
    Industry.ENVIRONMENTAL.value: (
        "排污", "排放", "监测", "废气", "废水", "固废", "危险废物", "环评", "在线监测", "污染物",
    ),
}

SEVERE_GROUPS = ("penalty", "qualification", "repeal")


@dataclass
class ClassifierResult:
    severity: str
    keywords: list[str]
    industries: list[str]
    reason: str
    edit_ratio: float
    number_delta: bool

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "keywords": self.keywords,
            "industries": self.industries,
            "reason": self.reason,
            "edit_ratio": self.edit_ratio,
            "number_delta": self.number_delta,
        }


def detect_keyword_groups(text: str) -> dict[str, list[str]]:
    normalized = normalize_for_match(text)
    found: dict[str, list[str]] = {}
    for group, words in KEYWORD_GROUPS.items():
        hits = [word for word in words if word in normalized]
        if hits:
            found[group] = hits
    return found


def detect_industries(text: str) -> list[str]:
    normalized = normalize_for_match(text)
    industries: list[str] = []
    for industry, words in INDUSTRY_KEYWORDS.items():
        if any(word in normalized for word in words):
            industries.append(industry)
    return industries


def _flatten(groups: dict[str, list[str]]) -> list[str]:
    return [f"{group}:{word}" for group in sorted(groups) for word in groups[group]]


def classify_change(
    change_type: str,
    old_text: str,
    new_text: str,
) -> ClassifierResult:
    """对一条变更判级。change_type: added / removed / modified。"""
    if change_type == ChangeType.ADDED.value:
        return _classify_one_side(new_text, ChangeType.ADDED.value)
    if change_type == ChangeType.REMOVED.value:
        return _classify_one_side(old_text, ChangeType.REMOVED.value)
    return _classify_modified(old_text, new_text)


def _classify_one_side(text: str, change_type: str) -> ClassifierResult:
    groups = detect_keyword_groups(text)
    industries = detect_industries(text)
    keywords = _flatten(groups)
    label = "新增条款" if change_type == ChangeType.ADDED.value else "删除条款"
    if "penalty" in groups or "qualification" in groups:
        groups_hit = "、".join(
            KEYWORD_LABELS.get(group, group) for group in ("penalty", "qualification") if group in groups
        )
        return ClassifierResult(
            severity=Severity.MAJOR.value,
            keywords=keywords,
            industries=industries,
            reason=f"{label}涉及{groups_hit}，改变义务边界",
            edit_ratio=1.0,
            number_delta=False,
        )
    if "repeal" in groups:
        return ClassifierResult(
            severity=Severity.MAJOR.value,
            keywords=keywords,
            industries=industries,
            reason=f"{label}含废止/停止执行表述",
            edit_ratio=1.0,
            number_delta=False,
        )
    return ClassifierResult(
        severity=Severity.GENERAL.value,
        keywords=keywords,
        industries=industries,
        reason=f"{label}，未涉及罚则或资质准入",
        edit_ratio=1.0,
        number_delta=False,
    )


def _classify_modified(old_text: str, new_text: str) -> ClassifierResult:
    ratio = edit_ratio(old_text, new_text)
    groups_old = set(detect_keyword_groups(old_text))
    groups_new = set(detect_keyword_groups(new_text))
    introduced = groups_new - groups_old
    removed_groups = groups_old - groups_new
    old_numbers = numbers_signature(old_text)
    new_numbers = numbers_signature(new_text)
    number_delta = old_numbers != new_numbers

    keywords_old = detect_keyword_groups(old_text)
    keywords_new = detect_keyword_groups(new_text)
    keywords = sorted(
        {f"new:{item}" for item in _flatten(keywords_new)} | {f"old:{item}" for item in _flatten(keywords_old)}
    )
    industries = sorted(set(detect_industries(old_text)) | set(detect_industries(new_text)))

    severe_introduced = [group for group in SEVERE_GROUPS if group in introduced]
    if severe_introduced:
        labels = "、".join(KEYWORD_LABELS.get(group, group) for group in severe_introduced)
        return ClassifierResult(
            severity=Severity.MAJOR.value,
            keywords=keywords,
            industries=industries,
            reason=f"修改后新增{labels}表述，编辑幅度 {ratio:.3f}",
            edit_ratio=ratio,
            number_delta=number_delta,
        )

    if ratio >= 0.08 or number_delta or introduced or removed_groups:
        parts: list[str] = []
        if number_delta:
            parts.append(f"数值口径变化（{'→'.join(old_numbers) or '空'} ⇒ {'→'.join(new_numbers) or '空'}）")
        if introduced:
            parts.append("新增关键词组：" + "、".join(KEYWORD_LABELS.get(g, g) for g in sorted(introduced)))
        if removed_groups:
            parts.append("移除关键词组：" + "、".join(KEYWORD_LABELS.get(g, g) for g in sorted(removed_groups)))
        if ratio >= 0.08:
            parts.append(f"编辑幅度 {ratio:.3f} ≥ 0.08")
        return ClassifierResult(
            severity=Severity.GENERAL.value,
            keywords=keywords,
            industries=industries,
            reason="一般变更：" + "；".join(parts),
            edit_ratio=ratio,
            number_delta=number_delta,
        )

    return ClassifierResult(
        severity=Severity.EDITORIAL.value,
        keywords=keywords,
        industries=industries,
        reason=f"编辑性变更：仅措辞/标点差异，编辑幅度 {ratio:.3f} < 0.08 且无数值变化",
        edit_ratio=ratio,
        number_delta=False,
    )
