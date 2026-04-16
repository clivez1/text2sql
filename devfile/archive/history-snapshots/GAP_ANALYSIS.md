# 差距分析 - Text2SQL vs Data Viz

> 对比两个项目的工程化水平，识别 Text2SQL 需要补强的领域

**日期**: 2026-03-27

---

## 1. 总体对比

| 维度 | Data Viz Agent | Text2SQL Agent | 差距等级 |
|------|---------------|----------------|----------|
| **代码质量** | ✅ 优秀 | ⚠️ 需改进 | 🟡 中 |
| **测试覆盖** | ✅ 180 passed | ❌ 104 tests (有错误) | 🔴 高 |
| **错误处理** | ✅ 统一 AppError | ❌ 散落 | 🔴 高 |
| **输入验证** | ✅ Pydantic 全覆盖 | ⚠️ 部分覆盖 | 🟡 中 |
| **LLM 弹性** | ✅ 重试+降级+超时 | ❌ 无保护 | 🔴 高 |
| **请求限流** | ✅ 60 req/min | ❌ 无保护 | 🟡 中 |
| **结构化日志** | ✅ JSON + request_id | ❌ print/基础日志 | 🟡 中 |
| **CI/CD** | ✅ GitHub Actions | ❌ 无 | 🟢 低 |
| **健康检查** | ✅ /health + /ready | ✅ /health | ✅ 无 |

**结论**: Text2SQL 需要重点补强 **测试修复** 和 **LLM 弹性调用**。

---

## 2. 详细对比

### 2.1 测试状态

| 指标 | Data Viz | Text2SQL |
|------|----------|----------|
| 测试文件数 | 10+ | 5 |
| 测试用例数 | 180 passed, 1 skipped | 104 collected (有错误) |
| 测试覆盖率 | 已统计 (pytest-cov) | 未统计 |
| CI 集成 | ✅ 自动运行 | ❌ 无 CI |

**Text2SQL 问题**:
```
E   ModuleNotFoundError: No module named 'app'
```

**根因**: 测试运行时 Python 路径未正确设置。

---

### 2.2 错误处理

**Data Viz (✅)**:
```python
# app/core/errors.py
class AppError(Exception):
    code: ErrorCode
    message: str
    detail: Optional[str]
    
    def to_response(self) -> Dict[str, Any]:
        return {"success": False, "error": {...}}

# 全局异常处理器
@app.exception_handler(AppError)
async def app_error_handler(request, exc):
    return JSONResponse(exc.to_response(), status_code=400)
```

**Text2SQL (❌)**:
```python
# app/api/main.py - 当前状态
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    # 直接返回异常信息，可能泄露敏感信息
    return JSONResponse({"error": str(exc)}, status_code=500)
```

**差距**: Text2SQL 缺少统一的错误码体系和异常处理器。

---

### 2.3 输入验证

**Data Viz (✅)**:
```python
# app/core/validators.py
class ChartRequest(BaseModel):
    chart_type: str = Field(..., regex="^(bar|line|pie|scatter|heatmap|radar)$")
    x_column: Optional[str] = None
    y_columns: Optional[List[str]] = None
    
    @validator("y_columns")
    def validate_y_columns(cls, v):
        if v and len(v) > 5:
            raise ValueError("最多支持 5 个 Y 轴列")
        return v
```

**Text2SQL (⚠️)**:
```python
# app/shared/schemas.py - 当前状态
class AskRequest(BaseModel):
    question: str
    db_name: Optional[str] = None
    
    # 缺少严格校验：
    # - question 长度限制
    # - db_name 格式校验
    # - 敏感词过滤
```

**差距**: Text2SQL 输入校验不够严格，缺少长度限制和格式校验。

---

### 2.4 LLM 弹性调用

**Data Viz (✅)**:
```python
# app/core/llm/resilient_client.py
class ResilientLLMClient:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def generate(self, prompt: str) -> str:
        try:
            return await asyncio.wait_for(
                self._call_primary(prompt),
                timeout=self.config.timeout,
            )
        except Exception:
            if self.config.fallback_enabled:
                return await self._call_fallback(prompt)
            raise
```

**Text2SQL (❌)**:
```python
# app/core/orchestrator/pipeline.py - 当前状态
def ask_question(question: str, db_name: str = None) -> dict:
    # 直接调用 Vanna，无重试、无超时、无降级
    sql = vanna.generate_sql(question)
    result = execute_sql(sql)
    return {"sql": sql, "result": result}
```

**差距**: Text2SQL 的 LLM 调用完全裸奔，网络抖动直接导致服务不可用。

---

### 2.5 请求限流

**Data Viz (✅)**:
```python
# app/middleware/rate_limiter.py
class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        # 滑动窗口算法，~30行代码
        ...
```

**Text2SQL (❌)**:
- 无任何限流保护
- 恶意用户可无限调用 LLM，导致成本失控

---

### 2.6 结构化日志

**Data Viz (✅)**:
```python
# app/core/logging.py
import json
from pythonjsonlogger import jsonlogger

formatter = jsonlogger.JsonFormatter(
    '%(timestamp)s %(level)s %(name)s %(message)s %(request_id)s'
)
```

**Text2SQL (❌)**:
```python
# 多处使用
print(f"Error: {e}")
logging.info("Processing request")
```

**差距**: Text2SQL 日志非结构化，难以集成 ELK 等日志平台。

---

## 3. 优先级排序

基于影响和风险，Text2SQL 演进优先级：

| 优先级 | 增强项 | 风险等级 | 工作量 |
|--------|--------|----------|--------|
| 🔴 P0 | 修复测试导入 | 高 | 0.5 天 |
| 🔴 P1 | LLM 弹性调用 | 高 | 1 天 |
| 🔴 P1 | 统一错误处理 | 高 | 0.5 天 |
| 🟡 P2 | 输入验证增强 | 中 | 0.5 天 |
| 🟡 P2 | 结构化日志 | 中 | 0.5 天 |
| 🟡 P2 | 请求限流 | 中 | 0.5 天 |
| 🟢 P3 | CI/CD | 低 | 0.5 天 |
| 🟢 P3 | 测试覆盖率 | 低 | 1 天 |

---

## 4. 可复用资产

从 Data Viz Agent 可直接复用的代码：

| 文件 | 用途 | 复用方式 |
|------|------|----------|
| `errors.py` | 统一错误处理 | 复制 + 适配错误码 |
| `validators.py` | 输入验证模式 | 参考 + 扩展字段 |
| `resilient_client.py` | LLM 弹性调用 | 复制 + 适配 Vanna |
| `rate_limiter.py` | 请求限流 | 直接复制 |
| `logging.py` | 结构化日志 | 直接复制 |
| `.github/workflows/` | CI/CD | 复制 + 适配路径 |

---

## 5. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 重构引入 Bug | 中 | 高 | 增量修改 + 测试先行 |
| LLM 调用失败 | 高 | 高 | 弹性调用 + 降级策略 |
| API 兼容性破坏 | 低 | 中 | 保持接口签名不变 |
| 性能下降 | 低 | 中 | 基准测试 |

---

## 6. 结论

Text2SQL Agent 当前工程化水平低于 Data Viz Agent，主要差距在：

1. **测试基础设施损坏** - 必须优先修复
2. **LLM 调用无保护** - 高风险，需立即加固
3. **错误处理不规范** - 影响用户体验和安全性

建议按照 TECH_EVOLUTION_PLAN.md 中的 Phase 0-2 顺序实施，预计 5.5 天可完成核心加固。