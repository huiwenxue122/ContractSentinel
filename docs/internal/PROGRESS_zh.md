# ContractSentinel — Progress & Milestones（中文，仅供本人查阅）

本文档记录项目各阶段完成情况、遇到的主要问题与解决方法、以及结果。便于复盘与展示开发过程。

---

## Phase 0：项目骨架与数据模型

### 完成内容

- 项目目录与依赖：`app/` 包结构、`app/config.py`（含 `get_settings()`、`.env` 支持）、`requirements.txt`；子包 `parsing`、`extraction`、`graph`、`retrieval`、`agents`、`schemas`、`api`、`evaluation` 的 `__init__.py`。
- 数据模型：`app/schemas/contract.py`（Clause、Definition、Party、Obligation、CrossReference、Contract）、`app/schemas/playbook.py`（Rule、RiskLevel）、`app/schemas/risk_memo.py`、`app/schemas/api_models.py`。

### 结果

- 可 `import app`，`get_settings()` 可读取 NEO4J_*、OPENAI_API_KEY、openai_model 等；依赖可通过 `pip install -r requirements.txt` 安装。

---

## Phase 1：结构层

### 任务 3：PDF 解析（Marker）

- **完成**：`app/parsing/`，使用 Marker 将 PDF 转为版式感知文本块，对外 `parse_pdf(path) -> (full_text, blocks)`。
- **结果**：样本 PDF（如 `EX-10.4(a).pdf`）可解析出完整文本与分页块。

### 任务 4：法律实体与关系抽取（LLM）

- **完成**：`app/extraction/prompts.py`、`app/extraction/entities.py`（`extract_contract` 单次 LLM 调用抽取 clauses、definitions、parties、obligations、cross_references）；`app/extraction/clause_segmenter.py`（规则分段：按 Section X.Y 正则匹配）；`app/extraction/cross_references.py`（规则解析交叉引用，生成 CrossReference 列表）。
- **流程**：结构层管道采用「规则分段优先」：先 `segment_clauses(full_text)` 得到 rule-based clauses，再 LLM 抽取；若规则分段有结果，则用其覆盖 LLM 的 clauses，再对 clauses 做交叉引用抽取。
- **结果**：输出与 `schemas.contract` 一致，可供 ingest 使用。

### 任务 5：Neo4j 图存储与查询

- **完成**：`app/graph/client.py`、`app/graph/models.py`（节点/边常量）、`app/graph/ingest.py`（Contract → Clause、Definition、Party、Obligation 及 HAS_CLAUSE、DEFINES、HAS_OBLIGATION、HAS_PARTY、REFERENCES）、`app/graph/query.py`（`get_clause_neighborhood`：某 clause 的 text、section_id、references_in/out、definitions、obligations）。
- **结果**：抽取结果可写入 Neo4j；按 contract_id、clause_id 可查询条款邻域。

### 任务 6：结构层端到端串联

- **完成**：`scripts/run_structural_pipeline.py`（PDF → parse → segment_clauses → extract_contract → extract_cross_references → ingest_contract）；`scripts/verify_extraction.py`（仅 LLM 抽取并导出 `out/contract_<stem>.json`）。
- **结果**：一条命令跑通「PDF → 规则分段 → LLM 抽取 → 交叉引用 → Neo4j 写入」；图中可查到条款与引用关系。

---

## Phase 2：推理层 — 检索与 Playbook

### 任务 7：审查手册配置与加载

- **完成**：`data/playbooks/default.yaml`（多条规则：R001 无限责任、R002 单方终止、R003 宽泛赔偿、R004 数据使用、R005 IP 归属、R006 单方修订等，含 keywords、criteria、risk_level）；`app/agents/playbook_loader.py`（YAML → List[Rule]）。
- **结果**：Scanner 可加载 playbook 规则列表。

### 任务 8：图增强检索（RAG + Graph Context）

- **完成**：`app/retrieval/graph_context.py`（`build_graph_context`：从 get_clause_neighborhood 取 definitions、obligations、references 拼成一段文本）；`app/retrieval/rag.py`（`get_context_for_clause`：返回 `clause_text`、`section_id`、`graph_context`、`snippets`）；`scripts/run_retrieval_demo.py`（随机或指定 contract_id/clause_id 打印 clause_text、graph_context、snippets）。
- **结果**：给定 contract_id、clause_id，可拿到该条款全文与图上下文，供 Scanner 使用。

---

## Phase 3：推理层 — Scanner Agent 与全合同扫描

### 任务 9：Scanner Agent

- **完成**：`app/agents/prompts.py`（SCANNER_SYSTEM、SCANNER_USER_TEMPLATE）；`app/agents/scanner.py`（`scan_clause(...)`，调用 OpenAI JSON mode，解析 findings）；`scripts/run_scanner_demo.py`（从图取随机或指定 clause，调 get_context_for_clause → scan_clause，打印 findings）。

#### 主要问题 1：随机跑多个 section 时 Findings 始终为 0

- **排查**：诊断 1 人工必中条款能命中 R003/R001 → Scanner 正常。诊断 2 发现 CLAUSE 为空 → 问题在数据未传入。
- **主要问题 2**：部分 clause 在 Neo4j 不存在或未存 text，导致 clause_text 为空；demo 加 Warning，区分数据缺失 vs 规则未命中。
- **主要问题 3**：合同 ID 含括号导致 zsh 报错 → 加引号。
- **主要问题 4**：有 text 的 section 仍 0 → 属规则未命中；加验证脚本区分两类 0。

### 全合同扫描与写回 Neo4j

- **完成**：`scripts/scan_all_clauses.py`；Clause -[:TRIGGERS]-> Rule 写回图；图模型增加 LABEL_RULE、REL_TRIGGERS。

---

## 当前状态小结

| 层级       | 状态 | 说明 |
|------------|------|------|
| 结构层     | ✅   | PDF → 解析 → 规则分段 + LLM 抽取 → 交叉引用 → Neo4j 入库，端到端跑通 |
| 检索层     | ✅   | 按 clause 取 clause_text + graph_context |
| Playbook   | ✅   | 多规则 YAML 加载 |
| Scanner    | ✅   | 单条款/全合同扫描；TRIGGERS 写回 Neo4j |
| Critic/Evaluator/LangGraph/API | ⏳   | 未实现 |

更多命令见 `docs/commands.md`。
