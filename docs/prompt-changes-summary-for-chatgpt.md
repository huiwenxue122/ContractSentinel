# 给 ChatGPT：抽取 Prompt 修改历史与问题总结（请据此重写需求与 Prompt）

请根据下面的事实和问题总结，重新写一份「从合同全文抽取结构化信息」的**需求说明**和**单次调用的 prompt**（优先单次调用，若你判断必须两阶段再说明）。代码会用 Python 的 `.format(text=合同全文)` 注入正文，因此 prompt 里除占位符 `{text}` 外，所有字面量花括号必须写成 `{{` 和 `}}`。

---

## 一、最初能跑通的版本（目标：恢复或优于此）

- **方式**：**单次** LLM 调用，一个 user prompt，要求模型一次输出一个 JSON，包含 5 个 key：`clauses`, `definitions`, `cross_references`, `parties`, `obligations`。
- **实际结果**：40 clauses, 5 definitions, 0 cross-refs, 2 parties（obligations 当时未强调，可能是 0）。
- **结论**：单次调用、一个 prompt 是可以跑通的，且能稳定得到 clauses、definitions、parties；只是 cross_references 和 obligations 为 0。

---

## 二、后续每次修改与出现的问题（按时间顺序）

### 修改 1：加强 cross_references 和 obligations 的抽取要求

- **动机**：希望 cross_refs 和 obligations 不要总是 0。
- **做法**：在 prompt 里明确要求「必须抽取交叉引用和义务」「不要返回空列表」、并给了很多例句（如 "subject to Section 4.1"）。
- **结果**：**definitions 从 5 变成 0**，clauses 数量也变了（变少，如 19 条）。模型似乎把「注意力」或输出空间挪给了 cross_refs/obligations，反而把 definitions 丢掉了。

### 修改 2：再强调 definitions 和「所有条款」

- **动机**：把 definitions 拉回 5，并保证条款覆盖全。
- **做法**：在 prompt 里把 definitions 和「EVERY section」写得很重，要求「至少 5 个定义」「所有编号条款」、并列举术语示例（"Services", "Affiliated Companies" 等）。
- **结果**：出现 **JSON 解析错误**（见修改 3）。也可能出现 definitions 仍为 0 或 clauses 数量异常的情况（与修改 1 叠加）。

### 修改 3：LLM 返回的 JSON 不合法导致程序报错

- **现象**：`json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes`（例如 line 408 column 1427）。即模型输出的字符串不是合法 JSON（可能缺引号、多了逗号、或内容被截断）。
- **做法**：程序侧增加了：`response_format={"type": "json_object"}`、用 `json_repair` 做容错、只解析最外层 `{...}` 等。这些是**代码层面的补救**，没有改 prompt 本身。
- **结论**：prompt 需要让模型**稳定输出合法 JSON**（键名双引号、无尾逗号、字符串内引号转义等），避免依赖修 JSON 的库。

### 修改 4：KeyError: '"name"'（或 KeyError: 'name'）

- **现象**：运行时报 `KeyError: '"name"'`，堆栈指向 `EXTRACT_STRUCTURE_USER.format(text=capped)`。
- **原因**：prompt 字符串里写了 JSON 示例，例如 `{"name": "Acme Inc."}`。在 Python 里执行 `.format(text=capped)` 时，`{name}` 会被当成占位符，而只传了 `text=...`，没有传 `name`，所以报错。
- **做法**：把 prompt 里**所有字面量花括号**改成双写：`{{` 和 `}}`，只保留一个占位符 `{text}`。这样 `.format(text=capped)` 之后，示例里才会正确显示 `{"name": "Acme Inc."}`。
- **结论**：**交给你的 prompt 若要在 Python 里用 `.format(text=合同全文)` 注入，则除 `{text}` 外，任何字面量 `{` `}` 都必须写成 `{{` `}}`。** 你生成的 prompt 要明确遵守这一点，或单独说明「在 Python 中使用时需转义花括号」。

