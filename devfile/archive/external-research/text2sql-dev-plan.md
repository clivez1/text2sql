# Text2SQL 数据分析 Agent 开发计划

> 项目目标：在 **2 周内完成可执行方案**，在 **6 周内完成可演示 Demo**，用于面试展示与工程能力证明。  
> 推荐路线：**基于 Vanna 二次开发**，以“快速成型 + 可解释 + 可扩展”为优先。  
> 目标用户：人工智能专业研究生。  
> 目标岗位：软件开发工程师 / Python 后端 / AI 应用开发 / 机器学习 / 测试开发 / 数据开发。

---

## 1. 项目定义与范围

### 1.1 核心价值
用户通过自然语言提问，系统完成：
1. 问题理解与必要澄清
2. Schema 检索与 SQL 生成
3. SQL 安全检查与执行
4. 结果表格展示与图表推荐
5. SQL 解释与自然语言总结

### 1.2 Demo 必做功能（MVP）
- 自然语言 → SQL
- SQL 执行 → 表格结果
- 自动图表推荐与渲染
- SQL 解释器
- 模糊问题追问澄清
- 查询历史记录与复用

### 1.3 明确不做（本期范围控制）
- 不做多租户权限系统
- 不做复杂 BI 报表平台
- 不做训练自研大模型
- 不做生产级高并发部署
- 不做跨数据库复杂联邦查询

---

## 2. 总体路线

### Phase A：2 周出方案
目标：形成技术决策、项目骨架、开发节奏、演示路线。

### Phase B：6 周出 Demo
目标：做出一套可本地启动、可演示、可讲清楚设计取舍的 Text2SQL Agent。

---

## 3. 技术架构设计

### 3.1 架构原则
- **Demo-first**：先打通端到端主链路，再补增强能力
- **可解释优先**：SQL 解释、图表推荐理由、错误原因可展示
- **只读安全**：默认只读连接，避免误写数据库
- **模块解耦**：NL2SQL、执行、图表、记忆分层清晰
- **可替换模型**：支持 OpenAI / Qwen / Ollama 作为推理后端

### 3.2 推荐架构图（逻辑）
```text
User Query
   ↓
Query Orchestrator
   ├─ Clarifier（是否需要追问）
   ├─ Schema Retriever（检索表结构/示例SQL）
   ├─ SQL Generator（生成SQL）
   ├─ SQL Guard（安全检查）
   ├─ SQL Executor（执行查询）
   ├─ Chart Recommender（图表推荐）
   └─ Explainer / Summarizer（解释SQL与结果）
   ↓
Streamlit UI / FastAPI
```

### 3.3 模块划分
| 模块 | 职责 | 关键输出 |
|---|---|---|
| `app/ui` | Demo 界面、交互、结果展示 | 页面、图表、历史记录 |
| `app/api` | FastAPI 接口层，供前端或测试调用 | `/ask` `/health` `/schema` |
| `app/core/orchestrator` | 编排主流程 | 标准化响应对象 |
| `app/core/llm` | 模型适配与 Prompt 管理 | SQL、解释文本、澄清问题 |
| `app/core/retrieval` | Schema/示例 SQL 检索 | 相关表、字段、样例 |
| `app/core/sql` | SQL 生成、安全校验、执行 | SQL、结果集、异常 |
| `app/core/chart` | 图表推荐与配置生成 | Plotly spec |
| `app/core/memory` | 查询历史、用户修正记录 | 历史问答、已纠正 SQL |
| `app/core/explain` | SQL 解释、业务总结 | 自然语言说明 |
| `app/config` | 环境变量、数据库连接、模型配置 | 配置对象 |
| `tests` | 单测、集成测试、回归样例 | 可重复验证结果 |

