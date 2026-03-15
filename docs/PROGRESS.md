# ContractSentinel — Progress & Milestones

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

- **完成**：`app/agents/prompts.py`（SCANNER_SYSTEM、SCANNER_USER_TEMPLATE）；`app/agents/scanner.py`（`scan_clause(clause_text, clause_ref, rules, graph_context)`，调用 OpenAI JSON mode，解析 findings，兼容 `rule_triggered`/`rule_id`、`evidence_summary`/`evidence`）；`scripts/run_scanner_demo.py`（从图取随机或指定 clause，调 get_context_for_clause → scan_clause，打印 findings）。

#### 主要问题 1：随机跑多个 section 时 Findings 始终为 0

- **现象**：对多个 section 跑 Scanner，输出均为 Findings: 0 (none)。
- **可能原因**：Scanner 逻辑错误、规则/合同不匹配、或传入模型的 clause_text 为空。
- **排查**：
  - **诊断 1**：人工构造一条必中条款（含 "indemnify, defend, and hold harmless" + "without limitation"），单独调 `scan_clause`。**结果**：能命中 R003 和 R001 → Scanner 代码与解析逻辑正常。
  - **诊断 2**：在 scanner 中加环境变量 `CONTRACT_SENTINEL_DEBUG_SCANNER=1`，打印传入模型的 rules_text、clause_text、graph_context。对指定 section_9_1 跑 demo 时发现 **CLAUSE 为空、GRAPH CONTEXT 为默认提示** → 问题在「数据未传入」而非 Scanner 本身。

#### 主要问题 2：run_scanner_demo 传入的 clause_text 为空

- **根因**：部分 clause 在 Neo4j 中不存在或 Clause 节点的 `text` 未写入。例如结构层管道用**规则分段**产出 clauses，若 PDF 中未识别出 "Section 9.1" 等标题，则图中没有 section_9_1，`get_context_for_clause` 返回的 `clause_text` 为空。
- **解决**：
  - 在 `run_scanner_demo.py` 中显式用 `ctx.get("clause_text")`，并对空字符串打 **Warning**，提示「该 clause 可能在图中不存在或未存储条文」。
  - 文档中明确：Findings: 0 有两类原因——（1）数据缺失：clause_text 为空；（2）规则未命中：有完整 clause_text 但条文不匹配 playbook。

#### 主要问题 3：指定 section 时 shell 报错 "zsh: number expected"

- **现象**：执行 `python scripts/run_scanner_demo.py EX-10.4(a) section_9_1` 时 zsh 报错。
- **根因**：合同 ID 中含括号 `(a)`，zsh 将括号当作特殊字符解析。
- **解决**：合同 ID 加引号，例如 `python scripts/run_scanner_demo.py "EX-10.4(a)" section_9_1`。已在 `docs/commands.md` 中统一改为带引号写法。

#### 主要问题 4：有 clause_text 的 section 仍返回 0 findings

- **现象**：例如 section_5_1 在 debug 下 clause_text、graph_context 均非空，但 Findings 仍为 0。
- **结论**：该条款内容（如 Company Data 定义）本身不包含当前 playbook 的关键词（indemnify、terminate、unlimited liability 等），属于**规则未命中**，而非 bug。与「空 clause_text 导致 0」需区分。
- **实施**：增加两项验证脚本 `run_scanner_verifications.py`：类别 1 用有 text 的 clause（如 section_5_1）验证「有文本但 0 = 规则未命中」；类别 2 用图中不存在的 clause（如 section_9_1 若未 ingest）验证「空文本 = 图里没数据」。并在文档中写明「当前状态总结」与「已确认 / 尚未确认」结论。

### 全合同扫描与写回 Neo4j

- **完成**：
  - `scripts/scan_all_clauses.py`：遍历图中所有 clause，对每个有 clause_text 的条款调 `scan_clause`，汇总为 (Clause, Rule, Risk Level, Evidence)；终端打印表格，并写入 `out/scan_<contract_id>.tsv`。
  - 将 findings 写回 Neo4j：新增 `Rule` 节点（id、risk_level、description）与关系 `Clause -[:TRIGGERS {evidence?}]-> Rule`；每次运行前删除该合同下已有 TRIGGERS 再写入，便于 Critic Agent 直接查询。
- **图模型**：`app/graph/models.py` 增加 `LABEL_RULE`、`REL_TRIGGERS`。
- **结果**：一条命令可扫完整合同并得到 Clause | Rule | Risk Level 表与 TSV；图中可查「某条款触发了哪些规则」，为后续 Critic 提供输入。

---

## 当前状态小结

| 层级       | 状态 | 说明 |
|------------|------|------|
| 结构层     | ✅   | PDF → 解析 → 规则分段 + LLM 抽取 → 交叉引用 → Neo4j 入库，端到端跑通 |
| 检索层     | ✅   | 按 clause 取 clause_text + graph_context，retrieval demo 验证 |
| Playbook   | ✅   | 多规则 YAML 加载，Scanner 使用 |
| Scanner    | ✅   | 单条款/全合同扫描正常；人工必中条款可触发 findings；真实条款 0 需区分「空文本」与「规则未命中」 |
| 全合同扫描 | ✅   | scan_all_clauses 输出 TSV 并写回 TRIGGERS 到 Neo4j |
| Critic     | ⏳   | 未实现；图已有 TRIGGERS，可直接读 Clause→Rule |
| Evaluator  | ⏳   | 未实现 |
| LangGraph  | ⏳   | 未实现 |
| API/前端   | ⏳   | 骨架存在，审查流未接 |

---

## 脚本与命令速查

- 结构层：`python scripts/run_structural_pipeline.py "data/sample_contracts/EX-10.4(a).pdf"`
- 图检索：`python scripts/run_retrieval_demo.py "EX-10.4(a)" section_1_1`
- Scanner 单条：`python scripts/run_scanner_demo.py "EX-10.4(a)" section_5_1`
- Scanner 全合同：`python scripts/scan_all_clauses.py "EX-10.4(a)"`
- 诊断/验证：`python scripts/run_scanner_diagnostic.py`；`python scripts/run_scanner_verifications.py "EX-10.4(a)"`

更多命令见 `docs/commands.md`。
