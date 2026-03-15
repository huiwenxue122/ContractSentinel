# 面试演示用 MVP 范围

目标：**一周内跑通一个最小可演示版本**，让面试官看到「合同 PDF → 结构层（解析 + 抽取 + **Neo4j 知识图谱**）→ 策略驱动的风险审查 → 结构化风险备忘录 + 简单 UI」，同时你能讲清完整架构（多智能体编排是下一步）。

---

## 一、面试时要展示的核心故事（1 分钟版）

1. **上传一份合同 PDF** → 经 **Marker 解析 + LLM 抽取** 得到法律实体与关系，写入 **Neo4j 知识图谱**（与架构图一致）。  
2. **按审查手册（Playbook）做风险扫描** → 识别无限责任、单方终止等条款；审查时可从图中取「条款邻域 / 定义 / 引用」作为上下文。  
3. **输出结构化风险备忘录** → 每条：条款、风险等级、触发的规则、理由、建议修订、是否升级人工。  
4. **在简单审查 UI 里看到结果** → 左侧合同/条款，右侧风险卡片，能对应上。

面试时可以说：*「结构层已经做到 Neo4j 知识图谱；推理层目前用 1～2 次 LLM 做审查，完整版会用 LangGraph 做 Scanner → Critic → Evaluator 三阶段编排。」*

---

## 二、MVP 必须要做的功能（必做）

| # | 功能 | 说明 | 对应任务精简版 |
|---|------|------|----------------|
| 1 | **项目骨架 + 数据模型** | 能跑起来的 FastAPI、schemas（合同条款、风险备忘录、Playbook、API 入参出参） | 任务 1 + 任务 2 |
| 2 | **PDF → 文本（结构层）** | 合同 PDF → 版式感知或纯文本。**优先 PyMuPDF/pdfplumber** 快速跑通；若时间充裕可接 **Marker**，与架构图一致 | 任务 3：`app/parsing/pdf.py` |
| 3 | **LLM 抽取 → 法律实体与关系** | 一次 LLM 调用：从全文抽出条款、定义、当事方、义务、交叉引用；输出与 schemas 对齐 | 任务 4：`app/extraction/`，输出供图写入 |
| 4 | **Neo4j 知识图谱** | 将抽取结果写入 Neo4j：节点（Clause、Definition、Party、Obligation）、边（REFERENCES、DEFINES 等）；提供**最小图查询**：按 clause_id/contract_id 取邻域（相关条款、定义、引用）供审查使用 | 任务 5：`app/graph/client.py`、`ingest.py`、`query.py` |
| 5 | **审查手册** | 一个 YAML：2～3 条规则（如无限责任 → High、单方终止 → High） | 任务 7：`data/playbooks/default.yaml` + loader |
| 6 | **「审查」逻辑（最小闭环）** | 输入：合同条款 + **图上下文（从 Neo4j 按条款取的邻域）** + Playbook。输出：**Structured Risk Memo**。用 1～2 次 LLM（Scanner + 一次校验/决策），**不用 LangGraph** | 任务 9～12 极简版；审查时调用 `graph.query` 取上下文 |
| 7 | **后端 API** | ① 上传 PDF（或「用样本」）→ 解析 + 抽取 + **写入 Neo4j** + 内存缓存 contract_id；② 传入 contract_id → 审查（读图上下文）→ 返回 Risk Memo | 任务 13～16 |
| 8 | **前端最小界面** | 一页：上传/样本 → 审查 → 左侧合同、右侧风险卡片 | 任务 17～19 |
| 9 | **一份样本合同** | `data/sample_contracts/` 下放一份 NDA PDF，演示稳定 | 同上 |

总结：**必做 = 骨架 + PDF 解析 + LLM 抽取 → Neo4j 知识图谱 + 最小图查询 + Playbook + 1～2 次 LLM 审查（带图上下文）→ Risk Memo + FastAPI + 单页前端 + 样本 PDF**。

---

## 三、MVP 可以不做或极简化的部分（先砍掉）

| 模块 | 建议 | 面试时怎么说 |
|------|------|--------------|
| **Marker** | 可选。先用 PyMuPDF/pdfplumber 保证一周内跑通；若 Day 1～2 顺利可再接 Marker，与架构图「Marker Parsing」一致 | 「当前用 PyMuPDF 抽文本；架构里是 Marker 做版式感知解析，可按需替换。」 |
| **LangGraph** | 不做。审查用 1～2 次顺序 LLM 调用，输出同一 Risk Memo schema | 「完整设计是 LangGraph 编排 Scanner → Critic → Evaluator，MVP 用顺序调用验证输出和产品逻辑。」 |
| **Critic / Evaluator 拆开** | 可合并成一次 LLM：输入 Scanner 候选 + 条款 + 图上下文，输出「是否成立 + escalation + fallback」 | 「架构里 Critic 校验、Evaluator 做升级决策；MVP 合并成一步。」 |
| **复杂图检索 / 向量 RAG** | 不做。只做「按 clause 取邻域」的简单 Cypher 查询，把邻域文本拼进 prompt 即可 | 「MVP 里用图的邻域查询给审查提供上下文；完整版会做更丰富的图检索和 RAG。」 |
| **评估 / Ragas / 基线** | 不做 | 「评估指标和基线对比在开发计划里，后续实现。」 |
| **单元测试 / 集成测试** | 可选 | 不强调也没问题 |

