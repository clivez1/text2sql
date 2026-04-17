# 配置说明

> 完整的环境变量配置指南

## 目录

- [配置加载流程](#配置加载流程)
- [环境变量清单](#环境变量清单)
- [LLM Provider 配置](#llm-provider-配置)
- [数据库配置](#数据库配置)
- [向量数据库配置](#向量数据库配置)
- [安全配置](#安全配置)
- [功能开关](#功能开关)
- [配置示例](#配置示例)
- [常见问题](#常见问题)

---

## 配置加载流程

### 加载顺序

```
启动应用
    ↓
load_dotenv() 加载 .env 文件
    ↓
Settings 类读取环境变量
    ↓
get_provider_config() 解析 Provider 配置
    ↓
各模块通过 get_settings() 获取配置
```

### 源码位置

**配置模块**：`app/config/settings.py`

```python
# settings.py 核心结构

@dataclass(frozen=True)
class Settings:
    """应用配置类
    
    所有配置项在类定义时从环境变量读取。
    使用 dataclass(frozen=True) 确保配置不可变。
    """
    app_env: str = os.getenv("APP_ENV", "dev")
    # ... 其他配置项
```

**加载入口**：

```python
from dotenv import load_dotenv
load_dotenv()  # 启动时执行，加载 .env 文件
```

---

## 环境变量清单

### 完整变量表

| 变量名 | 类型 | 默认值 | 必填 | 说明 |
|--------|------|--------|------|------|
| `APP_ENV` | string | `dev` | 否 | 运行环境 |
| `APP_HOST` | string | `0.0.0.0` | 否 | API 监听地址 |
| `APP_PORT` | int | `8000` | 否 | API 端口 |
| `LLM_API_KEY_N` | string | - | 是* | LLM API 密钥（N=1,2,3...），支持多 Provider 级联 |
| `LLM_BASE_URL_N` | string | - | 否 | LLM API 地址（对应 LLM_API_KEY_N） |
| `LLM_MODEL_N` | string | - | 否 | 模型名称（对应 LLM_API_KEY_N） |
| `DB_TYPE` | string | `sqlite` | 否 | 数据库类型 |
| `DB_URL` | string | `sqlite:///data/demo_db/sales.db` | 否 | 数据库连接串 |
| `VECTOR_DB_PATH` | string | `./.deploy/chroma` | 否 | 向量库路径 |
| `READONLY_MODE` | bool | `true` | 否 | 只读模式 |
| `SQL_MAX_ROWS` | int | `200` | 否 | 最大返回行数 |
| `SQL_QUERY_TIMEOUT` | int | `15` | 否 | 查询超时(秒) |
| `ALLOWED_TABLES` | string | `orders,products,...` | 否 | 表白名单 |
| `API_KEY_ENABLED` | bool | `false` | 否 | 启用 API Key 认证 |
| `API_KEYS` | string | - | 否 | 有效 API Key 列表（逗号分隔）|
| `API_KEY_HEADER` | string | `X-API-Key` | 否 | API Key 请求头名称 |

> *`LLM_API_KEY_1`（或向后兼容的 `LLM_API_KEY`）对复杂问题的 LLM 补充理解是必需项；但在测试/本地优先模式下，不再是主链路必填项。Provider 类型由 `LLM_BASE_URL_N` 自动检测，无需手动指定。

---

## LLM Provider 配置

### N-Provider 级联架构

系统支持配置多个 LLM Provider，按优先级自动级联。当 Provider 1 失败时，自动尝试 Provider 2，以此类推。

```
                    LLM 调用请求
                         │
                         ▼
              ┌─────────────────────┐
              │   Provider 1        │
              │ (LLM_API_KEY_1)     │
              └──────────┬──────────┘
                         │ 失败
                         ▼
              ┌─────────────────────┐
              │   Provider 2        │
              │ (LLM_API_KEY_2)     │
              └──────────┬──────────┘
                         │ 失败
                         ▼
                         ...
                         │ 全部失败
                         ▼
              ┌─────────────────────┐
              │   规则匹配 Fallback  │
              └─────────────────────┘
```

### 配置方式

所有 Provider 统一使用 OpenAI 兼容协议，通过 `LLM_BASE_URL_N` 自动检测 API 类型。

**单 Provider 配置**：

```bash
# 方式 1：使用无后缀变量（向后兼容）
LLM_API_KEY=sk-xxxxxxxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

# 方式 2：使用 _1 后缀（推荐）
LLM_API_KEY_1=sk-xxxxxxxx
LLM_BASE_URL_1=https://api.openai.com/v1
LLM_MODEL_1=gpt-4o-mini
```

**多 Provider 级联配置**：

```bash
# Provider 1：主服务（OpenAI）
LLM_API_KEY_1=sk-xxxxxxxx
LLM_BASE_URL_1=https://api.openai.com/v1
LLM_MODEL_1=gpt-4o-mini

# Provider 2：备用服务（DeepSeek）
LLM_API_KEY_2=sk-xxxxxxxx
LLM_BASE_URL_2=https://api.deepseek.com/v1
LLM_MODEL_2=deepseek-chat

# Provider 3：备用服务（百炼）
LLM_API_KEY_3=sk-xxxxxxxx
LLM_BASE_URL_3=https://coding.dashscope.aliyuncs.com/v1
LLM_MODEL_3=qwen-turbo
```

**配置规则**：
- 索引从 1 开始，连续编号（1, 2, 3...）
- 遇到第一个空缺即停止扫描
- `LLM_API_KEY` 等价于 `LLM_API_KEY_1`（向后兼容）
- Provider 类型由 `LLM_BASE_URL_N` 自动检测，无需手动指定

### 常用 Provider 示例

**OpenAI**：

```bash
LLM_API_KEY_1=sk-xxxxxxxx
LLM_BASE_URL_1=https://api.openai.com/v1
LLM_MODEL_1=gpt-4o-mini
```

**DeepSeek**：

```bash
LLM_API_KEY_1=sk-xxxxxxxx
LLM_BASE_URL_1=https://api.deepseek.com/v1
LLM_MODEL_1=deepseek-chat
```

**阿里百炼**：

```bash
LLM_API_KEY_1=sk-xxxxxxxx
LLM_BASE_URL_1=https://coding.dashscope.aliyuncs.com/v1
LLM_MODEL_1=qwen-turbo
```

**Moonshot**：

```bash
LLM_API_KEY_1=sk-xxxxxxxx
LLM_BASE_URL_1=https://api.moonshot.cn/v1
LLM_MODEL_1=moonshot-v1-8k
```

### 源码引用

**适配器**（`adapters.py`）：

```python
@dataclass(frozen=True)
class OpenAICompatibleAdapter:
    config: LLMProviderConfig

    @property
    def provider_name(self) -> str:
        return self.config.provider

    def generate_sql(self, question: str, schema_context: str | None = None) -> str:
        """Generate SQL from a natural language question using OpenAI chat completion."""
        client = self._build_client()
        # ... 调用 OpenAI API
```

**配置解析**（`settings.py`）：

```python
def get_provider_config(self, index: int = 1) -> LLMProviderConfig:
    """Get provider config. index is 1-based."""
    if index < 1 or index > len(self._llm_providers):
        raise ValueError(
            f"Provider index {index} out of range (1-{len(self._llm_providers)})"
        )
    return self._llm_providers[index - 1]
```

### Fallback 机制

当 LLM 调用失败时，系统自动级联到下一个 Provider，全部失败后 fallback 到规则匹配：

```
Provider 1 → timeout → Provider 2 → error → ... → Provider N → 规则匹配
```

**调用链**（源码：`client.py`）：

```python
def generate_sql(question: str) -> tuple[str, str, str, str | None]:
    """SQL 生成入口
    
    调用链：
    1. 尝试 Provider 1 生成
    2. 失败则尝试 Provider 2, 3, ...
    3. 全部失败则 fallback 到规则匹配
    4. 规则未命中则返回默认 SQL
    """
    try:
        adapter = get_llm_adapter()
        sql = adapter.generate_sql(question)
        return sql, explanation, adapter.provider_name, None
    except Exception as exc:
        # 所有 Provider 失败，fallback 到规则匹配
        blocked_reason = f"LLM runtime failed: {exc}"
        sql, explanation = generate_sql_by_rules(question)
        return sql, explanation, "fallback", blocked_reason
```

---

## 数据库配置

### SQLite（Demo/开发）

```bash
DB_TYPE=sqlite
DB_URL=sqlite:///data/demo_db/sales.db
```

**路径说明**：
- `sqlite:///` 后接相对路径（相对于项目根目录）
- `sqlite:////` 后接绝对路径（注意 4 个斜杠）

**源码引用**（`database.py`）：

```python
class SQLiteConnector(DatabaseConnector):
    """SQLite 连接器
    
    特点：
    - 无需额外服务，文件即数据库
    - 支持只读模式（通过 URI 参数）
    - 适合 Demo 和开发环境
    """
    
    def _create_engine(self) -> Engine:
        url = self.config.db_url
        # 只读模式：添加 ?mode=ro&uri=true
        if self.config.readonly and "mode=" not in url:
            url = url.replace("sqlite:///", "sqlite:///file:") + "?mode=ro&uri=true"
        return create_engine(url)
```

### MySQL（生产环境）

```bash
# 方式 1：完整连接串
DB_TYPE=mysql
DB_URL=mysql+pymysql://user:password@host:3306/database

# 方式 2：分离变量（适合容器环境）
MYSQL_HOST=db.internal
MYSQL_PORT=3306
MYSQL_USER=text2sql
MYSQL_PASSWORD=secret
MYSQL_DATABASE=sales
```

**连接串格式**：

```
mysql+pymysql://[用户名]:[密码]@[主机]:[端口]/[数据库]?[参数]
```

**推荐参数**：
- `charset=utf8mb4` - 支持中文
- `ssl=true` - 启用 SSL

**源码引用**（`database.py`）：

```python
class MySQLConnector(DatabaseConnector):
    """MySQL 连接器
    
    特点：
    - 使用 PyMySQL 驱动
    - 支持连接池
    - 生产环境推荐
    """
    
    def _create_engine(self) -> Engine:
        return create_engine(
            self.config.db_url,
            pool_pre_ping=True,    # 连接前检查存活
            pool_recycle=3600,     # 1小时回收连接
            connect_args={"connect_timeout": 10}
        )
```

### PostgreSQL

```bash
DB_TYPE=postgresql
DB_URL=postgresql://user:password@host:5432/database

# 或使用 psycopg2 驱动
DB_URL=postgresql+psycopg2://user:password@host:5432/database
```

### 数据库切换流程

```
应用启动
    ↓
读取 DB_URL 环境变量
    ↓
_detect_db_type() 识别数据库类型
    ↓
工厂方法 create_database_connector() 创建对应连接器
    ↓
SQLiteConnector / MySQLConnector / PostgreSQLConnector
```

---

## 向量数据库配置

### ChromaDB 配置

```bash
VECTOR_DB_PATH=./.deploy/chroma
```

**目录结构**：

```
.deploy/chroma/
├── chroma.sqlite3           # 主数据库文件
├── schema_store/            # Schema 向量存储
│   ├── chroma.sqlite3
│   └── <uuid>/              # 向量索引
└── <collection-id>/         # 其他 collection
```

### 初始化向量库

```bash
python scripts/ingest_schema.py
```

**执行流程**（源码：`ingest_schema.py`）：

```python
def main() -> None:
    # 1. 创建 ChromaDB 客户端
    client = chromadb.PersistentClient(path=str(settings_path))
    
    # 2. 创建/重建 collection
    collection = client.create_collection("schema_docs")
    
    # 3. 导入文档
    documents = []
    # - DDL 定义
    # - 表字段说明
    # - 示例 SQL
    collection.add(ids=ids, documents=documents, metadatas=metadatas)
```

**导入内容**：

| 类型 | 来源 | 用途 |
|------|------|------|
| DDL | `data/ddl/sales_schema.sql` | 表结构定义 |
| 字段说明 | `FIELD_DOCS` 字典 | 字段业务含义 |
| 示例 SQL | `EXAMPLE_SQL` 字典 | Few-shot 学习 |

---

## 安全配置

### 查询限制

| 变量 | 默认值 | 影响范围 |
|------|--------|----------|
| `READONLY_MODE` | `true` | 仅允许 SELECT 语句 |
| `SQL_MAX_ROWS` | `200` | 强制 LIMIT 上限 |
| `SQL_QUERY_TIMEOUT` | `15` | PostgreSQL 超时设置 |

### 只读模式

```bash
READONLY_MODE=true
```

**生效逻辑**（源码：`guard.py`）：

```python
def validate(self, sql: str) -> SQLValidationResult:
    # 只读模式检查
    if self.readonly and not lowered.startswith("select"):
        return SQLValidationResult(
            is_valid=False,
            error="Only SELECT statements are allowed in readonly mode."
        )
```

**SQLite 只读连接**（源码：`database.py`）：

```python
# SQLite 通过 URI 参数实现只读
url = url.replace("sqlite:///", "sqlite:///file:") + "?mode=ro&uri=true"
```

### 表白名单

```bash
ALLOWED_TABLES=orders,products,order_items,customers
```

**校验逻辑**（源码：`guard.py`）：

```python
def _extract_tables(self, sql: str) -> Set[str]:
    """从 SQL 中提取表名"""
    tables = set()
    for match in TABLE_PATTERN.finditer(sql):
        tables.add(match.group(1).lower())
    return tables

# 校验：查询的表必须在白名单内
forbidden_tables = tables - self.allowed_tables
if forbidden_tables:
    return SQLValidationResult(
        is_valid=False,
        error=f"Access denied to tables: {sorted(forbidden_tables)}"
    )
```

### 危险关键字拦截

**拦截列表**（源码：`guard.py`）：

```python
FORBIDDEN_KEYWORDS = {
    "insert", "update", "delete", "drop", "alter", "truncate",
    "create", "replace", "attach", "pragma", "vacuum", "exec",
    "execute", "xp_", "sp_", "into outfile", "load_file",
}
```

---

---

## API Key 认证

### 启用认证

```bash
API_KEY_ENABLED=true
API_KEYS=your-secret-key-1,your-secret-key-2
API_KEY_HEADER=X-API-Key
```

### 认证规则

| 端点 | 认证要求 |
|------|----------|
| `/health` | 公开 |
| `/metrics` | 公开 |
| `/docs` | 公开 |
| `/ask` | 需要 API Key |
| `/schemas` | 需要 API Key |

### 使用方式

```bash
# 带 API Key 的请求
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"question": "查询所有订单"}'
```

### 生成 API Key

```python
from app.core.auth.api_key import generate_api_key
print(generate_api_key())
```

## 功能开关

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENABLE_HISTORY` | `true` | 记录查询历史 |
| `ENABLE_CHART` | `true` | 智能图表推荐 |
| `ENABLE_CLARIFICATION` | `false` | 模糊问题追问 |

---

## 配置示例

### 开发环境

```bash
# .env - 开发环境

# 应用配置
APP_ENV=dev
APP_HOST=0.0.0.0
APP_PORT=8000

# LLM 配置（单 Provider）
LLM_API_KEY_1=sk-your-dev-key
LLM_BASE_URL_1=https://api.openai.com/v1
LLM_MODEL_1=gpt-4o-mini

# 数据库
DB_URL=sqlite:///data/demo_db/sales.db
VECTOR_DB_PATH=./.deploy/chroma

# 安全
READONLY_MODE=true
SQL_MAX_ROWS=200
```

### 生产环境

```bash
# .env - 生产环境

# 应用配置
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000

# LLM 配置（多 Provider 级联）
LLM_API_KEY_1=${OPENAI_API_KEY}
LLM_BASE_URL_1=https://api.openai.com/v1
LLM_MODEL_1=gpt-4o-mini

LLM_API_KEY_2=${DEEPSEEK_API_KEY}
LLM_BASE_URL_2=https://api.deepseek.com/v1
LLM_MODEL_2=deepseek-chat

# 数据库（MySQL）
DB_URL=mysql+pymysql://text2sql:${DB_PASSWORD}@db.internal:3306/sales
VECTOR_DB_PATH=./.deploy/chroma

# 安全
READONLY_MODE=true
SQL_MAX_ROWS=500
SQL_QUERY_TIMEOUT=30
ALLOWED_TABLES=orders,products,order_items,customers
```

---

## 常见问题

### Q1: 配置不生效

**排查步骤**：

```bash
# 1. 确认 .env 文件位置
ls -la .env

# 2. 检查环境变量是否加载
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('LLM_API_KEY_1'))"

# 3. 检查配置类
python -c "from app.config.settings import get_settings; s=get_settings(); print(s.provider_count)"
```

### Q2: LLM 调用失败

**检查清单**：
1. `LLM_API_KEY_1` 是否正确
2. `LLM_BASE_URL_1` 是否可达
3. 模型名称是否正确
4. 网络是否有代理

### Q3: 数据库连接失败

**SQLite**：
```bash
# 检查文件是否存在
ls -la data/demo_db/sales.db

# 检查文件权限
chmod 644 data/demo_db/sales.db
```

**MySQL**：
```bash
# 测试连接
mysql -h host -u user -p -e "SELECT 1"
```

---

## 更新记录

| 日期 | 更新内容 |
|------|----------|
| 2026-04-17 | Round 6: N-Provider Fallback, 移除 Vanna, 移除 USE_GENERATE_SQL_V2 |
| 2026-03-22 | 细化配置说明，添加源码引用和流程图 |
| 2026-03-22 | 创建配置说明文档 |