### 3.4 目录结构建议
```text
text2sql-agent/
├─ app/
│  ├─ api/
│  │  ├─ main.py
│  │  └─ routes/
│  │     ├─ ask.py
│  │     ├─ health.py
│  │     └─ schema.py
│  ├─ ui/
│  │  └─ streamlit_app.py
│  ├─ core/
│  │  ├─ orchestrator/
│  │  │  └─ pipeline.py
│  │  ├─ llm/
│  │  │  ├─ client.py
│  │  │  ├─ prompts.py
│  │  │  └─ models.py
│  │  ├─ retrieval/
│  │  │  ├─ schema_loader.py
│  │  │  ├─ vector_store.py
│  │  │  └─ examples_repo.py
│  │  ├─ sql/
│  │  │  ├─ generator.py
│  │  │  ├─ guard.py
│  │  │  ├─ executor.py
│  │  │  └─ validator.py
│  │  ├─ chart/
│  │  │  ├─ recommender.py
│  │  │  └─ renderer.py
│  │  ├─ memory/
│  │  │  ├─ history_store.py
│  │  │  └─ feedback_store.py
│  │  └─ explain/
│  │     ├─ sql_explainer.py
│  │     └─ summary.py
│  ├─ config/
│  │  ├─ settings.py
│  │  └─ logging.py
│  └─ shared/
│     ├─ schemas.py
│     └─ types.py
├─ data/
│  ├─ demo_db/
│  ├─ ddl/
│  ├─ examples/
│  └─ chroma/
├─ scripts/
│  ├─ init_demo_db.py
│  ├─ ingest_schema.py
│  └─ load_examples.py
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ fixtures/
├─ .env.example
├─ requirements.txt
├─ docker-compose.yml
├─ Dockerfile
└─ README.md
```

### 3.5 接口设计

#### `POST /ask`
请求：
```json
{
  "question": "上个月销售额最高的前5个产品是什么？",
  "session_id": "demo-user-001",
  "chart_enabled": true
}
```

响应：
```json
{
  "needs_clarification": false,
  "clarification_question": null,
  "generated_sql": "SELECT ...",
  "sql_explanation": "这条 SQL 按月份筛选后统计产品销售额，并按总额降序排序。",
  "result_preview": [{"product": "A", "sales": 10000}],
  "chart": {
    "type": "bar",
    "x": "product",
    "y": "sales",
    "reason": "适合展示 TopN 对比"
  },
  "summary": "上个月销售额最高的是 A 产品。"
}
```

#### `GET /health`
- 返回服务与数据库连接状态

#### `GET /schema`
- 返回可查询表结构概览

### 3.6 数据流设计
1. 接收问题
2. 判断是否模糊，必要时返回追问
3. 检索相关表结构、字段和示例 SQL
4. 生成 SQL
5. 做危险语句校验（仅 SELECT / LIMIT / 白名单表）
6. 执行 SQL
7. 根据结果列和数据类型推荐图表
8. 生成 SQL 解释与业务总结
9. 将问题、SQL、反馈写入历史记录

---

## 4. 开发计划（6 周里程碑）

## Week 1：项目启动与基线跑通
### 目标
- 跑通 Vanna / 数据库 / UI 最小链路
- 明确代码骨架与样例数据

### 任务拆解
- 搭建 Python 环境与依赖
- 初始化项目目录
- 准备 Demo 数据库（SQLite）
- 跑通 Vanna 官方最小示例
- 建立 `.env.example` 与配置加载逻辑
- 完成首版 README 和启动脚本

### 验收标准
- `streamlit run app/ui/streamlit_app.py` 可启动
- Demo 数据库可连接
- 至少 1 个自然语言问题能转成 SQL 并执行

### 里程碑产物
- 项目骨架
- Demo 数据库
- 最小可运行界面

---

## Week 2：Schema 检索与基础 SQL 生成
### 目标
- 让系统“知道数据库结构”
- 提升单表查询的稳定性

### 任务拆解
- 编写 Schema 导入脚本
- 将 DDL / 字段说明 / 示例 SQL 写入 Chroma
- 设计 SQL 生成 Prompt
- 建立 20 条基础问答测试集
- 增加 SQL 基础校验

### 验收标准
- 单表查询准确率达到可演示水平（建议 70%+）
- 能输出 SQL 与自然语言解释
- 错误 SQL 不会直接执行危险语句

### 里程碑产物
- Schema RAG
- 测试样例集 v1
- SQL 生成主链路

---

## Week 3：多表 JOIN 与结果可视化
### 目标
- 支持 2~3 表关联分析
- 完成“查完就能看图”的展示链路

### 任务拆解
- 优化多表 JOIN Prompt 模板
- 增加字段关联信息（外键/业务关系）
- 实现 Plotly 图表推荐逻辑
- 支持柱状图 / 折线图 / 饼图 / 表格
- UI 支持 SQL、结果表、图表三联展示

### 验收标准
- 至少 3 个多表场景可稳定演示
- 图表能根据结果列类型自动推荐
- 页面可同时展示 SQL、数据和图表

### 里程碑产物
- JOIN 查询
- 图表推荐器
- UI 主展示流

---

## Week 4：差异化能力实现
### 目标
- 做出“不是只会生成 SQL”的特色能力

### 任务拆解
- 实现 SQL 解释器
- 实现追问澄清逻辑
- 增加查询历史记录
- 支持用户修正 SQL 并回写示例
- 中文 Prompt 优化

