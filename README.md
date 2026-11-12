# lawdelta · 法规标准更新采集与条款变更比对台

安衡合规咨询 · 法规监测组的内部工作台：每周从三个公开来源采集法规新版本，按「第X条」切分并对齐，
把**条款编号重排**的噪声压掉，只留下真正改动的条款，再给出**重大 / 一般 / 编辑性**三级判断，
最后由分析师确认影响行业、合规总监发布客户可见的变更说明。

## 真实场景

- **客户**：安衡合规咨询 · 法规监测组（6 人），为 40 家制造 / 医疗 / 制药客户维护合规台账。
- **现在的做法**：每周人工打开 3 个来源（国家标准全文公开系统、市场监管总局规章库、地方生态环境厅文件），
  把新条文复制到 Word，和上一版肉眼比对，再手写变更说明。
- **三个痛点**：① 条款编号重排后整篇 diff 全是噪声；② 无法快速判断「哪一条变了、影响哪个客户」；
  ③ 变更说明靠人写，漏项。
- **上下游**：上游 = 3 个公开来源网页/PDF → 本系统替代「人工复制 + Word 比对 + 手写说明」 →
  下游 = 客户合规台账与内部培训材料。
- **角色**：

| 角色 | 账号 | 主要页面 | 权限 | 典型动作 |
|---|---|---|---|---|
| `admin` 合规总监 | `admin@lawdelta.io` | 全部 5 页 | 来源配置、发起比对、确认、**发布**、查看审计 | 发布客户可见的变更说明 |
| `analyst` 法规分析师 | `analyst@lawdelta.io` | 时间线 / 比对结果 / 确认 | 采集新版本、发起比对、确认变更并标注影响行业 | 每周跑采集与比对 |
| `viewer` 客户只读 | `viewer@lawdelta.io` | 已发布变更说明 | 只读已发布内容（写接口一律 403） | 查看台账变更 |

统一的演示密码：`Demo@2026`。

## 一天的工作剧本（seed 数据与剧本一致）

1. 08:40 分析师打开「文档版本时间线」，看到 `SRC-STD` 来源上次巡检 2026-11-10 06:30。
2. 08:41 点「采集新版本」→ 从 `GB 30871-2022` 拉到 **v3**（11 条，状态「待比对」）。
3. 08:42 选左 v2 / 右 v3 发起比对 → worker 切分对齐，得到 **9 条变更：3 重大 / 4 一般 / 2 编辑性**，
   同时报告「编号重排 8 条 · 0 误报」。
4. 08:50 分析师确认 2 条（1 条重大 + 1 条一般），标注影响行业「制造 / 环保」并写台账动作。
5. 09:00 合规总监在「变更确认与影响标注」页发布会话 → 客户视图出现 2 条发布说明。
6. 09:02 导出 Markdown 变更说明与 CSV 清单，发给客户成功团队。
7. 15:00 客户（viewer）登录只看「已发布变更说明」，看不到未发布批次，也点不动任何写按钮（接口 403）。
8. 次日 seed 内置的 `HJ 1200-2021 v3→v4` 批次继续复用同一套算法与判级口径。

## 核心算法（全部 Python 真算，落库可复现）

### 1. 条款切分与对齐（`backend/src/services/clause_splitter.py` + `clause_aligner.py`）

- **切分**：正则 `第[一二三…N]条` 定位条头，条间正文即条文；`（一）` / `1.` 识别为款；
  空条文 / 无条头 / 条号无法解析 → `unparsed` 计数，不进入发布。
- **对齐**：先对归一文本（去空白、统一标点）做**完全相等配对**（相似度 1.0）——
  编号只用于展示，不参与判等，所以**条款编号重排不会产生任何变更项**；
  其余候选按 `0.7 × TF-IDF 余弦 + 0.3 × SimHash 汉明距相似度` 建矩阵，贪心取最高分配对
  （条号相同仅 +0.02 破平权重）；未配对 → 新增 / 删除；配对但正文不同 → 修改。
- **阈值**：`match_threshold=0.55`（低于此不配对）、`change_threshold=0.86`
  （相似度 <0.86 记「实质修改」，0.86–1 记「措辞修改」，两者都算变更项，避免编辑性变更被静默吞掉）。