### 修改 5：改成「两阶段」抽取（Phase 1 结构，Phase 2 条款）

- **动机**：怀疑单次调用时「输出 token 不够」，模型把空间都用来输出 clauses 长文本，导致 definitions/parties 被截断或省略，所以改为：第一次只抽 parties、definitions、cross_references、obligations；第二次只抽 clauses；最后在代码里合并。
- **做法**：拆成两个 prompt（EXTRACT_STRUCTURE_USER 和 EXTRACT_CLAUSES_USER），程序发两次 API 调用。
- **结果**：
  - 先触发了修改 4 的 KeyError（因阶段 1 的 prompt 里有未转义的 `{` `}`）。
  - 修完 KeyError 后，脚本在「Extracting (LLM)...」处**长时间无输出**（用户以为「运行不出来」）。原因可能是：两次请求都带 10 万+ 字符的正文，每次要等 1～3 分钟，且之前没有「Phase 1 / Phase 2」的中间打印。
- **结论**：两阶段不一定必要；单次调用曾得到过 40 clauses + 5 definitions + 2 parties。若恢复单次调用并写好 prompt，可能更简单、更快、更少出错。只有在你能明确论证「单次输出 token 上限必然导致 definitions/parties 缺失」时，再建议两阶段。

---

## 三、当前需求（请按此重写）

1. **目标**：从一份合同全文（纯文本，可能 10 万+ 字符）中，**一次** LLM 调用输出一个 JSON，包含：
   - `clauses`：所有条款（每条约 id, section_id, text, page），数量应与合同实际条款数一致（例如 40 条左右）。
   - `definitions`：所有定义（每条 term, definition, 可选 source_clause_id），至少 5 个若合同中有定义。
   - `parties`：当事方（每条约 name, 可选 description），通常 2 个。
   - `cross_references`：交叉引用（每条 from_clause_id, to_clause_id, 可选 ref_text），尽量多抽，可为空数组。
   - `obligations`：义务（每条 description, 可选 clause_id），尽量多抽，可为空数组。

2. **输出格式**：**仅合法 JSON**，无 markdown、无代码块外套、无解释。键名必须双引号，无尾逗号，字符串内若有引号需转义。以便程序直接 `json.loads(...)` 解析。

3. **约束**：  
   - 合同正文在调用时会通过占位符注入，占位符为 **`{text}`**。  
   - 若该 prompt 会在 Python 里用 `.format(text=合同全文)` 注入，则 prompt 中**除 `{text}` 外**的所有字面量 `{` `}` 必须写成 **`{{`** 和 **`}}`**。

4. **优先**：**单次调用、一个 user prompt** 能同时得到 clauses、definitions、parties（且 definitions 不为 0）。在此基础上再考虑 cross_references 和 obligations。若你判断单次调用必然无法同时满足「条款全」和「定义全」，再说明理由并给出两阶段方案。

---

## 四、请你输出的内容

1. **需求说明**（可给产品/开发看）：简要说明输入、输出、五个 key 的含义与结构、以及「单次调用优先」的理由。
2. **System prompt**：一段短说明（角色 + 只输出合法 JSON、键名与结构按约定）。
3. **User prompt**：一段完整 prompt，其中合同正文位置用 **`{text}`** 表示；若供 Python `.format(text=...)` 使用，则除 `{text}` 外所有花括号写成 `{{` `}}`。
4. 若你坚持两阶段，请分别给出「阶段 1」和「阶段 2」的 user prompt，并说明为何单次无法满足。

把上述「修改历史与问题」和「当前需求」一起发给 ChatGPT 后，用其生成的需求与 prompt 替换项目中的 `docs/prompt-requirements.md` 和 `app/extraction/prompts.py` 中的内容；若采用单次调用，需把 `app/extraction/entities.py` 中两阶段调用改回单次调用并合并结果。