---

## 四、MVP 最小任务列表（按实现顺序）

含 **Structural Layer 到 Neo4j 知识图谱**，便于按顺序实现。

1. **骨架**：`app/` 包结构、`config.py`（`OPENAI_API_KEY`、`NEO4J_URI` 等）、`requirements.txt`（FastAPI、PyMuPDF 或 pdfplumber、openai、neo4j、pydantic、python-multipart）、`app/main.py` 空 app。
2. **Schemas**：`app/schemas/` 下定义：`Clause`、`Definition`、`CrossReference`、`Contract`（条款 + 定义 + 引用 + 原始文本）、`RiskMemoItem`、`StructuredRiskMemo`、Playbook 的 `Rule`、枚举 `RiskLevel` / `Escalation`。
3. **PDF 解析**：`app/parsing/pdf.py`，PyMuPDF 或 pdfplumber，`parse_pdf(path_or_bytes) -> str` 或 `List[{text, page}]`。
4. **LLM 抽取**：`app/extraction/entities.py` + prompt：输入全文，输出 JSON（条款、定义、当事方、义务、交叉引用）；转成与 schemas 一致的结构，供图写入。
5. **Neo4j 图**：`app/graph/client.py`（连接）、`ingest.py`（把抽取结果写入图：节点 Clause/Definition/Party/Obligation，边 REFERENCES、DEFINES 等）、`query.py`（按 contract_id/clause_id 取邻域，返回相关条款/定义/引用的文本，供审查 prompt 使用）。
6. **Playbook**：`data/playbooks/default.yaml`（2～3 条规则），loader 返回 `List[Rule]`。
7. **审查**：`app/agents/review.py`：输入 contract_id（或内存中的 Contract + 图 client），对每条条款（或先 Scanner 筛出的条款）用 `graph.query` 取图上下文，再 1～2 次 LLM 产出 `StructuredRiskMemo`。
8. **API**：POST 上传 PDF（或「用样本」）→ 解析 + 抽取 + **写入 Neo4j** + 记录 contract_id；POST review(contract_id) → 从图取上下文 + 审查 → 返回 Risk Memo。
9. **前端**：单页：上传/样本 → 审查 → 左侧合同、右侧风险卡片。
10. **样本 + README**：`data/sample_contracts/` 一份 NDA；README 增加 Quick Start（含 Neo4j 启动方式、环境变量）、说明 MVP 已包含结构层到 Neo4j 知识图谱。

---

## 五、建议的一周时间分配（5 个工作日）

含 **Structural Layer → Neo4j**，按天拆解。

| 天 | 目标 | 产出 |
|----|------|------|
| Day 1 | 骨架 + Schemas + PDF 解析 + LLM 抽取（PDF → 法律实体与关系）；本地跑通抽取输出 | 任务 1、2、3、4 |
| Day 2 | Neo4j：client + ingest + query（写入图谱 + 按条款取邻域）；Playbook；审查逻辑（Contract + **图上下文** + Playbook → StructuredRiskMemo） | 任务 5、6、7 |
| Day 3 | FastAPI：上传 → 解析 + 抽取 + **写入 Neo4j**；review(contract_id) → 图上下文 + 审查 → Risk Memo；Postman/curl 验证 | 任务 8 |
| Day 4 | 前端单页：上传/样本 + 审查 + 风险卡片 | 任务 9 |
| Day 5 | 样本 PDF 端到端跑通、README Quick Start（含 Neo4j）、演示话术与追问准备 | 任务 10 + 演练 |

若 Day 1 提前完成，可把 PDF 解析换成 Marker，与架构图「Marker Parsing」完全一致。

---

## 六、面试时可能被问到、如何答（简表）

| 问题 | 建议回答要点 |
|------|--------------|
| 为什么用图？ | 合同不是线性的，条款间有定义和引用关系；用图可以按 clause 取邻域，做跨条款推理。**MVP 里已经接入 Neo4j**，解析后写入图谱，审查时用图上下文增强 prompt。 |
| 结构层具体做了什么？ | 合同 PDF 经解析（PyMuPDF/Marker）→ LLM 抽取法律实体与关系 → 写入 Neo4j（Clause、Definition、Party、Obligation 及 REFERENCES、DEFINES 等边），和架构图一致。 |
| Scanner/Critic/Evaluator 分别做什么？ | Scanner 按 Playbook 找候选风险；Critic 用图上下文校验是否成立；Evaluator 做升级决策和 fallback。MVP 里用 1～2 次 LLM 合并实现同一输出格式，下一步用 LangGraph 拆成三阶段。 |
| 如何评估效果？ | 设计了 benchmark（风险条款召回、精确率、引用与升级准确率）和 Chunk RAG / Graph RAG / 多智能体基线，在开发计划里，后续实现。 |
| 生产环境会怎么扩展？ | LangGraph 三阶段编排、更丰富的图检索与 RAG、前端证据链与高亮、评估 pipeline 和监控。 |

---

按这份 MVP 范围，**结构层做到 Neo4j 知识图谱** + 审查（带图上下文）+ 单页前端，即可在一周内跑通演示；面试时可直接对照架构图说「Structural Layer 已实现到 Neo4j Knowledge Graph」，再结合 README 和 `docs/architecture.md` 讲推理层与完整架构即可。