### 验收标准
- 模糊问题会先追问
- SQL 解释可读、适合面试讲解
- 历史记录可查看并复用

### 里程碑产物
- SQL 解释器
- Clarifier
- 历史学习机制 v1

---

## Week 5：稳定性、测试与工程化打磨
### 目标
- 把 Demo 做稳，避免演示翻车

### 任务拆解
- 增加异常处理与兜底文案
- 增加 SQL 超时 / 空结果 / 语法错误处理
- 写单元测试与集成测试
- 增加 Dockerfile / docker-compose
- 增加日志与调试开关

### 验收标准
- 核心场景回归测试通过
- 本地可一键启动
- 常见错误有清晰提示

### 里程碑产物
- 测试集 v2
- Docker 启动方案
- 稳定版 Demo

---

## Week 6：文档、演示脚本与面试包装
### 目标
- 让项目“能演、能讲、能答”

### 任务拆解
- 完善 README、架构图、接口文档
- 准备演示脚本与截图
- 准备 3 个面试场景
- 准备技术亮点与取舍说明
- 预演 2~3 轮，记录问题并修复

### 验收标准
- 10 分钟内可完整演示
- 可清楚解释：为什么选 Vanna、如何做 RAG、如何保证 SQL 安全
- 项目文档可供面试官快速阅读

### 里程碑产物
- README 完整版
- 演示脚本
- 面试问答清单

---

## 5. 每周可验收清单

| 周次 | 必须验收 | 演示可见结果 |
|---|---|---|
| W1 | 环境可跑通 | 页面能打开，能连库 |
| W2 | 单表查询可用 | 输入问题后返回 SQL + 结果 |
| W3 | 多表与图表可用 | 同时展示 SQL/表格/图表 |
| W4 | 差异化功能可见 | 会追问、会解释 SQL |
| W5 | 稳定性增强 | 错误时不崩，能提示 |
| W6 | 面试可演 | 有完整脚本和话术 |

---

## 6. 风险与应对

| 风险 | 影响 | 预防 / 应对 |
|---|---|---|
| Vanna 二次开发耦合较深 | 影响迭代效率 | 先包一层自有 orchestrator，避免业务逻辑直接散落在框架里 |
| SQL 生成不稳定 | Demo 体验差 | 用示例 SQL + Schema 检索 + 固定测试集回归 |
| 中文问题理解偏差 | 回答质量不稳 | 中文 Prompt 单独优化，保留澄清机制 |
| 图表推荐不合理 | 演示观感差 | 先做规则版推荐，不依赖模型自由发挥 |
| 数据库安全问题 | 风险高 | 只读账号、仅允许 SELECT、表白名单、LIMIT 注入 |
| 范围失控 | 6 周出不了 Demo | 严格执行 P0/P1/P2 分层，不做 BI 平台化 |
| API Key / 外部模型不稳定 | 阻塞开发 | 预留 Ollama / Qwen 本地模型备选 |

---

## 7. 环境搭建指南

## 7.1 依赖清单
```txt
python>=3.11
pip>=24
sqlite3
```

`requirements.txt` 建议：
```txt
vanna>=0.7
fastapi>=0.115
uvicorn>=0.30
streamlit>=1.49.0
plotly>=5.17.0
pandas>=2.2.0
sqlalchemy>=2.0.41
chromadb>=0.5.0
openai>=1.0.0
python-dotenv>=1.0.0
pydantic>=2.8
pytest>=8.0
httpx>=0.27
```

可选：
```txt
psycopg2-binary
pymysql
ollama
```

## 7.2 配置文件
`.env.example`
```bash
APP_ENV=dev
APP_HOST=0.0.0.0
APP_PORT=8000

LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini

DB_URL=sqlite:///data/demo_db/sales.db
VECTOR_DB_PATH=./data/chroma
SQL_MAX_ROWS=200
SQL_QUERY_TIMEOUT=15

ENABLE_HISTORY=true
ENABLE_CHART=true
ENABLE_CLARIFICATION=true
READONLY_MODE=true
```

## 7.3 初始化命令
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 7.4 启动命令
### 方案 A：只跑 Streamlit Demo
```bash
streamlit run app/ui/streamlit_app.py
```

### 方案 B：前后端分离
```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
streamlit run app/ui/streamlit_app.py
```

## 7.5 数据初始化命令
```bash
python scripts/init_demo_db.py
python scripts/ingest_schema.py
python scripts/load_examples.py
```

