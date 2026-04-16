# API 接口文档

> Text2SQL Agent REST API 完整参考

## 目录

- [基础信息](#基础信息)
- [接口列表](#接口列表)
- [调用流程](#调用流程)
- [接口详情](#接口详情)
  - [GET /](#get-)
  - [GET /health](#get-health)
  - [GET /schemas](#get-schemas)
  - [POST /ask](#post-ask)
  - [GET /ask](#get-ask)
- [数据模型](#数据模型)
- [错误处理](#错误处理)
- [调用示例](#调用示例)

---

## 基础信息

| 项目 | 值 |
|------|-----|
| Base URL | `http://localhost:8000` |
| Content-Type | `application/json` |
| API 版本 | `v3.0.0` |
| OpenAPI 文档 | `/docs` |
| ReDoc 文档 | `/redoc` |

**源码位置**：`app/api/main.py`

---

## 接口列表

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/` | API 基本信息 | 无 |
| GET | `/health` | 健康检查 | 无 |
| GET | `/schemas` | 获取数据库结构 | 无 |
| POST | `/ask` | 自然语言查询 | 无 |
| GET | `/ask` | 自然语言查询 (GET) | 无 |

---

## 调用流程

### /ask 接口调用流程

```
POST /ask
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  1. 参数校验 (AskRequest)                                │
│     - question: 必填                                     │
│     - session_id: 可选                                   │
│     - explain: 可选                                      │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  2. SQL 生成 (ask_question)                             │
│     ├── 本地分类 / 本地 schema context                   │
│     ├── 优先规则 SQL / 模板 SQL                         │
│     └── 仅复杂问题才尝试 LLM，失败则 fallback            │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  3. 安全校验 (validate_readonly_sql)                    │
│     - 仅允许 SELECT                                      │
│     - 表白名单检查                                       │
│     - 强制添加 LIMIT                                     │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  4. 执行查询 (run_query)                                │
│     - 连接数据库                                         │
│     - 执行 SQL                                          │
│     - 返回 DataFrame                                    │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  5. 图表推荐 (ChartRecommender)                         │
│     - 分析数据类型                                       │
│     - 推荐图表类型                                       │
│     - 计算置信度                                         │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  6. 构建响应 (AskResponse)                              │
│     - 组装所有结果                                       │
│     - 计算执行时间                                       │
└─────────────────────────────────────────────────────────┘
    │
    ▼
  返回 JSON
```

**源码引用**（`main.py`）：

```python
@app.post("/ask", response_model=AskResponse, tags=["Query"])
def ask(request: AskRequest) -> AskResponse:
    start_time = time.time()
    
    try:
        # 1. 执行查询（包含 SQL 生成 + 安全校验 + 执行）
        result = ask_question(request.question)
        
        # 2. 图表推荐
        df = pd.DataFrame(result.result_preview)
        if not df.empty:
            recommender = ChartRecommender()
            recommendation = recommender.recommend(df, request.question)
            chart_config = {...}
        
        # 3. 返回响应
        return create_ask_response(result, execution_time_ms, chart_config)
        
    except Exception as e:
        return AskResponse(success=False, error=str(e), ...)
```

---

## 接口详情

### GET /

获取 API 基本信息，用于快速验证服务是否运行。

**请求**：无

**响应**：

```json
{
  "name": "Text2SQL Agent API",
  "version": "3.0.0",
  "docs": "/docs",
  "endpoints": {
    "ask": "POST /ask",
    "health": "GET /health",
    "schemas": "GET /schemas"
  }
}
```

**源码引用**：

```python
@app.get("/", tags=["Root"])
def root() -> dict:
    return {
        "name": "Text2SQL Agent API",
        "version": "3.0.0",
        "docs": "/docs",
        "endpoints": {...}
    }
```

---

### GET /health

健康检查，用于监控和负载均衡器探测。

**请求**：无

**响应字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | `ok` 或 `error` |
| `db_type` | string | 数据库类型：`sqlite`/`mysql`/`postgresql` |
| `db_connected` | bool | 数据库连接是否成功 |
| `latency_ms` | float | 响应延迟（毫秒） |
| `version` | string | API 版本 |
| `timestamp` | string | 时间戳（ISO 格式） |

**响应示例**：

```json
{
  "status": "ok",
  "db_type": "sqlite",
  "db_connected": true,
  "latency_ms": 5.23,
  "version": "3.0",
  "timestamp": "2026-03-22T10:30:00"
}
```

**失败响应**：

```json
{
  "status": "error",
  "db_type": "mysql",
  "db_connected": false,
  "latency_ms": 1023.45,
  "version": "3.0",
  "timestamp": "2026-03-22T10:30:00"
}
```

**源码引用**：

```python
@app.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse:
    start_time = time.time()
    settings = get_settings()
    
    try:
        # 测试数据库连接
        engine = create_engine(settings.db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False
    
    latency_ms = (time.time() - start_time) * 1000
    
    return HealthResponse(
        status="ok" if db_connected else "error",
        db_connected=db_connected,
        latency_ms=round(latency_ms, 2),
        ...
    )
```

---

### GET /schemas

获取数据库表结构信息，用于前端展示或验证连接。

**请求**：无

**响应字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `tables` | object | 表名 → 列名列表的映射 |
| `ddl` | string | 简化的 DDL 描述 |

**响应示例**：

```json
{
  "tables": {
    "orders": ["order_id", "customer_name", "order_date", "city", "total_amount"],
    "products": ["product_id", "product_name", "category"],
    "order_items": ["order_item_id", "order_id", "product_id", "quantity", "unit_price"]
  },
  "ddl": "-- orders\n(order_id, customer_name, order_date, city, total_amount)\n\n-- products\n(product_id, product_name, category)\n\n-- order_items\n(order_item_id, order_id, product_id, quantity, unit_price)"
}
```

**源码引用**：

```python
@app.get("/schemas", response_model=SchemaResponse, tags=["Database"])
def get_schemas() -> SchemaResponse:
    engine = create_engine(settings.db_url)
    inspector = inspect(engine)
    
    tables = {}
    for table_name in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns(table_name)]
        tables[table_name] = columns
    
    return SchemaResponse(tables=tables, ddl=...)
```

---

### POST /ask

核心接口：自然语言查询。

**请求体**：

```json
{
  "question": "上个月销售额最高的前5个产品是什么？",
  "session_id": "user-001",
  "explain": true
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `question` | string | ✅ | - | 自然语言问题（中文） |
| `session_id` | string | ❌ | `null` | 会话 ID，预留多轮对话 |
| `explain` | bool | ❌ | `true` | 是否返回 SQL 解释 |

**请求校验**（源码：`schemas.py`）：

```python
class AskRequest(BaseModel):
    question: str = Field(..., description="自然语言问题")  # 必填
    session_id: Optional[str] = Field(None, description="会话ID")
    explain: bool = Field(True, description="是否返回 SQL 解释")
```

**响应字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 请求是否成功 |
| `question` | string | 用户原始问题 |
| `generated_sql` | string | 生成的 SQL 语句 |
| `mode` | string | 运行模式：`llm`/`fallback`/`error`；其中 `fallback` 是本地优先主路径 |
| `blocked_reason` | string? | 安全拦截原因（如有） |
| `sql_explanation` | string | SQL 业务含义解释 |
| `result_preview` | array | 查询结果（对象数组） |
| `row_count` | int | 结果行数 |
| `execution_time_ms` | float | 总执行时间（毫秒） |
| `chart` | object? | 图表推荐配置 |
| `error` | string? | 错误信息（如有） |

**mode 字段说明**：

| 值 | 含义 |
|-----|------|
| `llm` | 复杂问题由 LLM 补充生成 SQL |
| `fallback` | 使用本地规则 / 模板 SQL / fast-fallback 成功处理 |
| `error` | 发生错误，未执行查询 |

**chart 字段结构**：

```json
{
  "chart_type": "bar",
  "x_column": "product_name",
  "y_column": "total_sales",
  "y_columns": ["total_sales"],
  "color_column": null,
  "confidence": 0.85
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `chart_type` | string | 图表类型：`bar`/`line`/`pie`/`scatter`/`table` |
| `x_column` | string? | X 轴列名 |
| `y_column` | string? | Y 轴主列名 |
| `y_columns` | array | Y 轴所有列名 |
| `color_column` | string? | 颜色分组列 |
| `confidence` | float | 推荐置信度 (0-1) |

**成功响应示例**：

```json
{
  "success": true,
  "question": "上个月销售额最高的前5个产品是什么？",
  "generated_sql": "SELECT p.product_name, SUM(oi.quantity * oi.unit_price) as total_sales FROM products p JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id WHERE strftime('%Y-%m', o.order_date) = (SELECT strftime('%Y-%m', date(MAX(order_date), 'start of month', '-1 month')) FROM orders) GROUP BY p.product_name ORDER BY total_sales DESC LIMIT 5",
  "mode": "fallback",
  "blocked_reason": null,
  "sql_explanation": "统计上个月各产品销售额并取 Top5。",
  "result_preview": [
    {"product_name": "iPhone 15", "total_sales": 150000.00},
    {"product_name": "MacBook Pro", "total_sales": 120000.00},
    {"product_name": "iPad Air", "total_sales": 85000.00},
    {"product_name": "AirPods Pro", "total_sales": 62000.00},
    {"product_name": "Apple Watch", "total_sales": 48000.00}
  ],
  "row_count": 5,
  "execution_time_ms": 156.78,
  "chart": {
    "chart_type": "bar",
    "x_column": "product_name",
    "y_column": "total_sales",
    "y_columns": ["total_sales"],
    "color_column": null,
    "confidence": 0.92
  },
  "error": null
}
```

**Fallback 响应示例**（LLM 失败）：

```json
{
  "success": true,
  "question": "各城市的订单数量",
  "generated_sql": "SELECT city, COUNT(*) AS order_count FROM orders GROUP BY city ORDER BY order_count DESC LIMIT 10;",
  "mode": "fallback",
  "blocked_reason": "LLM runtime failed: API key missing",
  "sql_explanation": "按城市统计订单量并排序。",
  "result_preview": [
    {"city": "北京", "order_count": 150},
    {"city": "上海", "order_count": 120}
  ],
  ...
}
```

**错误响应示例**：

```json
{
  "success": false,
  "question": "删除所有订单",
  "generated_sql": "",
  "mode": "error",
  "blocked_reason": null,
  "sql_explanation": "",
  "result_preview": [],
  "row_count": 0,
  "execution_time_ms": 0,
  "chart": null,
  "error": "Only SELECT statements are allowed in readonly mode."
}
```

---

### GET /ask

GET 方式的查询接口，便于浏览器测试。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `question` | string | ✅ | 自然语言问题 |
| `session_id` | string | ❌ | 会话 ID |

**请求示例**：

```
GET /ask?question=各城市订单数量&session_id=test-001
```

**响应**：与 POST /ask 相同

**源码引用**：

```python
@app.get("/ask", response_model=AskResponse, tags=["Query"])
def ask_get(
    question: str = Query(..., description="自然语言问题"),
    session_id: Optional[str] = Query(None, description="会话ID"),
) -> AskResponse:
    return ask(AskRequest(question=question, session_id=session_id))
```

---

## 数据模型

### 请求模型

**AskRequest**（源码：`schemas.py`）

```python
class AskRequest(BaseModel):
    question: str           # 必填，自然语言问题
    session_id: Optional[str]  # 可选，会话 ID
    explain: bool = True    # 可选，是否解释 SQL
```

### 响应模型

**AskResponse**（源码：`schemas.py`）

```python
class AskResponse(BaseModel):
    success: bool           # 请求是否成功
    question: str           # 用户问题
    generated_sql: str      # 生成的 SQL
    mode: str               # 运行模式
    blocked_reason: Optional[str]  # 拦截原因
    sql_explanation: str    # SQL 解释
    result_preview: List[Dict[str, Any]]  # 查询结果
    row_count: int          # 结果行数
    execution_time_ms: float  # 执行时间
    chart: Optional[ChartConfig]  # 图表配置
    error: Optional[str]    # 错误信息
```

**HealthResponse**

```python
class HealthResponse(BaseModel):
    status: str             # ok / error
    db_type: str            # sqlite / mysql / postgresql
    db_connected: bool      # 数据库连接状态
    latency_ms: float       # 响应延迟
    version: str            # API 版本
    timestamp: str          # 时间戳
```

**SchemaResponse**

```python
class SchemaResponse(BaseModel):
    tables: Dict[str, List[str]]  # 表名 → 列名列表
    ddl: Optional[str]            # DDL 描述
```

---

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": "错误类型",
  "detail": "详细信息"
}
```

### HTTP 状态码

| 状态码 | 说明 | 常见原因 |
|--------|------|----------|
| `200` | 成功 | - |
| `400` | 请求参数错误 | `question` 为空、JSON 格式错误 |
| `500` | 服务器内部错误 | 数据库连接失败、未捕获异常 |
| `503` | 服务不可用 | 数据库连接超时 |

### 业务错误

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `Only SELECT statements are allowed` | 尝试执行非 SELECT 语句 | 检查问题是否包含删除/修改意图 |
| `Access denied to tables: xxx` | 访问白名单外的表 | 修改 `ALLOWED_TABLES` 配置 |
| `Dangerous SQL keyword detected` | SQL 包含危险关键字 | 检查问题表述 |
| `LLM runtime failed` | LLM 调用失败 | 检查 API Key、网络连接 |

### 全局异常处理

**源码引用**（`main.py`）：

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """捕获所有未处理异常"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "detail": "Internal server error",
        }
    )
```

---

## 调用示例

### cURL

```bash
# 健康检查
curl http://localhost:8000/health

# 获取 Schema
curl http://localhost:8000/schemas

# 自然语言查询（POST）
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "各城市订单数量"}'

# 自然语言查询（GET）
curl "http://localhost:8000/ask?question=各城市订单数量"
```

### Python

```python
import requests

BASE_URL = "http://localhost:8000"

# 健康检查
def check_health():
    resp = requests.get(f"{BASE_URL}/health")
    return resp.json()

# 查询
def ask(question: str):
    resp = requests.post(
        f"{BASE_URL}/ask",
        json={"question": question}
    )
    result = resp.json()
    
    if result["success"]:
        print(f"SQL: {result['generated_sql']}")
        print(f"结果: {result['result_preview']}")
        if result["chart"]:
            print(f"推荐图表: {result['chart']['chart_type']}")
    else:
        print(f"错误: {result['error']}")

# 使用
ask("上个月销售额最高的前5个产品")
```

### JavaScript / TypeScript

```typescript
const BASE_URL = "http://localhost:8000";

interface AskResponse {
  success: boolean;
  question: string;
  generated_sql: string;
  mode: string;
  result_preview: Record<string, any>[];
  chart?: {
    chart_type: string;
    x_column: string;
    y_column: string;
    confidence: number;
  };
  error?: string;
}

async function ask(question: string): Promise<AskResponse> {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return response.json();
}

// 使用
ask("各城市订单数量").then((result) => {
  if (result.success) {
    console.log("SQL:", result.generated_sql);
    console.log("数据:", result.result_preview);
  } else {
    console.error("错误:", result.error);
  }
});
```

### 前端集成示例（React）

```jsx
import { useState } from 'react';

function Text2SQLDemo() {
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('请求失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="输入问题..."
      />
      <button onClick={handleAsk} disabled={loading}>
        {loading ? '查询中...' : '查询'}
      </button>
      
      {result && (
        <div>
          <pre>{result.generated_sql}</pre>
          <table>
            {/* 渲染 result.result_preview */}
          </table>
        </div>
      )}
    </div>
  );
}
```

---

## 更新记录

| 日期 | 更新内容 |
|------|----------|
| 2026-03-22 | 细化 API 文档，添加流程图、源码引用、完整示例 |
| 2026-03-20 | 创建 API 文档初版 |