# arch-agent-extensibility 分析结论

> Extensibility & Rules 专项分析
> 更新时间：2026-04-14 23:34

---

## 一、Provider 扩展 OCP 问题

### 当前 if-elif 链位置

| 文件 | 函数 | 当前 Provider 数 | 新增 Provider 需改 |
|------|------|----------------|------------------|
| `client.py` | `get_llm_adapter()` | 2 个（bailian_code_plan, openai_compatible） | ✅ 改此文件 |
| `settings.py` | `get_provider_config()` | 3 个（bailian_code_plan, openai_compatible, astron） | ✅ 改此文件 |
| `adapters.py` | import + 类定义 | 2 个 adapter 类 | ✅ 改此文件 |

**结论：当前需要改 3 个文件才能新增 1 个 Provider，违反 OCP（开闭原则）。**

### 额外发现：隐藏 bug

`settings.py` 的 `get_provider_config()` **已经写了 `astron` 分支**，但 `client.py` 的 `get_llm_adapter()` 完全没有处理 `astron`——这意味着 astron 配置存在但实际不可用，是隐藏的 bug。

### 受影响的功能点

- `check_llm_connectivity()` 依赖 `get_llm_adapter()`
- `generate_sql()` 中 `adapter.provider_name` 追踪
- `health_check.py` 中的 fallback 判断

---

## 二、ProviderRegistry 设计

### 推荐方案：@register 装饰器 + 插件自动发现

```python
# app/core/llm/registry.py
from typing import Protocol, ClassVar
from dataclasses import dataclass

class LLMProviderRegistry:
    _providers: ClassVar[dict[str, type["LLMAdapter"]]] = {}
    
    @classmethod
    def register(cls, name: str):
        """装饰器：@LLMProviderRegistry.register("openai")"""
        def decorator(adapter_cls: type["LLMAdapter"]) -> type["LLMAdapter"]:
            cls._providers[name] = adapter_cls
            return adapter_cls
        return decorator
    
    @classmethod
    def create(cls, name: str, config: "LLMProviderConfig") -> "LLMAdapter":
        if name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(f"Unknown provider: {name}. Available: {available}")
        return cls._providers[name](config=config)
    
    @classmethod
    def available_providers(cls) -> list[str]:
        return list(cls._providers.keys())
```

```python
# app/core/llm/adapters.py（改造后）
from app.core.llm.registry import LLMProviderRegistry

@LLMProviderRegistry.register("bailian_code_plan")
@dataclass(frozen=True)
class BailianCodePlanAdapter(OpenAICompatibleAdapter):
    provider_name: str = "bailian_code_plan"

@LLMProviderRegistry.register("openai_compatible")
@dataclass(frozen=True)
class OpenAICompatibleAdapter:
    config: LLMProviderConfig
    provider_name: str = "openai_compatible"
    # ... 其余方法不变

# astron 只需新增一个类 + @register，不再改 client.py / settings.py
@LLMProviderRegistry.register("astron")
@dataclass(frozen=True)
class AstronAdapter(OpenAICompatibleAdapter):
    provider_name: str = "astron"
```

```python
# client.py（改造后）
def get_llm_adapter() -> LLMAdapter:
    settings = get_settings()
    config = settings.get_provider_config()
    return LLMProviderRegistry.create(config.provider, config)
```

**效果：新增 Provider 只需在 adapters.py 加 1 个文件 + @register 装饰器，client.py / settings.py 零改动。**

---

## 三、规则 YAML 化

### RuleStore 结构设计

```python
# app/core/sql/rules/rule_store.py
from pathlib import Path
from typing import Optional
import yaml

@dataclass(frozen=True)
class Rule:
    keywords: tuple[str, ...]
    sql: str
    explanation: str
    priority: int = 0          # 数值越大优先级越高
    tags: tuple[str, ...] = ()  # e.g. ("region", "order")

class RuleStore:
    rules: list[Rule]
    version: str = "1.0"
    
    @classmethod
    def from_yaml(cls, path: Path) -> "RuleStore":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        rules = [
            Rule(
                keywords=tuple(r["keywords"]),
                sql=r["sql"],
                explanation=r["explanation"],
                priority=r.get("priority", 0),
                tags=tuple(r.get("tags", [])),
            )
            for r in data["rules"]
        ]
        return cls(rules=rules, version=data.get("version", "1.0"))
    
    def match(self, question: str) -> Optional[Rule]:
        """按优先级从高到低匹配关键词"""
        normalized = question.replace("？", "").replace("?", "").strip()
        matched = []
        for rule in self.rules:
            if all(kw in normalized for kw in rule.keywords):
                matched.append(rule)
        if not matched:
            return None
        return max(matched, key=lambda r: r.priority)
    
    def match_with_classification(
        self, question: str, classification: "QuestionClassification"
    ) -> Optional[Rule]:
        """结合分类结果的增强匹配"""
        if classification.needs_llm:
            return None  # 分类认为需要 LLM，不走 rule
        candidates = [r for r in self.rules if r.category == classification.category]
        candidates = candidates or self.rules
        normalized = question.replace("？", "?").strip()
        for rule in candidates:
            if all(kw in normalized for kw in rule.keywords):
                return rule
        return None
```

