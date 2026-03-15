# MVP 本地运行：你需要做的事

代码不依赖任何「数据集」训练，只依赖 **LLM API** 和 **Neo4j**。按下面做即可跑通演示。

---

## 1. 环境

- **Python 3.10+**
- 终端里在项目根目录执行：
  ```bash
  cd /Users/claire/ContractSentinel
  python -m venv .venv
  source .venv/bin/activate   # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  ```

---

## 2. 你要准备的三样东西

### ① OpenAI API Key（必选）

- 审查和抽取都用 **OpenAI API**，不需要自己准备数据集或训练模型。
- 打开 https://platform.openai.com/api-keys 创建 key。
- 在项目根目录创建 `.env` 文件（可复制 `.env.example`）：
  ```bash
  cp .env.example .env
  ```
  在 `.env` 里填写：
  ```env
  OPENAI_API_KEY=sk-你的key
  ```

### ② Neo4j（必选，结构层要写知识图谱）

- **方式 A：Docker（推荐）**
  ```bash
  docker run -d --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    neo4j:5
  ```
  然后在 `.env` 里设：
  ```env
  NEO4J_URI=bolt://localhost:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=your_password
  ```

- **方式 B：本地安装**  
  从 https://neo4j.com/download/ 安装，创建数据库并记下 bolt 地址、用户名、密码，写入 `.env`。

### ③ 一份样本合同 PDF（演示用）

- **不需要**任何「训练数据集」，只需要 **1 份** 用来演示的合同（如 NDA 或 MSA）。
- 你可以：
  - 从网上下载任意 NDA/MSA 模板 PDF，或  
  - 用自己有的脱敏合同。
- 把这一份 PDF 放到项目的 **`data/sample_contracts/`** 目录下，例如：
  ```text
  data/sample_contracts/sample_nda.pdf
  ```
- 后端「用样本」功能会读这个目录下的 PDF 做解析和审查演示。

---

## 3. 小结：你需要干什么

| 项目 | 你要做的 |
|------|----------|
| **数据集** | **不需要**准备训练数据；只用 **1 份** 演示用 PDF 放到 `data/sample_contracts/`。 |
| **LLM** | 直接接 **OpenAI API**；在 `.env` 里配置 `OPENAI_API_KEY` 即可。 |
| **Neo4j** | 用 Docker 起一个 Neo4j，或在本地安装，在 `.env` 里配置 `NEO4J_URI`、`NEO4J_USER`、`NEO4J_PASSWORD`。 |
| **运行** | `uvicorn app.main:app --reload` 启动后端；后续任务会加上上传和审查接口。 |

当前已完成：**任务 1（骨架 + config + requirements）** 和 **任务 2（schemas）**。接下来会做任务 3～4（PDF 解析 + LLM 抽取），你只要准备好上述三样即可。