## 7.6 Docker 快速启动（Week 5 后）
```bash
docker build -t text2sql-agent .
docker run --rm -p 8000:8000 --env-file .env text2sql-agent
```

---

## 8. 演示脚本设计

## 8.1 目标
在 8~10 分钟内展示：
- LLM + RAG + 数据库 + 可视化 + Agent 体验
- 不只是“生成 SQL”，而是“完成分析任务”

## 8.2 推荐演示场景

### 场景 1：TopN 销售分析
用户提问：
> 上个月销售额最高的前 5 个产品是什么？

展示点：
- 自然语言 → SQL
- SQL 执行结果
- TopN 柱状图
- SQL 解释器

### 场景 2：城市对比分析
用户提问：
> 对比一下北京和上海各季度的订单量变化。

展示点：
- 多表 JOIN
- 分组聚合
- 折线/分组柱状图
- 自然语言总结

### 场景 3：模糊问题澄清
用户提问：
> 查询用户数据。

系统追问：
> 你想看哪些字段？是否需要时间范围或筛选条件？

展示点：
- Agent 不是盲查，而是先澄清
- 产品思维与用户体验

### 场景 4：用户纠错学习
用户提问后对 SQL 进行修正

展示点：
- 查询历史记录
- 用户反馈回写
- 可解释“后续如何提升命中率”

## 8.3 演示话术模板
1. **开场**：
   - 这是一个面向非 SQL 用户的数据分析 Agent，目标是把自然语言问题转换成可执行查询，并给出图表和解释。
2. **技术路线**：
   - 我基于 Vanna 做二次开发，没有重复造轮子，而是把精力放在可解释性、中文体验和交互设计上。
3. **核心亮点**：
   - RAG 理解 Schema
   - SQL 安全检查
   - 智能图表推荐
   - 追问澄清
   - 查询历史学习
4. **收尾**：
   - 这个项目既能体现 LLM 应用能力，也能体现后端工程、Prompt 设计和测试思维。

## 8.4 面试常见问题准备
| 问题 | 建议回答方向 |
|---|---|
| 为什么选 Vanna？ | 开发效率高、社区成熟、便于把时间投入差异化能力 |
| 如何保证 SQL 安全？ | 只读连接、白名单表、仅允许 SELECT、超时与 LIMIT 控制 |
| 如何提升准确率？ | Schema RAG、示例 SQL、澄清机制、固定评测集 |
| 为什么不是纯 Prompt？ | Text2SQL 本质依赖数据库上下文，RAG 比纯 Prompt 稳定 |
| 如何扩展到生产？ | PostgreSQL、缓存、鉴权、异步执行、监控、日志 |

---

## 9. 开发分工建议（单人项目视角）

| 角色视角 | 本项目对应工作 |
|---|---|
| Python 后端 | API、SQL 执行、安全校验、配置管理 |
| AI 应用开发 | Prompt、RAG、Agent 流程设计 |
| 数据开发 | Schema 建模、SQL 优化、数据集准备 |
| 测试开发 | 测试集、回归用例、错误场景覆盖 |
| 软件工程 | Docker、README、目录结构、可复现启动 |

> 面试时可以强调：这是一个“多岗位能力交叉”的项目，而不是单点算法作业。

---

## 10. 本周立刻可执行的启动清单

### 未来 3 天
- 确认 Demo 数据库题材（销售 / 电商 / 用户增长）
- 初始化项目骨架
- 跑通 Vanna 最小 Demo
- 建立 `.env.example` 与 README

### 未来 7 天
- 完成 Schema 导入
- 完成 20 条基础问答测试集
- 实现单表查询主链路
- 输出 SQL + 结果 + 解释

### 未来 14 天
- 完成整体方案冻结
- 明确模块边界与接口
- 确认演示脚本和样例数据
- 进入 Week 3 的多表与图表阶段

---

## 11. 最终建议
- **技术基线**：Vanna + SQLAlchemy + Chroma + Streamlit + Plotly
- **面试亮点优先级**：SQL 解释器 > 追问澄清 > 智能图表推荐 > 查询历史学习
- **开发策略**：先跑主链路，再补特色功能，不做过度工程化
- **交付目标**：6 周内做出一套“可运行、可演示、可讲清楚设计取舍”的 Demo

---

## 12. DoD 对照检查
- [x] 开发计划可执行：含每周任务、里程碑、验收标准
- [x] 技术架构清晰：含目录结构、模块划分、接口设计
- [x] 环境搭建可复现：含依赖、配置、启动命令
- [x] 演示脚本完整：含场景、话术、常见问答
