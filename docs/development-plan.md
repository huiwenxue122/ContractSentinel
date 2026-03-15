# ContractSentinel 开发计划

基于 README.md 与 docs/architecture.md 整理，仅规划不写代码。

---

## 1. 核心功能总结

系统需要实现以下核心能力：

### 1.1 结构层（Structural Layer）

- **合同 PDF 解析**：用 Marker 做版式感知的 PDF 解析，得到结构化文本块。
- **法律实体与结构抽取**：用 LLM 从文本中抽取：
  - 定义（Definitions）
  - 条款/章节（Clauses / Sections）
  - 当事方（Parties）
  - 义务（Obligations）
  - 交叉引用（Cross-references，如 “subject to Section 4.2”）
- **法律知识图谱**：将上述要素存入 Neo4j，形成「条款–定义–引用」等关系图，支持后续跨条款推理。

### 1.2 推理层（Reasoning Layer）

- **审查手册（Review Playbook）**：可配置的规则集（如：无限责任→高风险、单方终止→高风险、保密期>5年→中风险），作为策略驱动审查的依据。
- **图增强检索（RAG + Graph）**：不仅检索单段文本，还要拉取关联的定义、被引用条款、相关义务等图上下文。
- **多智能体流水线（LangGraph）**：
  - **Scanner Agent**：按 Playbook 识别候选风险（条款 + 触发的规则 + 初步证据）。
  - **Critic Agent**：用图上下文、交叉引用、定义范围等校验 Scanner 结论是否成立，过滤不充分或错误发现。
  - **Evaluator Agent**：在「可接受 / 建议修订 / 升级人工审查」中做最终决策，考虑策略严重度、歧义、条款交互、证据置信度。
- **输出**：每条问题对应结构化结果：风险等级、触发的规则、理由、建议替代表述、升级建议、引用（章节/页码）。

### 1.3 接口层（Interface Layer）

- **结构化风险备忘录（Structured Risk Memo）**：API 返回统一 schema（含 clause、risk_level、rule_triggered、reason、fallback_language、escalation、citation 等）。
- **证据导向的审查 UI**：非聊天界面，而是审查界面：
  - 左侧：合同/条款原文；
  - 右侧：问题卡片，每张卡片展示：条款、触发的策略、推理、替代表述、升级建议及证据链。
- **人工决策**：界面支持律师查看证据后做出最终接受/修订/升级决策（可仅记录，不做强制闭环）。

### 1.4 评估（Evaluation）

- **基准数据集**：少量 NDA/MSA 合同，人工标注：风险条款、期望升级标签、可接受的替代表述、期望引用。
- **指标**：风险条款召回率、标记条款精确率、交叉引用推理成功率、引用准确率、升级决策准确率、幻觉/无依据声称率。
- **基线对比**：Chunk RAG vs Graph RAG vs 多智能体（Scanner + Critic + Evaluator），用于说明图结构与多智能体带来的提升。

---

## 2. 需要的模块

| 模块 | 职责 | 主要依赖/技术 |
|------|------|----------------|
| **parsing** | PDF → 版式文本块 | Marker |
| **extraction** | 文本 → 定义/条款/当事方/义务/交叉引用 | LLM API |
| **graph** | 存储与查询法律知识图谱；提供「按条款取关联上下文」的接口 | Neo4j（或兼容驱动） |
| **retrieval** | 基于图上下文的 RAG：为给定条款/问题检索相关片段 + 图邻域 | 向量库（可选）+ graph 模块 |
| **agents** | Scanner / Critic / Evaluator 的实现与 LangGraph 编排 | LangGraph、LLM API |
| **schemas** | 合同结构、风险备忘录、Playbook 规则、API 请求/响应等 Pydantic 模型 | Pydantic |
| **api** | 暴露「上传 PDF → 解析 → 图谱构建 → 审查 → 返回风险备忘录」等 HTTP 接口 | FastAPI |
| **evaluation** | 加载基准数据、跑审查流水线、计算指标、对比基线 | Ragas（可选）、自定义指标 |
| **frontend** | 证据导向的审查 UI：合同展示 + 风险卡片 + 证据链 | React / Next.js |
| **playbooks（数据）** | 审查手册的规则定义（可 JSON/YAML），供 agents 与配置使用 | 无 |
| **benchmark（数据）** | 标注好的 NDA/MSA 样本与标准答案 | 无 |

---

## 3. 推荐项目目录结构

在 README 已有结构上做细化与补充，便于分层开发与测试：