- **可复现**：无随机数、无外部模型；`TF-IDF` 用字符二元组 + 数字整词，容器 / 本地逐位一致。

### 2. 变更分类与影响等级（`backend/src/services/change_classifier.py`）

- **关键词词典**（7 组）：强制性义务 / 罚则 / 期限 / 资质准入 / 废止 / 适用范围 / 记录留档；
  行业词典（制造 / 医疗 / 环保）。
- **修改幅度**：`edit_ratio = 1 − SequenceMatcher(归一旧文本, 归一新文本).ratio()`；
  另算「数字签名变化」（19.5%→21%、一年→两年、3 天→5 天）。
- **判决**：新增/删除含 罚则 或 资质准入 → `重大`；修改后新引入 罚则/资质准入/废止 → `重大`；
  否则 `edit_ratio ≥ 0.08` 或数字变化或任一组关键词增减 → `一般`；只剩措辞/标点 → `编辑性`。
- **失败态**：空条文 / 解析失败 → `unparsed` 并计入 `severity_counts`。
- **输出落库**：`change_items.severity / keywords / industries / reason / similarity / edit_ratio`，
  前端只展示接口回传的数值（无前端硬编码 / 假图）。

## 功能模块（除登录外 3 个可串链路的模块）

1. **采集**：来源清单与巡检配置 → `POST /api/sources/{id}/crawl` 落新版本（幂等，重复采集 409）。
2. **比对**：`POST /api/diffs` 建批次 → Celery worker 执行 → `GET /api/diffs/{id}` 轮询统计与变更列表。
3. **确认与发布**：`POST /api/changes/{id}/confirm`（确认 + 影响行业）→ `POST /api/diffs/{id}/publish`
   → `GET /api/public/changes` 客户视图 → 导出 MD/CSV。
   发布不变量：① 现行版本只向前推进——目标版本高于现行才切换，旧批次发布仅补历史说明、不回退现行；
   ② 同一批次重复发布幂等（不新增/不重复变更，返回 409）；③ 并发发布由「每法规至多一个现行版本」
   部分唯一索引 + 按法规的事务级锁兜底，不会出现两个现行版本；④ 客户列表按版本递进排序，
   与导出同源标注同一现行版本（已发布批次的导出只含已发布变更）。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite + Pinia + Vue Router + Axios（自绘 SVG/排版，无图表 CDN） |
| 后端 | Python 3.11 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 + PyJWT |
| 算法 | 纯标准库：TF-IDF、SimHash、difflib 序列相似度（无 numpy / 无外部分词器） |
| 异步 | Celery 5 + Redis（worker 消费 `lawdelta.run_diff`，beat 写心跳与来源巡检） |
| 数据库 | PostgreSQL 16（`lawdelta` schema，9 张表） |
| 容器 | 5 服务：frontend(Nginx) / backend(uvicorn) / worker(Celery) / db / redis，全部 healthcheck |
| 视觉 | 铅字印刷 · 法典装订：米白纸 / 深棕墨 / 朱红印章；Noto Serif SC + Source Sans 3；`oklch()` 色板 |

## 快速启动

```bash
cp .env.example .env
docker compose up -d --build
# 等 5/5 healthy 后（约 40-90s）
docker compose exec backend python -m scripts.seed_demo   # 幂等，可重复执行
open http://localhost:18241
```

- 前端：<http://localhost:18241>
- 后端直连：<http://localhost:19241/api/health>
- 数据库映射：`localhost:17741`（PG16，库/用户 `lawdelta`）

首次启动 `SEED_DEMO=true` 时 backend 会在启动阶段自动执行一次 seed（失败只记 WARNING 不阻塞）。
seed 结束时打印一行：

```
SEED_SUMMARY brand=lawdelta sources=3 documents=2 versions=6 diffruns=2 changes=9 users=3
```

重复执行只打印 `SEED_SKIPPED`，这一行逐字一致（幂等校验口径）。

## 目录

