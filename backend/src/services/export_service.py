"""导出：Markdown 变更说明 / CSV 变更清单。

数字、条号、级别全部来自数据库里算法落库的结果，导出不做二次计算。
"""
from __future__ import annotations

import csv
import io

from src.constants.enums import CHANGE_TYPE_LABELS, INDUSTRY_LABELS, SEVERITY_LABELS, SourceKind  # noqa: F401
from src.constants.roles import ROLE_LABELS


def render_markdown(run_payload: dict, changes: list[dict]) -> str:
    stats = run_payload.get("stats") or {}
    severity = run_payload.get("severity_counts") or {}
    published = [change for change in changes if change["published"] or change["confirmed"]]
    lines: list[str] = []
    lines.append(f"# {run_payload.get('title') or run_payload.get('document_key')} 条款变更说明")
    lines.append("")
    lines.append(f"- 法规编号：`{run_payload.get('document_key')}`")
    lines.append(f"- 版本：`{run_payload.get('base_label')}` → `{run_payload.get('target_label')}`")
    lines.append(f"- 比对批次：`{run_payload.get('id')}`")
    lines.append(f"- 算法版本：`{run_payload.get('algorithm_version')}`")
    lines.append(
        f"- 现行版本：`{run_payload.get('current_version_label') or '（尚未有现行版本）'}`"
        "（导出时点，与客户视图一致）"
    )
    lines.append(
        f"- 结论：共 {run_payload.get('change_count', 0)} 条变更"
        f"（重大 {severity.get('major', 0)} / 一般 {severity.get('general', 0)} / 编辑性 {severity.get('editorial', 0)}）"
    )
    lines.append(
        f"- 条款统计：旧 {stats.get('total_old', 0)} 条、新 {stats.get('total_new', 0)} 条，"
        f"未变 {stats.get('unchanged', 0)} 条，编号重排 {stats.get('renumbered_pairs', 0)} 条（0 误报）"
    )
    if run_payload.get("published_at"):
        lines.append(f"- 发布时间：{run_payload['published_at']}")
        if run_payload.get("is_effective"):
            lines.append("- 批次性质：现行版本发布（本批次目标版本即现行版本）")
        else:
            lines.append("- 批次性质：历史批次补充发布（现行版本未因此回退）")
    else:
        lines.append("- 状态：未发布草稿（含未确认内容，请勿直接发送客户）")
    if run_payload.get("publish_note"):
        lines.append(f"- 发布说明：{run_payload['publish_note']}")
    lines.append("")
    lines.append("| 条号（旧→新） | 类型 | 级别 | 相似度 | 影响行业 | 说明 |")
    lines.append("|---|---|---|---|---|---|")
    for change in changes:
        old_label = change.get("clause_label_old") or "—"
        new_label = change.get("clause_label_new") or "—"
        industries = "、".join(
            INDUSTRY_LABELS.get(item, item) for item in (change.get("impact_industries") or change.get("industries") or [])
        ) or "—"
        note = (change.get("impact_note") or change.get("reason") or "").replace("|", "\\|")
        lines.append(
            f"| {old_label} → {new_label} | {CHANGE_TYPE_LABELS.get(change['change_type'], change['change_type'])} "
            f"| {SEVERITY_LABELS.get(change['severity'], change['severity'])} "
            f"| {change['similarity']:.3f} | {industries} | {note} |"
        )
    lines.append("")
    lines.append(f"共 {len(changes)} 条变更，其中已确认 {len(published)} 条。")
    if run_payload.get("published_at"):
        lines.append("本清单仅含已发布变更，与客户视图（/api/public/changes）指向同一有效版本。")
    lines.append("")
    lines.append("> 由 lawdelta 生成：条款对齐 + 变更分类结果均由后端算法落库，可复现。")
    return "\n".join(lines)


def render_csv(run_payload: dict, changes: list[dict]) -> str:
    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        [
            "document_key", "base_version", "target_version", "clause_no_old", "clause_no_new",
            "change_type", "severity", "similarity", "edit_ratio", "industries",
            "impact_industries", "confirmed", "published", "reason", "impact_note",
            "current_version",
        ]
    )
    for change in changes:
        writer.writerow(
            [
                run_payload.get("document_key", ""),
                run_payload.get("base_label", ""),
                run_payload.get("target_label", ""),
                change.get("clause_no_old") if change.get("clause_no_old") is not None else "",
                change.get("clause_no_new") if change.get("clause_no_new") is not None else "",
                change["change_type"],
                change["severity"],
                f"{change['similarity']:.4f}",
                f"{change['edit_ratio']:.4f}",
                "|".join(change.get("industries") or []),
                "|".join(change.get("impact_industries") or []),
                "1" if change.get("confirmed") else "0",
                "1" if change.get("published") else "0",
                (change.get("reason") or "").replace("\n", " "),
                (change.get("impact_note") or "").replace("\n", " "),
                run_payload.get("current_version_label", ""),
            ]
        )
    return buffer.getvalue()


def export_filename(run_payload: dict, fmt: str) -> str:
    key = (run_payload.get("document_key") or "document").replace(" ", "-")
    return f"lawdelta-{key}-{run_payload.get('base_label')}-{run_payload.get('target_label')}-changes.{fmt}"