### YAML 格式示例（`config/rules/sql_templates.yaml`）

```yaml
version: "1.0"
rules:
  - keywords: ["上个月", "前5", "产品", "销售额"]
    sql: >
      SELECT p.product_name, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
      FROM order_items oi
      JOIN orders o ON oi.order_id = o.order_id
      JOIN products p ON oi.product_id = p.product_id
      WHERE strftime('%Y-%m', o.order_date) = (
        SELECT strftime('%Y-%m', date(MAX(order_date), 'start of month', '-1 month'))
        FROM orders
      )
      GROUP BY p.product_name ORDER BY revenue DESC LIMIT 5;
    explanation: "统计上个月各产品销售额并取 Top5。"
    priority: 10
    tags: ["product", "revenue", "time"]

  - keywords: ["各城市", "订单数量"]
    sql: "SELECT city, COUNT(*) AS order_count FROM orders GROUP BY city ORDER BY order_count DESC LIMIT 10;"
    explanation: "按城市统计订单量并排序。"
    priority: 5
    tags: ["city", "order"]

  - keywords: ["订单", "总数"]
    sql: "SELECT COUNT(*) AS order_count FROM orders LIMIT 50;"
    explanation: "统计订单总数。"
    priority: 5
    tags: ["order"]
```

### 从 RULES list 迁移策略

1. **自动转换脚本**：用 Python 将 `generator.py` 中的 `RULES: list[Rule]` 自动导出为 YAML（直接序列化）
2. **`generate_sql_by_rules()` 改造**：改为 `RuleStore.from_yaml(path).match(question)`
3. **`try_template_sql()` 合并**：可作为 `RuleStore` 的高优先级特殊规则（加 `priority: 100`），或作为 `TemplateSqlSynthesizer` 独立保留
4. **渐进迁移**：YAML 和硬编码并行，对比结果一致性后再废弃硬编码

### 关键设计决策

- 关键词匹配用 `all(kw in normalized)` 而非精确匹配，保留现有宽松语义
- `priority` 字段解决关键词重叠覆盖问题（如"北京"+"订单" vs "订单"+"总数"）
- `tags` 字段支持按业务维度分类，为后续选择性启用提供基础

---

## 四、DB 层统一：db_abstraction.py vs database.py 取舍

### 现状分析

| 维度 | `database.py`（旧/简单） | `db_abstraction.py`（新/完整） |
|------|------------------------|------------------------------|
| DatabaseConfig | `db_type: str` | `db_type: DatabaseType(Enum)` ✅ |
| 异常处理 | 简单 try/catch | SQLAlchemyError 细分 ✅ |
| 连接池 | 无显式配置 | `QueuePool` + `pool_recycle` ✅ |
| 健康检查 | `test_connection()` 返回 `(bool, str)` | `HealthStatus` dataclass ✅ |
| 事件机制 | 无 | `@event.listens_for` ✅ |
| 子类实现 | SQLite/MySQL/Pg 三类在文件内 | 拆分 `connectors/` 子目录 ✅ |
| 单例模式 | 无，工厂函数 | `DatabaseManager` 单例 ✅ |

### 根因

`db_abstraction.py` 是后来写的完整版，但 `database.py` 没删除（或有其他模块仍依赖它），形成两套并行。

### 是否值得引入 IDatabaseStrategy？

**结论：不需要。理由：**

1. `db_abstraction.py` 已经有 `DatabaseConnector(ABC)` — 这就是事实上的 interface，不需要再引入额外的 `IDatabaseStrategy` 抽象层
2. `DatabaseConnector` 的子类（SQLite/MySQL/PostgreSQL）在 `connectors/` 目录已经是策略模式实现
3. `DatabaseManager` 管理多 connector 实例，已经是工厂+单例

**真正的问题是：统一入口，而不是增加抽象。**

### 建议

- **废弃 `database.py`**，所有 DB 访问统一走 `db_abstraction.py`
- `DatabaseManager` 作为唯一入口，提供 `execute()` / `health_check()` / `get_connector()`
- `connectors/` 下的子类作为策略实现（已经是良好的设计）
- 需要先 `grep` 确认 `database.py` 的所有调用点，确保迁移无遗漏

---

## 五、UI 绕过 API 解决方案

### 问题

`streamlit_app.py` 直接 import `ask_question` 或 `generate_sql`，绕过了 HTTP API 层。

### 根本原因

业务逻辑层没有通过 HTTP 服务友好暴露，或 API 层需要额外 auth 封装导致 UI 跳过。

### HTTP 调用具体实现（FastAPI 为例）

```python
# app/api/routes.py
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import os

router = APIRouter(prefix="/api/v1", tags=["text2sql"])

def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """验证 API key，支持两种模式"""
    expected = os.getenv("TEXT2SQL_API_KEY", os.getenv("OPENCLAW_BAILIAN_API_KEY", ""))
    if not expected:
        return "dev"  # 无 key 模式（开发环境）
    if x_api_key == expected:
        return "validated"
    raise HTTPException(401, "Invalid API key")

@router.post("/query")
def query_question(
    question: str,
    _: str = Header(verify_api_key),
):
    """Text2SQL 查询接口"""
    from app.core.client import generate_sql
    sql, explanation, mode, reason = generate_sql(question)
    return {"sql": sql, "explanation": explanation, "mode": mode, "reason": reason}
```

