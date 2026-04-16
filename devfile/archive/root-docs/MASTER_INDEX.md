# Text2SQL Agent 项目主索引

> **目的**：整合所有方案与步骤清单，避免上下文丢失。后续项目构建以此文档为准。

---

## 1. 项目概述

### 1.1 核心目标
构建一个**可展示的技术作品**，证明在 BI+AI 领域的开发能力，用于求职展示。

### 1.2 核心功能
| 优先级 | 功能 | 说明 |
|--------|------|------|
| P0 | 自然语言转SQL | 用户用中文提问，系统生成SQL |
| P0 | SQL执行+结果展示 | 安全执行查询，展示表格数据 |
| P0 | 多数据库支持 | SQLite(Demo)/MySQL/PostgreSQL |
| P1 | 智能图表推荐 | 根据数据特征推荐柱状图/折线图/饼图 |
| P1 | 安全校验 | SQL注入防护、只读权限、敏感字段过滤 |
| P2 | SQL解释器 | 用自然语言解释SQL含义 |
| P2 | 追问澄清 | 模糊问题主动追问 |
| P2 | 查询历史学习 | 记录用户修正，持续优化 |

### 1.3 技术栈
| 层级 | 技术 | 说明 |
|------|------|------|
| LLM层 | Vanna AI + 百炼Code Plan | 主创新点 |
| Agent框架 | LangGraph / Vanna | 状态机+多Agent协作 |
| SQL引擎 | SQLAlchemy | 支持多种数据库后端 |
| 向量检索 | ChromaDB | RAG存储Schema和示例SQL |
| 前端 | Streamlit | 快速构建Demo界面 |
| 可视化 | Plotly | 交互式图表 |
| 数据库 | SQLite/MySQL | SQLite用于Demo，MySQL用于生产 |

---

## 2. 参考文档索引

### 2.1 工作区文档路径
| 文档 | 路径 | 内容 |
|------|------|------|
| 技术调研报告 | `outputs/project-1-text2sql.md` | 技术可行性、参考项目、差异化建议 |
| 6周开发计划 | `outputs/text2sql-dev-plan.md` | 详细里程碑、任务拆解、验收标准 |
| LLM适配器设计 | `outputs/text2sql-llm-adapter-design.md` | 多Provider支持、Fallback策略 |
| 百炼Code Plan调研 | `outputs/bailian-codeplan-research.md` | 百炼平台特性研究 |
| Vanna适配研究 | `outputs/vanna-llm-adapter-research.md` | Vanna框架集成方案 |

### 2.2 已有项目目录
| 项目 | 路径 | 状态 |
|------|------|------|
| text2sql-agent | `projects/text2sql-agent/` | 基础版本，有骨架代码 |
| dify-text2sql-agent | `projects/dify-text2sql-agent/` | 详细文档版本 |

---

## 3. 项目目录结构

```
text2sql-agent/
├── app/
│   ├── api/                 # FastAPI 接口层
│   │   ├── main.py
│   │   └── routes/
│   ├── ui/                  # Streamlit 界面
│   │   └── streamlit_app.py
│   ├── core/                # 核心业务逻辑
│   │   ├── orchestrator/    # 流程编排
│   │   ├── llm/             # LLM适配器
│   │   ├── retrieval/       # Schema检索(RAG)
│   │   ├── sql/             # SQL生成/校验/执行
│   │   ├── chart/           # 图表推荐
│   │   ├── memory/          # 查询历史
│   │   └── explain/         # SQL解释器
│   ├── config/              # 配置管理
│   └── shared/              # 公共类型
├── data/
│   ├── demo_db/             # SQLite Demo数据库
│   ├── ddl/                 # 表结构定义
│   └── examples/            # 示例SQL
├── scripts/
│   ├── init_demo_db.py      # 初始化Demo数据库
│   └── ingest_schema.py     # 导入Schema到向量库
├── tests/
│   ├── unit/
│   └── integration/
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 4. 开发里程碑（4周精简版）

### Week 1: MVP基础
- [x] W1-01: 初始化项目结构
- [x] W1-02: 创建SQLite销售数据库（产品、订单、客户表）
- [x] W1-03: 集成Vanna AI核心
- [x] W1-04: 实现统一LLM适配器（Code Plan + OpenAI）
- [x] W1-05: 开发Streamlit基础界面
- [x] W1-06: 实现fallback机制

**验收**: 本地运行，输入问题返回SQL+结果

### Week 2: MySQL支持+安全校验
- [x] W2-01: 数据库抽象层设计
- [x] W2-02: MySQL连接器实现
- [x] W2-03: SQL注入防护
- [x] W2-04: 权限控制系统（只读）
- [x] W2-05: 多数据库切换测试

**验收**: MySQL连接成功，安全校验通过

### Week 3: 可视化增强
- [x] W3-01: 数据类型分析器
- [x] W3-02: 图表推荐算法
- [x] W3-03: Plotly图表渲染（已完成，支持柱状图/折线图/饼图/散点图）
- [x] W3-04: PDF/Excel导出（已完成）

**验收**: ✅ 智能图表推荐可用，支持交互式可视化与导出

### Week 4: 生产就绪
- [x] W4-01: FastAPI服务（已完成，POST/GET /ask, /health, /schemas）
- [x] W4-02: Docker容器化（已完成，Dockerfile + docker-compose.yml + entrypoint）
- [x] W4-03: 完整文档（已完成，README + architecture.md + api.md + deployment.md）
- [x] W4-04: 测试覆盖率>80%（已完成，109 passed）

**验收**: ✅ 全部完成，项目可交付

---

## 5. LLM适配层设计

### 5.1 Provider优先级
```
bailian_code_plan (主) → dashscope → openai → deepseek → local_fallback
```

### 5.2 配置项
```bash
LLM_PROVIDER=bailian_code_plan
LLM_MODEL=glm-5
LLM_BASE_URL=https://coding.dashscope.aliyuncs.com/v1
LLM_API_KEY=