```
contractsentinel/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用入口
│   ├── config.py                  # 配置（API keys、Neo4j、模型等）
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── contracts.py       # 上传 PDF、触发解析与图谱构建
│   │   │   ├── review.py          # 触发审查、返回风险备忘录
│   │   │   └── health.py          # 健康检查
│   │   └── deps.py                # 公共依赖（DB、LLM client 等）
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── contract.py            # 条款、定义、交叉引用、合同根结构
│   │   ├── risk_memo.py           # 风险备忘录、citation、escalation
│   │   ├── playbook.py            # 规则、风险等级枚举
│   │   └── api_models.py          # 请求/响应 DTO
│   │
│   ├── parsing/
│   │   ├── __init__.py
│   │   ├── pdf.py                 # Marker 封装：PDF → 文本块/页
│   │   └── blocks.py              # 块类型、段落划分（若需要）
│   │
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── prompts.py             # 抽取用的 prompt 模板
│   │   ├── entities.py            # 调用 LLM 做实体/关系抽取
│   │   └── normalizer.py          # 归一化 section id、引用格式等
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── client.py              # Neo4j 连接与会话
│   │   ├── models.py              # 节点/边类型（与 schemas 对齐）
│   │   ├── ingest.py              # 将 extraction 结果写入图
│   │   └── query.py               # 按条款/节点取邻域、定义、引用链
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── graph_context.py       # 利用 graph.query 组装图上下文
│   │   ├── chunking.py            # 可选：按条款/页分块
│   │   └── rag.py                 # 检索接口：query → 文本片段 + 图上下文
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── prompts.py             # Scanner / Critic / Evaluator 的 prompt
│   │   ├── scanner.py             # Scanner Agent 逻辑
│   │   ├── critic.py              # Critic Agent 逻辑
│   │   ├── evaluator.py           # Evaluator Agent 逻辑
│   │   ├── graph.py               # LangGraph 图定义与编排
│   │   └── playbook_loader.py     # 加载 data/playbooks 规则
│   │
│   └── evaluation/
│       ├── __init__.py
│       ├── dataset.py             # 加载 benchmark 标注数据
│       ├── runner.py              # 对每条样本跑审查、收集输出
│       ├── metrics.py             # 召回率、精确率、引用/升级准确率等
│       └── baselines.py           # Chunk RAG / Graph RAG / Multi-Agent 对比
│
├── data/
│   ├── sample_contracts/          # 示例 PDF（NDA、MSA）
│  ├── playbooks/
│   │   └── default.yaml           # 默认审查规则
│   └── benchmark/
│       ├── contracts/             # 标注用合同 PDF 或 ID
│       └── annotations.jsonl      # 金标：风险条款、升级、引用等
│
├── frontend/
│   └── (Next.js 结构：页面、合同展示、风险卡片、证据链组件)
│
├── notebooks/                     # 探索性分析、抽取/图构建 demo
├── tests/
│   ├── unit/
│   │   ├── test_parsing.py
│   │   ├── test_extraction.py
│   │   ├── test_graph.py
│   │   ├── test_retrieval.py
│   │   └── test_agents.py
│   └── integration/
│       └── test_review_pipeline.py
│
├── docs/
│   ├── architecture.md
│   └── development-plan.md       # 本文档
├── pics/
├── README.md
├── .gitignore
└── requirements.txt
```

说明：