```
gb-568/
├── docker-compose.yml            # 5 服务 + 命名卷 + healthcheck
├── .env / .env.example
├── backend/
│   ├── Dockerfile  requirements.txt  alembic.ini  entrypoint.sh
│   ├── migrations/               # Alembic 初始迁移（容器内用 scripts/bootstrap_db.py 建表）
│   ├── scripts/
│   │   ├── seed_demo.py          # 幂等 seed（自然键 upsert）
│   │   ├── fixtures.py           # 条款 fixture（A/B 两部法规的版本正文）
│   │   └── bootstrap_db.py       # metadata.create_all 建表
│   └── src/
│       ├── config/               # settings / database / app / celery_app
│       ├── constants/            # roles / enums / error_codes / limits / log_templates
│       ├── models/               # user / source / document / diff_run / change_item / audit_log
│       ├── schemas/              # auth / domain / common（Pydantic）
│       ├── services/             # 算法 + 业务编排（crawl/diff/change/export/audit/...）
│       ├── controllers/          # 薄控制器（参数 → service → dict）
│       ├── routes/               # FastAPI 路由（/api/*）
│       ├── middlewares/          # auth / rbac / rate_limit / audit_logger / error_handler
│       └── utils/                # jwt / password / textutils / redis / logger / errors
├── worker/                       # Celery：run_diff / source_sweep / heartbeat + healthcheck.sh
└── frontend/
    └── src/{api,stores,types,components/common,hooks,pages,router,utils,constants,styles}
```

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `COMPOSE_PROJECT_NAME` | `lawdelta` | 容器名前缀 |
| `FRONTEND_PORT` | `18241` | Nginx 端口 |
| `BACKEND_PORT` | `19241` | uvicorn 端口 |
| `DB_PORT` | `17741` | PostgreSQL 宿主映射 |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | `lawdelta` … | 数据库 |
| `JWT_SECRET` | dev 值 | JWT 签名密钥（生产必须替换） |
| `REDIS_URL` | `redis://redis:6379/0` | Celery broker + 限流窗口 |
| `SEED_DEMO` | `true` | 启动时是否自动 seed |
| `RATE_LIMIT_DIFF_PER_MINUTE` / `RATE_LIMIT_CRAWL_PER_MINUTE` | `12` / `8` | 限流桶 |

## 共享枚举出现位置

`ChangeType`（added/removed/modified）与 `Severity`（major/general/editorial/unparsed）：

- 后端定义：`backend/src/constants/enums.py`
- 后端使用：`services/change_classifier.py`、`services/diff_service.py`、`services/export_service.py`
- 前端定义：`frontend/src/constants/enums.ts`
- 前端使用：`pages/DiffResultPage.vue`、`pages/ChangeReviewPage.vue`、`pages/PublishedPage.vue`、
  `components/common/SeverityTag.vue`、`components/common/ClauseDiffCard.vue`

同组还有：`DiffRunStatus`、`DocumentStatus`、`Industry`、`SourceKind`（同上两处成对定义）。

## 接口一览（统一 `/api` 前缀，JWT Bearer）

| 方法 | 路径 | 权限 |
|---|---|---|
| POST | `/api/auth/login` | 公开 |
| GET | `/api/auth/me` | 任意登录角色 |
| GET | `/api/sources` / `/api/documents` / `/api/documents/{id}` | 任意登录角色 |
| PATCH | `/api/sources/{id}` | admin |
| POST | `/api/sources/{id}/crawl` | admin / analyst |
| POST | `/api/diffs` | admin / analyst |
| GET | `/api/diffs` / `/api/diffs/{id}` / `/api/diffs/{id}/changes` | 任意登录角色 |
| GET | `/api/changes/pending` | 任意登录角色 |
| POST | `/api/changes/{id}/confirm` | admin / analyst |
| POST | `/api/diffs/{id}/publish` | **仅 admin** |
| GET | `/api/public/changes` | 任意登录角色（客户视图） |
| GET | `/api/diffs/{id}/export?format=md|csv` | admin / analyst |
| GET | `/api/audit` | admin |

## 本地开发

```bash
# 后端（需本机 PG16 + Redis）
cd backend && pip install -r requirements.txt
uvicorn src.main:app --reload --port 19241
# worker
cd backend && celery -A src.config.celery_app worker -l info   # 或直接跑 docker compose 的 worker
# 前端
cd frontend && npm install && npm run dev                     # http://localhost:18241
```

## 测试

测试脚本、截图与 `TESTING.md` 在 `batch-20261112/test-artifacts/gb-568/`（源码目录不放测试产物）。

## License

MIT（演示项目，法规文本为虚构改写，仅用于工程演示，不作为合规依据）。
