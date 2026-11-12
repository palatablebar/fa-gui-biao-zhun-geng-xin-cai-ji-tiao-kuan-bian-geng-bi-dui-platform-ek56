"""演示用法规条款 fixture（离线、确定性，不含任何外部抓取）。

两部法规：
  A《GB 30871-2022 危险化学品企业特殊作业安全规范》—— 来源：国家标准全文公开系统
     v1 首发（11 条）→ v2 **条款编号重排版**（正文逐字相同，仅顺序/条号变化）
     → 主流程中采集 v3（9 处实质变更，3 重大 / 4 一般 / 2 编辑性）
  B《HJ 1200-2021 排污单位自行监测技术指南 制药工业》—— 来源：地方生态环境厅文件
     v1 8 条 → v2 9 条 → v3 11 条 → v4 11 条（9 处变更，3 重大 / 4 一般 / 2 编辑性）

设计意图：A 的 v1→v2 只做编号重排（0 变更），用来证明「编号重排不产生噪声」；
A 的 v2→v3 与 B 的 v3→v4 使用同一套变更模式，便于用同一算法复现同一分级结果。
"""
from __future__ import annotations

from datetime import date

from src.services.clause_splitter import int_to_chinese

DEMO_PASSWORD = "Demo@2026"
DEMO_DOMAIN = "lawdelta.io"

DEMO_USERS: list[tuple[str, str, str]] = [
    (f"admin@{DEMO_DOMAIN}", "陈立衡 · 合规总监", "admin"),
    (f"analyst@{DEMO_DOMAIN}", "宋知微 · 法规分析师", "analyst"),
    (f"viewer@{DEMO_DOMAIN}", "客户合规台账（只读）", "viewer"),
]

DEMO_SOURCES: list[dict] = [
    {
        "code": "SRC-STD",
        "name": "国家标准全文公开系统",
        "kind": "national_standard",
        "base_url": "https://openstd.samr.gov.cn/bzgk/gb/",
        "fetch_cycle": "每周一 06:30",
        "owner_note": "强制国标（GB）全文，按发布日期巡检；PDF 转文本后切条。",
        "enabled": True,
        "next_issue_hint": date(2026, 11, 10),
    },
    {
        "code": "SRC-SAMR",
        "name": "市场监管总局规章库",
        "kind": "regulatory",
        "base_url": "https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/",
        "fetch_cycle": "每周三 07:00",
        "owner_note": "部门规章与规范性文件；本季暂无可入台账的新规章（空状态）。",
        "enabled": True,
        "next_issue_hint": None,
    },
    {
        "code": "SRC-ENV",
        "name": "地方生态环境厅文件",
        "kind": "local_env",
        "base_url": "https://sthjt.example.gov.cn/xxgk/",
        "fetch_cycle": "每周五 08:00",
        "owner_note": "地方排放标准与监测指南；制药、化工行业为主。",
        "enabled": True,
        "next_issue_hint": date(2026, 10, 28),
    },
]


def render_document(bodies: list[str]) -> str:
    """把条款正文列表渲染为「第X条 …」的法规全文。"""
    blocks = [f"第{int_to_chinese(index + 1)}条 {body}" for index, body in enumerate(bodies)]
    return "\n\n".join(blocks)


# --------------------------------------------------------------- 文档 A ----
# GB 30871-2022 原始条文（v1 顺序）
A_BASE: list[str] = [
    "本规范规定了危险化学品企业特殊作业的安全要求，适用于生产、储存、使用危险化学品的企业。",
    "企业应当建立特殊作业安全管理制度，明确作业审批流程与各级责任人。",
    "动火作业前，企业应当办理动火安全作业票，并经安全管理部门审批。",
    "动火安全作业票的有效期不超过3天，一张作业票只能用于一处动火作业。",
    "受限空间作业应当进行氧含量检测，氧含量应为19.5%～23.5%。",
    "作业前应当对参加作业的人员进行安全交底，交底记录应当留存一年。",
    "临时用电作业应当由持证电工实施，并办理临时用电安全作业票。",
    "动火作业现场应当配置灭火器材，作业完毕后应当清理现场并确认无残留火种。",
    "企业应当每半年组织一次特殊作业专项检查，检查结果纳入年度安全考核；未按期检查的，责令限期整改并予以通报。",
    "高处作业是指在坠落高度基准面2米以上（含2米）有可能坠落的高处进行的作业。",
    "本规范自2022年10月1日起实施，原GB 30871-2014同时废止。",
]

# v1：原始顺序
A_V1_BODIES: list[str] = list(A_BASE)

# v2：编号重排版。正文逐字不变，仅调整顺序 → 条号整体重排。
# 顺序映射（旧序号 → 新序号）：2→1, 3→2, 1→3, 5→4, 4→5, 6→6, 7→7, 8→8, 11→9, 9→10, 10→11
A_V2_BODIES: list[str] = [
    A_BASE[1], A_BASE[2], A_BASE[0], A_BASE[4], A_BASE[3],
    A_BASE[5], A_BASE[6], A_BASE[7], A_BASE[10], A_BASE[8], A_BASE[9],
]

