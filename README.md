# 🔍 Text2SQL Agent

> 自然语言转 SQL 智能查询系统 | 本地规则 / 本地 RAG 优先，LLM 仅作补充

[![Python](https://img.shields.io/badge/Python-3.11+-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-orange)]()
[![ChromaDB](https://img.shields.io/badge/ChromaDB-1.0+-purple)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()

---

## 这是什么？

**Text2SQL Agent** 是一个面向 BI+AI 领域展示的 Demo 项目。

**核心能力**：
- 输入中文问题 → 本地分类/规则/模板优先生成 SQL → 执行查询 → 智能图表
- 支持 SQLite / MySQL / PostgreSQL
- 内置 SQL 注入防护、表白名单、只读模式

**适用场景**：
- BI 工具的自然语言查询原型
- Text2SQL 技术方案演示
- 本地规则 / 本地 RAG / Text2SQL 工程化学习参考

---

## 读者导航

> 开发推进与进度判断请优先阅读 `devfile/`。`docs/` 主要承担使用说明、API、配置、部署说明。

```
我是谁？                    我该看什么？
─────────────────────────────────────────────
新用户/评估者        →    快速启动 → 演示截图
使用者              →    QUICKSTART.md → CONFIGURATION.md
集成开发者          →    api.md → 架构设计
运维/部署           →    deployment.md
源码阅读者          →    architecture.md → 模块详解
```

| 角色 | 推荐阅读路径 |
|------|-------------|
| **新用户** | README → [快速上手](docs/QUICKSTART.md) → 本地启动 |
| **API 集成** | [API 文档](docs/api.md) → 调用示例 |
| **部署运维** | [配置说明](docs/CONFIGURATION.md) → [部署指南](docs/deployment.md) |
| **架构理解** | [架构设计](docs/architecture.md) → 模块详解 |
| **二次开发** | `devfile/README.md` → `devfile/01-current-state.md` → `devfile/02-target-architecture.md` |
| **推进项目** | `devfile/00-master-plan.md` → `devfile/03-execution-roadmap.md` → `devfile/07-completed-history.md` |

---

## 功能演示

### 1. 自然语言查询

```
用户输入: "上个月销售额最高的前5个产品是什么？"
    ↓
生成 SQL: SELECT p.product_name, SUM(oi.quantity * oi.unit_price) as total_sales 
          FROM products p JOIN order_items oi ON p.product_id = oi.product_id 
          WHERE strftime('%Y-%m', o.order_date) = '2026-02' 
          GROUP BY p.product_name ORDER BY total_sales DESC LIMIT 5
    ↓
执行结果: [{"product_name": "iPhone 15", "total_sales": 150000}, ...]
```

### 2. 智能图表推荐

```
数据特征: 分类(product_name) + 数值(total_sales)
    ↓
推荐图表: 柱状图 (confidence: 0.92)
    ↓
渲染: Plotly 交互式图表
```

### 3. 安全校验

```
恶意输入: "删除所有订单"
    ↓
校验拦截: "Only SELECT statements are allowed in readonly mode."
```

---

## 核心功能

| 功能 | 说明 | 源码位置 |
|------|------|----------|
| 🗣️ 自然语言转SQL | 本地规则 + 分类 + 模板 SQL + 可选 LLM | `app/core/llm/` `app/core/sql/` `app/core/nlu/` |
| 🔍 Schema 检索 | 本地 schema context + 向量检索 | `app/core/retrieval/` |
| 📊 图表推荐 | 自动识别数据类型推荐 | `app/core/chart/` |
| 🔒 安全校验 | 注入防护 + 表白名单 | `app/core/sql/guard.py` |
| 🔌 多数据库 | SQLite/MySQL/PostgreSQL | `app/core/sql/database.py` |

---

## 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **本地语义层** | 规则分类 / 模板 SQL | - | 主链路优先执行 |
| **LLM** | 百炼/OpenAI | - | 关键自然语言理解补充 |
| **向量库** | ChromaDB | 1.0+ | Schema RAG 存储 |
| **后端** | FastAPI | 0.115+ | REST API |
| | SQLAlchemy | 2.0+ | 数据库抽象 |
| **前端** | Streamlit | 1.32+ | Web UI |
| **可视化** | Plotly | 5.18+ | 交互式图表 |

---

## 快速启动

### 前置条件

- Python 3.11+
- pip 最新版
- （可选）Docker

### 3 步启动

```bash
# 1. 进入项目
cd /path/to/text2sql-agent

# 2. 安装 + 配置
pip install -r requirements.txt
cp .env.example .env && nano .env  # 填入 LLM_API_KEY

# 3. 初始化 + 启动
python scripts/init_demo_db.py
streamlit run app/ui/streamlit_app.py
```

访问：http://localhost:8501

> 详细步骤见 [QUICKSTART.md](docs/QUICKSTART.md)

### Docker 一键启动

```bash
docker-compose up -d combined
# UI: http://localhost:8501
# API: http://localhost:8000/docs
```

---

## API 快览

### POST /ask

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "各城市订单数量"}'
```

**响应**：

```json
{
  "success": true,
  "generated_sql": "SELECT city, COUNT(*) AS order_count FROM orders GROUP BY city LIMIT 10",
  "mode": "fallback",
  "result_preview": [{"city": "北京", "order_count": 150}],
  "chart": {"chart_type": "bar", "x_column": "city", "y_column": "order_count"}
}
```

> 完整 API 见 [api.md](docs/api.md)

---

## 项目结构

```
text2sql-agent/
├── app/
│   ├── presentation/        # 新入口层：API、UI 适配
│   ├── application/         # 新应用层：编排、用例、会话、actions
│   ├── domain/              # 新领域层：查询、治理、会话、可视化对象
│   ├── infrastructure/      # 新基础设施层：LLM、检索、执行、存储、安全、观测
│   ├── core/                # 过渡区：旧实现仍在逐步迁移
│   ├── shared/              # 共享 schemas / types / utils
│   └── config/              # 配置管理
│
├── data/                    # Demo 数据（入 git）
│   ├── demo_db/            # SQLite Demo 数据库
│   └── ddl/                # 表结构定义
│
├── .deploy/                 # 运行时数据（不入 git）
│   ├── chroma/             # ChromaDB 向量数据
│   ├── logs/               # 应用日志
│   └── db/                 # 运行时数据库
│
├── datasets/                # 测试数据集（不入 git）
│
├── scripts/                # 初始化、验证和运维脚本
│
├── tests/                  # 测试用例
├── docs/                   # 当前运行态文档（使用、配置、API、部署）
└── devfile/                # 规划文档（现状、目标架构、路线图、归档）
```

---

## 配置要点

**最小配置**（`.env`）：

```bash
LLM_PROVIDER=bailian_code_plan
LLM_API_KEY=你的API密钥  # 仅复杂问题补充理解时需要
```

**安全配置**：

```bash
READONLY_MODE=true              # 仅允许 SELECT
SQL_MAX_ROWS=200                # 最大返回行数
ALLOWED_TABLES=orders,products  # 表白名单
```

> 完整配置见 [CONFIGURATION.md](docs/CONFIGURATION.md)

---

## 文档索引

| 文档 | 内容 | 适合谁 |
|------|------|--------|
| [QUICKSTART.md](docs/QUICKSTART.md) | 15分钟跑通 | 新用户 |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | 环境变量详解 | 使用者/运维 |
| [api.md](docs/api.md) | API 端点 + 示例 | 集成开发者 |
| [architecture.md](docs/architecture.md) | 架构设计 + 扩展点 | 架构师/开发者 |
| [deployment.md](docs/deployment.md) | 部署运维 | 运维人员 |

---

## 测试

```bash
# 运行全部测试
pytest tests/ -v

# 测试覆盖
pytest tests/ --cov=app --cov-report=html
```

**当前状态**：
- 测试：265 passed, 2 skipped
- 覆盖率：80%
- Docker：combined 模式已通过
- 可观测性：`/metrics` 端点可用
- 认证：API Key 中间件已集成（默认禁用）
- 结论：工程化收口完成，可交付

---

## 开发进度

| 阶段 | 任务 | 状态 |
|------|------|------|
| W1 | MVP 基础（本地查询链路 + Streamlit） | ✅ |
| W2 | MySQL 支持 + 安全校验 | ✅ |
| W3 | 智能图表 + 导出功能 | ✅ |
| W4 | 生产就绪（Docker + API + 文档） | ✅ |

---

## 扩展点

| 扩展方向 | 入口文件 | 参考文档 |
|----------|----------|----------|
| 新增 LLM Provider | `app/core/llm/adapters.py` | architecture.md#扩展点 |
| 新增数据库类型 | `app/core/sql/connectors/` | architecture.md#扩展点 |
| 新增图表类型 | `app/core/chart/recommender.py` | architecture.md#扩展点 |

---

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| LLM 调用失败 | 检查 `LLM_API_KEY` 配置 |
| 数据库连接失败 | 检查 `DB_URL` 路径 |
| ChromaDB 错误 | 运行 `python scripts/ingest_schema.py` |

> 详细排查见 [deployment.md](docs/deployment.md#故障排查)

---

## License

MIT License