- **app/**：后端核心，按「解析 → 抽取 → 图 → 检索 → 智能体 → API」分层，便于单测与替换。
- **data/playbooks** 与 **data/benchmark**：与「策略驱动」和「可评估」直接相关，单独成目录。
- **evaluation**：独立于主流程，通过 API 或直接调 runner 跑基准与基线。

---

## 4. 开发步骤（Step-by-Step Plan）

### Phase 0：环境与骨架

1. 创建仓库目录结构（如上），并添加 `app/` 下各包的空 `__init__.py`。
2. 配置 Python 环境与 `requirements.txt`（Marker、Neo4j 驱动、LangGraph、FastAPI、LLM SDK、Pydantic 等）。
3. 在 `app/schemas` 中定义与 README/architecture 一致的核心数据结构（合同节点、风险备忘录、citation、escalation 枚举、Playbook 规则格式）。
4. 在 `app/config.py` 中集中管理配置（Neo4j URI、API keys、模型名等），支持 env 或 `.env`。

### Phase 1：结构层

5. **parsing**：用 Marker 实现 PDF → 文本块（带页码/版式信息），接口例如 `parse_pdf(path) -> List[TextBlock]`。
6. **extraction**：设计并实现 LLM 抽取流程（定义、条款、当事方、义务、交叉引用），输出与 `schemas.contract` 对齐；可先做「单合同、分块抽取再合并」。
7. **graph**：实现 Neo4j 的写入（ingest）与按条款/节点查询邻域（query），保证 extraction 输出能稳定写入图并支持「给定 clause_id 取定义与引用链」。
8. 串联：**PDF → parsing → extraction → graph.ingest**，用 `data/sample_contracts` 中 1～2 份合同做端到端验证（可用 notebook 或脚本）。

### Phase 2：推理层 — 检索与 Playbook

9. **retrieval**：实现 `graph_context`（基于 graph.query）与可选文本 RAG；对外接口如 `retrieve_context(clause_id, contract_id, query?) -> (text_snippets, graph_context)`。
10. 在 `data/playbooks` 中定义至少一份可机器读的审查手册（如 YAML：规则 id、描述、风险等级、匹配模式或关键词），并实现 `playbook_loader` 供 agents 使用。

### Phase 3：推理层 — 多智能体

11. **Scanner Agent**：输入为「条款文本 + 图上下文 + Playbook」，输出为「候选问题列表」（条款、规则、初步证据）；实现并做单测或小样本跑通。
12. **Critic Agent**：输入为 Scanner 输出 + 条款 + 图上下文，输出为「支持/不支持 + 理由」；对每条 Scanner 发现调用一次。
13. **Evaluator Agent**：输入为 Critic 结果 + 策略严重度等，输出为 Acceptable / Suggest Revision / Escalate for Human Review，以及可选 fallback_language。
14. 用 **LangGraph** 编排：合同/条款列表 → 对每条条款（或先检索得到的候选）→ Scanner → Critic → Evaluator → 聚合为 Structured Risk Memo；输出格式严格对齐 `schemas.risk_memo`。

### Phase 4：接口层 — API

15. **FastAPI**：实现 `api/routes/contracts.py`（上传 PDF、触发解析与图谱构建、返回 contract_id 或解析状态）。
16. 实现 `api/routes/review.py`（传入 contract_id，触发审查流水线，返回 Structured Risk Memo JSON）。
17. 统一错误码与日志；添加简单健康检查（如 `api/routes/health.py`），确保 Neo4j 与 LLM 可用性可测。

### Phase 5：接口层 — 前端

18. 初始化 Next.js 前端，实现基础布局：左侧合同/条款展示，右侧留空用于卡片。
19. 实现「风险卡片」组件：展示 clause、rule_triggered、reason、fallback_language、escalation、citation；支持展开证据链（引用到的条款/定义）。
20. 对接后端：上传 PDF → 轮询或 WebSocket 取状态 → 请求审查 → 展示风险备忘录为卡片列表；左侧根据 citation 高亮或定位条款。

### Phase 6：评估与基线

21. 在 `data/benchmark` 中准备少量标注数据（至少 2～3 份 NDA/MSA，含风险条款、期望升级、期望引用）。
22. 实现 `evaluation/dataset` 加载与 `evaluation/runner`（调用审查流水线或 API，收集每条样本的输出）。
23. 实现 `evaluation/metrics`：风险条款召回、标记精确率、引用准确率、升级准确率、简单幻觉检测（如无引用支撑的声称）。
24. 实现 Chunk RAG 与 Graph RAG（或仅多智能体）两种基线，在相同 benchmark 上跑通并记录结果，写入 `evaluation/baselines` 或 notebook 中便于对比。

### Phase 7：收尾与文档

25. 补充单元测试（parsing、extraction、graph、retrieval、agents 的关键路径）与至少一条集成测试（PDF → 审查 → 风险备忘录）。
26. 更新 README：如何安装、配置环境变量、运行后端/前端、运行评估；在 docs 中简要说明各模块职责与数据流（可引用本文档）。
27. 可选：Docker Compose 编排 Neo4j + 后端，便于一键本地演示。

---

## 5. 依赖关系简图

- **parsing** 不依赖其他 app 模块。
- **extraction** 依赖 parsing 输出与 schemas。
- **graph** 依赖 schemas；ingest 依赖 extraction 输出。
- **retrieval** 依赖 graph 与 schemas。
- **agents** 依赖 retrieval、schemas、playbook 配置。
- **api** 依赖 parsing、extraction、graph、agents、schemas。
- **evaluation** 依赖 api 或直接调 agents + retrieval + graph，以及 data/benchmark。
- **frontend** 仅依赖 api 的 HTTP 接口。

按上述顺序实现，可最大程度减少返工并保持每步可验证。