### Streamlit 端改造

```python
# streamlit_app.py（改造后）
import requests
import os

API_BASE = os.getenv("TEXT2SQL_API_URL", "http://localhost:8000/api/v1")

def ask_question_via_api(question: str) -> dict:
    api_key = os.getenv("TEXT2SQL_API_KEY", "")
    headers = {"X-API-Key": api_key} if api_key else {}
    response = requests.post(
        f"{API_BASE}/query",
        json={"question": question},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
```

### API key 传递方案

| 场景 | 方案 |
|------|------|
| 开发/内部 | `OPENCLAW_BAILIAN_API_KEY` 作为共享 key，Streamlit 从 env 读 |
| 多用户 | 每个用户在飞书应用配置自己的 key，通过 header 传递 |
| Key 轮转 | 后端支持多个有效 key（set of keys），Streamlit 读自己的 env |

### 收益

- API 层天然隔离，UI 升级不影响后端逻辑
- 可以对 API 请求做限流、审计、权限控制
- 后端可以独立部署和扩展

---

## 六、对其他 subagent 提案的质疑（可扩展性视角）

### 对 Generation & LangChain agent 的质疑

**1. 接口契约问题**

如果 `SqlGenerator` 接口设计为只接受 "原始 question 字符串"：

```python
def generate(self, question: str) -> GenerationResult:  # ❌ 缺失 classification
```

那么 `QuestionClassification` 结果作为第一级路由信号就无法注入。**建议接口设计为：**

```python
def generate(
    self,
    question: str,
    classification: QuestionClassification,  # ✅ 必须注入
    schema_context: str,
) -> GenerationResult:
```

否则 classification 永远只是"参考信息"而非真正的路由决策者。

**2. LCEL Chain 的可替换性**

LCEL 的 `|` 操作符本身是组合式的，但如果 `ChatPromptTemplate` 和 `ChatOpenAI` 是直接实例化而非通过工厂注入，换 LLM provider 仍然需要改代码。建议 LCEL chain 也通过 `ProviderRegistry` 创建。

### 对 RAG & Retrieval agent 的质疑

**1. ChromaDB 硬编码的位置**

`retrieve_schema_context()` 直接 `import chromadb` 并调用 `chromadb.PersistentClient`，这是强耦合。抽象为 `SchemaRetriever` 接口是对的，但要注意接口返回值设计（见下）。

**2. 接口设计警告：返回类型不应是 `str`**

如果 retrieval 接口设计为：

```python
def retrieve_schema_context(question: str, limit: int = 4) -> str:  # ❌ 字符串拼接
```

这对测试和 mock 很不友好，上层无法知道检索质量。建议返回结构化对象：

```python
@dataclass(frozen=True)
class SchemaContext:
    documents: list[str]           # 原始检索文档
    table_hints: list[str]         # 硬编码的表名提示
    field_aliases: dict[str, list[str]]  # 字段别名映射
    scores: list[float] = ()        # 相似度分数（用于判断检索质量）
    source: str = "unknown"         # "chroma" | "local" | "ddl"

class SchemaRetriever(Protocol):
    def retrieve(self, question: str, limit: int) -> SchemaContext: ...
```

这样上层（`generate_sql`）可以按需使用各字段，而不是总是把所有字段拼接成字符串。

Generation 层收到 `SchemaContext` 后，可以：
- 如果 `scores` 普遍偏低 → 降低 LLM 的置信度，提示使用 rule fallback
- 如果 `documents` 为空 → 使用 DDL fallback
- 将 `source` 写入 metadata 用于可观测性

**3. Embedding 模型切换**

现有 `schema_loader.py` 中 embedding 模型是隐式的（ChromaDB 默认），如果要支持 bge/m3e 需要在 `SchemaRetriever` 接口中注入 `Embeddings` 实例。建议使用 LangChain 的 `Embeddings` 接口并在 retrieval 初始化时注入，而不是在 `LocalVanna._build_vanna()` 深处隐式指定。

---

## 七、关键结论汇总

| # | 结论 | 优先级 |
|---|------|-------|
| 1 | ProviderRegistry 用 @register 装饰器，client.py/settings.py 解耦 | P0 |
| 2 | `astron` 分支在 settings.py 存在但在 client.py 缺失，是隐藏 bug | P1 |
| 3 | 废弃 `database.py`，统一走 `db_abstraction.py` | P1 |
| 4 | 规则 YAML 化，RuleStore + priority + tags | P0 |
| 5 | UI 改走 HTTP API，避免直接 import | P1 |
| 6 | `SqlGenerator.generate()` 接口必须接收 `QuestionClassification` | P1 |
| 7 | `SchemaRetriever` 返回 `SchemaContext` dataclass 而非 `str` | P1 |