BAILIAN_CODEPLAN_API_KEY=
BAILIAN_CODEPLAN_MODEL=glm-5

LLM_FALLBACK_CHAIN=dashscope,openai,deepseek,local_fallback
```

### 5.3 接口规范
```python
class LLMAdapter(Protocol):
    def generate_sql(self, question: str, *, ddl: str = None) -> str
    def healthcheck(self) -> dict
```

---

## 6. 安全校验规则

### 6.1 SQL白名单
- 仅允许 `SELECT` 语句
- 禁止 `INSERT/UPDATE/DELETE/DROP/ALTER/CREATE`
- 强制 `LIMIT` 上限

### 6.2 权限控制
- 数据库连接使用只读账号
- 表级别白名单
- 敏感字段过滤

### 6.3 查询限制
- 超时时间: 15秒
- 最大返回行数: 200行
- JOIN数量限制: 3表

---

## 7. 接口设计

### POST /ask
```json
// 请求
{
  "question": "上个月销售额最高的前5个产品是什么？",
  "session_id": "demo-user-001"
}

// 响应
{
  "generated_sql": "SELECT ...",
  "sql_explanation": "这条SQL按月份筛选后统计...",
  "result_preview": [...],
  "chart": {"type": "bar", "x": "product", "y": "sales"},
  "summary": "上个月销售额最高的是A产品。"
}
```

### GET /health
- 返回服务与数据库连接状态

---

## 8. 演示场景

### 场景1: TopN销售分析
> "上个月销售额最高的前5个产品是什么？"
展示: SQL生成 → 执行 → 柱状图 → 解释

### 场景2: 城市对比分析
> "对比一下北京和上海各季度的订单量变化"
展示: 多表JOIN → 折线图 → 总结

### 场景3: 模糊问题澄清
> "查询用户数据"
展示: 追问澄清 → 精确查询

---

## 9. 依赖清单

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
```

---

## 10. 快速启动命令

```bash
# 初始化
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 初始化数据库
python scripts/init_demo_db.py
python scripts/ingest_schema.py

# 启动Demo
streamlit run app/ui/streamlit_app.py

# Docker启动
docker-compose up -d
```

---

## 11. 质量标准

| 指标 | 要求 |
|------|------|
| 代码覆盖率 | > 80% |
| 响应时间 | < 3秒 |
| Demo启动时间 | < 5分钟 |
| 文档完整度 | 100% |

---

## 12. 更新记录

| 日期 | 更新内容 |
|------|----------|
| 2026-03-20 | W4-01 FastAPI服务完成，80 passed |
| 2026-03-20 | W3-03 Plotly图表渲染完成，W3-04 PDF/Excel导出完成，Week 3 100% |
| 2026-03-19 | W3-02 图表推荐算法完成，102 passed |
| 2026-03-19 | W3-01 数据类型分析器完成，79 passed |
| 2026-03-19 | 修复测试：SQLAlchemy 2.x API适配 + SQLite语法兼容 |
| 2026-03-18 | 创建主索引文档，整合所有方案与步骤清单 |

---

**此文档为项目唯一索引，后续开发以此为准，避免上下文丢失。**