# v3：主流程采集的新版本。基于 v2 的 11 条：
#   修改 7（T3 重大 / T5 一般 / T4 一般 / T7 编辑性 / T6 一般 / T8 一般 / T10 编辑性）
#   新增 1（资质准入 → 重大）、删除 1（原 v2 第十条 检查条款 → 重大）
#   未变 3（T2 / T1 / T11），并且仍保留编号重排
A_V3_MAJOR_1 = (
    "动火作业前，企业应当办理动火安全作业票，并经企业主要负责人审批；"
    "未经审批擅自动火的，责令停止作业并处以五万元罚款。"
)
A_V3_ADDED_QUALIFICATION = (
    "企业应当取得危险化学品安全生产许可证，特种作业人员应当持证上岗；"
    "未取得相应资质的，不得从事特殊作业。"
)
A_V3_BODIES: list[str] = [
    A_BASE[1],            # T2 未变（重排后 2→1）
    A_BASE[0],            # T1 未变（重排后 1→2）
    A_V3_ADDED_QUALIFICATION,  # 新增 → 重大
    A_V3_MAJOR_1,         # T3 修改 → 重大（新增罚则）
    "受限空间作业应当进行氧含量检测，氧含量应为19.5%～21%。",              # 一般（数值）
    "动火安全作业票的有效期不超过5天，一张作业票只能用于一处动火作业。",     # 一般（数值）
    A_BASE[10],           # T11 未变（重排后 11→7）
    "临时用电作业应当由持证电工实施，并办理临时用电安全作业票。".replace("应当", "应"),
    "作业前应当对参加作业的人员进行安全交底，交底记录应当留存两年。",         # 一般（数值）
    "动火作业现场应当配置灭火器材、消防沙与正压式空气呼吸器，作业完毕后应当清理现场并确认无残留火种。",  # 一般（幅度）
    "高处作业指在坠落高度基准面2米以上（含2米）有可能坠落的高处进行的作业。",  # 编辑性（删一个「是」）
]

# --------------------------------------------------------------- 文档 B ----
B_V3_BODIES: list[str] = [
    "本指南规定了制药工业排污单位自行监测的一般要求，适用于制药工业排污单位废水、废气排放的监测。",
    "排污单位应当制定自行监测方案，明确监测点位、指标、频次与责任人。",
    "废水排放口化学需氧量的监测频次为每季度1次，取样点位不少于2个。",
    "废气排放口颗粒物的监测限值为20mg/m³，超标时应当加密监测。",
    "排污单位应当于每年3月31日前报送上一年度自行监测年度报告。",
    "在线监测设备应当每季度校准一次，校准记录应当留存三年。",
    "监测数据出现异常时，排污单位应当及时排查并在3日内报告所在地生态环境主管部门。",
    "排污单位应当按照排污许可证要求开展自行监测，并在厂区显著位置公开监测信息。",
    "自行监测方案发生重大变更的，排污单位应当在变更后10个工作日内重新备案并书面说明原因。",
    "排污单位应当委托具备相应资质的检验检测机构开展监测，并对监测数据的真实性负责。",
    "本指南自2021年9月1日起实施。",
]

B_V4_BODIES: list[str] = [
    B_V3_BODIES[0],
    B_V3_BODIES[1],
    "废水排放口化学需氧量的监测频次为每季度2次，取样点位不少于3个。",          # 一般（数值）
    "废气排放口颗粒物的监测限值为10mg/m³，超标时应当加密监测。",              # 一般（数值）
    "排污单位应当于每年4月30日前报送上一年度自行监测年度报告。",              # 一般（数值）
    "在线监测设备应每季度校准一次，校准记录应当留存三年。",                    # 编辑性（应当→应）
    "监测数据出现异常时，排污单位应当及时排查并在3日内报告生态环境主管部门。",          # 编辑性（删「所在地」）
    "排污单位应当按照排污许可证要求开展自行监测，保存原始监测记录不少于五年，"
    "并在厂区显著位置和单位网站公开监测信息。",                                # 一般（幅度）
    "排污单位应当委托具备相应资质的检验检测机构开展监测，并对监测数据的真实性负责；"
    "出具虚假监测数据的，责令改正并处以十万元罚款，对直接责任人依法追究责任。",  # 重大（新增罚则）
    "制药工业排污单位应当取得排污许可证，发酵类药品生产车间还应当安装在线监测设备并与生态环境主管部门联网。",
    B_V3_BODIES[10],
]
# 说明：v4 相比 v3 少一条（原第九条 方案变更备案 → 删除，含备案/资质表述 → 重大），
# 多一条（排污许可证联网 → 新增，含资质准入 → 重大）。

