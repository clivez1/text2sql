# 快速上手指南

> 15 分钟跑通 Text2SQL Agent 核心流程

## 目录

- [前置条件](#前置条件)
- [安装步骤](#安装步骤)
- [验证功能](#验证功能)
- [Docker 快速部署](#docker-快速部署)
  - [一键启动](#一键启动推荐)
  - [Windows 下 Docker Desktop 测试部署](#windows-下-docker-desktop-测试部署)
- [常见问题](#常见问题)

---

## 前置条件

| 依赖 | 版本 | 检查命令 | 为什么需要 |
|------|------|----------|------------|
| Python | 3.11+ | `python3 --version` | 项目使用 3.11 特性 |
| pip | 最新 | `pip --version` | 依赖安装 |
| SQLite | 3.x | `sqlite3 --version` | Demo 数据库 |

---

## 安装步骤

### 第一步：获取项目

```bash
cd /path/to/text2sql-agent
```

### 第二步：配置环境变量

```bash
cp .env.example .env
nano .env  # 或使用任意编辑器
```

**最小配置**：

```bash
# 测试/本地优先模式下，可先不依赖有效 LLM Key
LLM_API_KEY_1=可留空或后续再配置
LLM_BASE_URL_1=https://api.openai.com/v1  # 或其他 OpenAI 兼容 API
```

**为什么这样配**：

| 变量 | 作用 | 不配置会怎样 |
|------|------|-------------|
| `LLM_API_KEY_1` | 复杂问题补充理解 | 简单/半结构化问题仍可走本地规则与模板 |
| `LLM_BASE_URL_1` | 指定 LLM API 地址 | 默认使用 OpenAI 兼容协议 |

---

### 第三步：安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**核心依赖**：

| 包 | 用途 |
|---|------|
| `openai` | LLM 调用（OpenAI 兼容协议） |
| `chromadb` | 向量数据库（Schema RAG） |
| `fastapi` | REST API |
| `streamlit` | Web UI |
| `plotly` | 交互式图表 |

---

### 第四步：初始化数据

```bash
python scripts/init_demo_db.py    # 创建 Demo 数据库
python scripts/ingest_schema.py   # 导入 Schema 到向量库
```

**为什么需要两步**：

| 脚本 | 产出 |
|------|------|
| `init_demo_db.py` | `data/demo_db/sales.db` (500订单+50商品) |
| `ingest_schema.py` | `.deploy/chroma/schema_store/` (向量索引) |

---

### 第五步：启动服务

```bash
# UI 模式
streamlit run app/ui/streamlit_app.py

# API 模式（另一个终端）
uvicorn app.api.main:app --reload --port 8000
```

**端口说明**：

| 端口 | 服务 | 访问地址 |
|------|------|----------|
| 8501 | Streamlit UI | http://localhost:8501 |
| 8000 | FastAPI | http://localhost:8000/docs |

---

## 验证功能

### 测试 1：健康检查

```bash
curl http://localhost:8000/health
```

**预期响应**（v3.0 新格式）：

```json
{
  "status": "ok",
  "db_type": "sqlite",
  "db_connected": true,
  "llm_available": false,
  "provider_count": 1,
  "latency_ms": 5.23,
  "timestamp": "2026-04-15T10:30:00"
}
```

### 测试 2：自然语言查询

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "各城市订单数量"}'
```

**预期响应**（v3.0 新格式，含图表推荐）：

```json
{
  "success": true,
  "question": "各城市订单数量",
  "generated_sql": "SELECT city, COUNT(*) AS order_count FROM orders GROUP BY city ORDER BY order_count DESC LIMIT 10",
  "mode": "fallback",
  "sql_explanation": "按城市统计订单量并排序 | pipeline_generate_ms=2.34 | pipeline_query_ms=15.67",
  "result_preview": [
    {"city": "北京", "order_count": 150},
    {"city": "上海", "order_count": 120}
  ],
  "row_count": 10,
  "chart": {
    "chart_type": "bar",
    "x_column": "city",
    "y_column": "order_count",
    "confidence": 0.92
  }
}
```

### 测试 3：YAML 规则匹配（v3.0 新特性）

项目内置 27 条 YAML 规则，支持关键词匹配：

```bash
# 测试规则匹配
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "订单总数"}'
```

**常用测试问题**：

| 问题 | 匹配规则 | 预期结果 |
|------|---------|---------|
| `各城市订单数量` | city + order_count | 按城市分组计数 |
| `订单总数` | order + count | COUNT(*) |
| `订单平均金额` | order + avg | AVG(total_amount) |
| `北京订单` | city=北京 | 筛选北京订单 |
| `最近订单` | order + recent | ORDER BY DESC LIMIT 10 |
| `商品类别` | product + category | 按类别分组 |

### 测试 4：图表推荐（v3.0 新特性）

```bash
# 测试图表推荐
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "商品类别统计"}'
```

响应中的 `chart` 字段会自动推荐合适的图表类型：
- `bar` - 分类数据对比
- `line` - 时间序列趋势
- `pie` - 占比分布
- `scatter` - 相关性分析
- `table` - 默认表格展示

### 测试 5：API 端点一览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | API 信息 |
| `/health` | GET | 健康检查（含 LLM 状态） |
| `/ask` | POST | 自然语言查询 |
| `/ask` | GET | 查询（URL 参数） |
| `/schemas` | GET | 数据库 Schema |
| `/metrics` | GET | 可观测性指标 |

---

## Docker 快速部署

### 一键启动（推荐）

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 LLM_API_KEY（可选）

# 启动 combined 模式（UI + API 同容器）
docker-compose up -d combined

# 初始化向量库（首次必需）
docker exec -it text2sql-combined python scripts/ingest_schema.py
```

### 访问服务

| 服务 | 地址 |
|------|------|
| Streamlit UI | http://localhost:8501 |
| FastAPI Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

### 分离模式（可选）

```bash
# 分别启动 UI 和 API
docker-compose up -d ui api
```

### Windows 下 Docker Desktop 测试部署

若你在 Windows 上使用 Docker Desktop（推荐启用 WSL2 集成），可按以下步骤进行本地部署测试。

**前置要求**：
- 已安装 Docker Desktop 并启用 WSL2 后端
- 已在 Docker Desktop 设置中开启对项目所在驱动器（如 D:\）的文件共享

**部署步骤**：

```powershell
# 1. 进入项目根目录
cd D:\AI\codeSpace\text2sql-0412

# 2. 清理旧容器（如有）
docker-compose down -v

# 3. 启动 combined 模式（UI + API 同容器）
docker-compose up -d combined

# 4. 查看启动日志
docker-compose logs -f combined
```

**验证访问**：

| 服务 | 地址 |
|------|------|
| Streamlit UI | http://localhost:8501 |
| FastAPI Docs | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |

**首次初始化数据**：

```powershell
# 初始化 Demo 数据库
docker exec -it text2sql-combined python scripts/init_demo_db.py

# 导入 Schema 到向量库
docker exec -it text2sql-combined python scripts/ingest_schema.py
```

**运行时数据与隐私数据说明**：

| 目录 | 用途 | 是否入 Git |
|------|------|-----------|
| `.deploy/` | 运行时数据（向量库、日志） | ❌ 不入 |
| `datasets/` | 高隐私测试数据 | ❌ 不入 |
| `data/` | Demo 演示数据 | ✅ 入 |

> ⚠️ **重要**：`.deploy/` 为运行时目录，容器重建时可能被覆盖。高隐私测试数据应放在 `datasets/` 或外部加密存储，并通过卷挂载映射到容器。

**常见问题排查**：

```powershell
# 查看容器日志
docker-compose logs -f combined

# 检查容器状态
docker ps -a

# 进入容器调试
docker exec -it text2sql-combined bash
```

---

## 常见问题

### Q1: ModuleNotFoundError

```bash
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Q2: LLM 调用失败（mode: fallback）

**这在测试阶段通常不是故障。**

说明：
- 简单问题本来就应优先走本地规则 / 模板
- 项目内置 27 条 YAML 规则，覆盖常见查询场景
- 只有复杂问题才需要 LLM 补充
- 若业务结果正确，`mode=fallback` 可视为主成功路径

只有在复杂问题明显理解失败时，再检查 `.env` 中 `LLM_API_KEY_1` 是否正确。

### Q3: 数据库不存在

```bash
python scripts/init_demo_db.py
```

### Q4: ChromaDB 错误

```bash
rm -rf .deploy/chroma/schema_store
python scripts/ingest_schema.py
```

### Q5: 端口占用

```bash
# Linux/macOS
lsof -i :8501
kill -9 <PID>

# Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

### Q6: Docker 容器内 ChromaDB 未初始化

```bash
docker exec -it text2sql-combined python scripts/ingest_schema.py
```

### Q7: SQL 被拦截（READONLY_MODE）

默认开启只读模式，仅允许 SELECT 语句：

```bash
# 如需关闭（不推荐生产环境）
READONLY_MODE=false
```

---

## 功能开关（v3.0）

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `READONLY_MODE` | `true` | 仅允许 SELECT 语句 |
| `SQL_MAX_ROWS` | `200` | 最大返回行数 |
| `ALLOWED_TABLES` | `orders,products,...` | 表白名单 |
| `API_KEY_ENABLED` | `false` | 启用 API Key 认证 |

---

## 下一步

| 目标 | 文档 |
|------|------|
| 完整配置 | [CONFIGURATION.md](CONFIGURATION.md) |
| API 集成 | [api.md](api.md) |
| 生产部署 | [deployment.md](deployment.md) |
| 架构设计 | [architecture.md](architecture.md) |

---

## 更新记录

| 日期 | 内容 |
|------|------|
| 2026-04-17 | 新增 Windows Docker Desktop 部署说明 |
| 2026-04-17 | Round 6: 移除 Vanna 依赖, N-Provider 配置更新 |
| 2026-04-15 | v3.0 大更新：YAML 规则、图表推荐、Docker 部署、新 API 格式 |
| 2026-04-11 | 工程化收口：覆盖率 80%、可观测性、认证骨架 |
| 2026-03-22 | 创建初版 |