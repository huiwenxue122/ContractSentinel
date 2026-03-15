# ContractSentinel 终端命令速查

每次重新跑项目时按顺序看这里即可。所有命令默认在**项目根目录** `ContractSentinel` 下执行。

---

## 一、一次性准备（新电脑 / 新 clone 后）

### 1. 进入项目并创建虚拟环境

```bash
cd /Users/claire/ContractSentinel
python -m venv .venv
source .venv/bin/activate
```

Windows 激活命令：

```bash
.venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 环境变量

```bash
cp .env.example .env
```

然后编辑 `.env`，填写：

- `OPENAI_API_KEY=sk-...`
- `NEO4J_URI=bolt://localhost:7687`
- `NEO4J_USER=neo4j`
- `NEO4J_PASSWORD=你的密码`

### 4. 启动 Neo4j（Docker）

若本机还没有名为 `neo4j` 的容器，或需要重新起一个（密码与 .env 一致）：

```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/你的密码 neo4j:5
```

若已有同名容器，先删再起：

```bash
docker stop neo4j
docker rm neo4j
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/你的密码 neo4j:5
```

确认在跑：

```bash
docker ps
```

---

## 二、每次打开终端要跑项目时

### 1. 进入项目并激活虚拟环境

```bash
cd /Users/claire/ContractSentinel
source .venv/bin/activate
```

### 2. （可选）确认 Neo4j 在跑

```bash
docker ps
```

若 `neo4j` 未在列表或未运行，用 Docker Desktop 点启动，或重新执行上面「启动 Neo4j」的 `docker run`。

---

## 三、按任务/功能要运行的命令

### 任务 3+4：PDF 解析 + LLM 抽取（结构层脚本）

用样本 PDF 跑通「PDF → 合同结构」，不写 Neo4j：

```bash
python scripts/run_structural_pipeline.py "data/sample_contracts/EX-10.4(a).pdf"
```

不传参数则默认用 `data/sample_contracts/EX-10.4(a).pdf`：

```bash
python scripts/run_structural_pipeline.py
```

### 验证抽取结果（摘要 + 导出 JSON）

```bash
python scripts/verify_extraction.py "data/sample_contracts/EX-10.4(a).pdf"
```

输出在 `out/contract_EX-10.4(a).json`，可打开与 PDF 对照。

### 启动后端 API（FastAPI）

（任务 8 完成后可用）

```bash
uvicorn app.main:app --reload
```

浏览器访问：<http://127.0.0.1:8000>，API 文档：<http://127.0.0.1:8000/docs>。

### 启动前端（任务 9 完成后可用）

在**新开一个终端**里：

```bash
cd /Users/claire/ContractSentinel/frontend
npm install
npm run dev
```

按提示在浏览器打开（一般为 <http://localhost:3000>）。

---

## 四、常用检查命令

| 目的           | 命令              |
|----------------|-------------------|
| 看 Neo4j 是否在跑 | `docker ps`       |
| 停掉 neo4j 容器  | `docker stop neo4j` |
| 删除 neo4j 容器  | `docker rm neo4j`   |
| 当前 Python / 包 | `which python` / `pip list` |

---

## 五、命令与任务对应关系

| 任务           | 要运行的命令（在项目根、已激活 .venv） |
|----------------|----------------------------------------|
| 环境准备       | 见「一、一次性准备」                   |
| 每次开终端     | `cd ...` + `source .venv/bin/activate` |
| 任务 3+4 测试  | `python scripts/run_structural_pipeline.py "data/sample_contracts/EX-10.4(a).pdf"` |
| 验证抽取       | `python scripts/verify_extraction.py "data/sample_contracts/EX-10.4(a).pdf"` |
| 启动后端       | `uvicorn app.main:app --reload`        |
| 启动前端       | `cd frontend && npm run dev`          |

有新任务或新脚本时，把对应命令补进本文档即可。