B_V1_BODIES: list[str] = [
    "本指南规定了制药工业排污单位自行监测的一般要求，适用于制药工业排污单位废水、废气排放的监测。",
    "排污单位应当制定自行监测方案，明确监测点位、指标与责任人。",
    "废水排放口化学需氧量的监测频次为每季度1次。",
    "废气排放口颗粒物的监测限值为20mg/m³。",
    "排污单位应当于每年3月31日前报送上一年度自行监测年度报告。",
    "排污单位应当按照排污许可证要求开展自行监测，并在厂区显著位置公开监测信息。",
    "排污单位应当委托具备相应资质的检验检测机构开展监测。",
    "本指南自2021年9月1日起实施。",
]

B_V2_BODIES: list[str] = [
    B_V1_BODIES[0],
    B_V1_BODIES[1],
    B_V1_BODIES[2],
    B_V1_BODIES[3],
    B_V1_BODIES[4],
    "在线监测设备应当每季度校准一次，校准记录应当留存三年。",
    B_V1_BODIES[5],
    B_V1_BODIES[6],
    B_V1_BODIES[7],
]

# ------------------------------------------------------- 文档元数据表 ----
DOCUMENT_SPECS: list[dict] = [
    {
        "document_key": "GB 30871-2022",
        "source_code": "SRC-STD",
        "title": "危险化学品企业特殊作业安全规范",
        "issuer": "国家市场监督管理总局 · 国家标准化管理委员会",
        "versions": [
            {"version_label": "v1", "version_no": 1, "status": "superseded",
             "issued_at": date(2022, 3, 15), "effective_at": date(2022, 10, 1),
             "bodies": A_V1_BODIES, "note": "2022 首发版"},
            {"version_label": "v2", "version_no": 2, "status": "current",
             "issued_at": date(2025, 6, 20), "effective_at": date(2025, 12, 1),
             "bodies": A_V2_BODIES, "note": "条款编号重排版（正文逐字未改）"},
        ],
    },
    {
        "document_key": "HJ 1200-2021",
        "source_code": "SRC-ENV",
        "title": "排污单位自行监测技术指南 制药工业",
        "issuer": "省生态环境厅",
        "versions": [
            {"version_label": "v1", "version_no": 1, "status": "superseded",
             "issued_at": date(2021, 9, 1), "effective_at": date(2021, 12, 1),
             "bodies": B_V1_BODIES, "note": "2021 首发版"},
            {"version_label": "v2", "version_no": 2, "status": "superseded",
             "issued_at": date(2024, 5, 10), "effective_at": date(2024, 9, 1),
             "bodies": B_V2_BODIES, "note": "补充在线监测校准要求"},
            {"version_label": "v3", "version_no": 3, "status": "superseded",
             "issued_at": date(2026, 6, 18), "effective_at": date(2026, 8, 1),
             "bodies": B_V3_BODIES, "note": "扩充至 11 条"},
            {"version_label": "v4", "version_no": 4, "status": "current",
             "issued_at": date(2026, 10, 28), "effective_at": date(2027, 1, 1),
             "bodies": B_V4_BODIES, "note": "现行版（罚则与许可要求收紧）"},
        ],
    },
]

# 待采集清单：来源 code → 尚未入库的新版本（主流程「采集」使用）
COLLECTIONS: dict[str, list[dict]] = {
    "SRC-STD": [
        {
            "document_key": "GB 30871-2022",
            "title": "危险化学品企业特殊作业安全规范",
            "issuer": "国家市场监督管理总局 · 国家标准化管理委员会",
            "version_label": "v3",
            "version_no": 3,
            "issued_at": date(2026, 11, 10),
            "effective_at": date(2027, 5, 1),
            "bodies": A_V3_BODIES,
            "note": "2026 修订版：罚则加重、许可与持证要求前移",
        }
    ],
}

# seed 内置的两条比对（一次编号重排 0 变更；一次 9 条变更）
SEED_DIFF_SPECS: list[dict] = [
    {
        "document_key": "GB 30871-2022",
        "base_version": "v1",
        "target_version": "v2",
        "requested_by": "analyst@lawdelta.io",
        "note": "编号重排版复核：期望 0 条变更",
        "confirm": [],
        "publish": False,
    },
    {
        "document_key": "HJ 1200-2021",
        "base_version": "v3",
        "target_version": "v4",
        "requested_by": "analyst@lawdelta.io",
        "note": "制药行业排放指南修订：9 条变更",
        "confirm": [
            {
                "severity": "major",
                "impact_industries": ["medical", "environmental"],
                "impact_note": "制药客户新增排污许可证与在线联网条款，台账需在 2027-01-01 前补录许可信息。",
                "publish_note": "客户台账与培训材料已同步至 v4 口径。",
            },
            {
                "severity": "general",
                "impact_industries": ["environmental"],
                "impact_note": "废水监测频次每季度 1→2 次、取样点位 2→3 个，6 家制药客户的自行监测方案需修订。",
                "publish_note": "已通知 6 家客户更新自行监测方案与取样点位布置。",
            },
        ],
        "publish": True,
    },
]
