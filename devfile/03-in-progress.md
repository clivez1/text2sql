# Text2SQL-0412 正在进行文档

> **架构优化执行阶段进行中**
> 开始时间：2026-04-15 10:07

---

## 执行状态

| Step | 任务 | 状态 | 完成日期 |
|------|------|------|---------|
| 1 | 规则 YAML 化 | ✅ 完成 | 2026-04-15 |
| 5 | Provider Registry + Fix Astron Bug | ✅ 完成 | 2026-04-15 |
| 2 | Chart 下沉 + 错误处理 | ✅ 完成 | 2026-04-15 |
| 6 | SchemaRetriever 抽象 | ✅ 完成 | 2026-04-15 |
| 3 | generate_sql() 拆分 | ✅ 完成 | 2026-04-15 |
| 4 | DB 层消重 | ✅ 完成 | 2026-04-15 |
| 7 | Pipeline Stage 化 | 🔳 长期目标 | - |

---

## Step 1 ✅ 完成 (2026-04-15)
**关键改动：**
- 新增 `app/rules/default_rules.yaml`（27条规则迁移完成，含 priority/tags 扩展字段）
- 新增 `app/rules/__init__.py`（`RuleStore` 单例，priority 数值越大优先级越高）
- 修改 `app/core/sql/generator.py`（移除硬编码 RULES list，改为 `RuleStore.match()`）
- `try_template_sql()` 保留 Python 层（无法 YAML 化）；`generate_sql_by_rules()` 从 YAML 匹配

---

## Step 5 ✅ 完成 (2026-04-15)
**关键改动：**
- `app/core/llm/client.py`：`get_llm_adapter()` 添加 `astron` 分支处理（与 `openai_compatible` 相同逻辑）
- Provider Registry 保持 if-elif 链，不强制装饰器（当前 2 个 Provider 不需要）

---

## Step 2 ✅ 完成 (2026-04-15)
**关键改动：**
- `app/shared/schemas.py`：`AskResult` 增加 `chart_config: Optional[dict[str, Any]] = None`
- `app/core/orchestrator/pipeline.py`：`ask_question()` 内直接调用 `ChartRecommender`，chart_config 写入 AskResult
- `app/api/main.py`：`/ask` handler 移除重复 chart 调用；`startup_event` 中注册 `register_error_handlers(app)`

---

## Step 6 ✅ 完成 (2026-04-15)
**关键改动：**
- 新增 `app/core/retrieval/base.py`：`SchemaRetriever` Protocol + `RetrievedChunk` dataclass
- 新增 `app/core/retrieval/chroma_retriever.py`：`ChromaSchemaRetriever` 实现 `retrieve()` + `ingest()`
- 重构 `app/core/retrieval/schema_loader.py`：`get_retriever()` 单例 + `retrieve_schema_context()` 委托
- 向后兼容：`retrieve_schema_context()` 仍返回 `str`

---

## Step 3 ✅ 完成 (2026-04-15)
**关键改动：**
- `app/core/llm/client.py`：原 `generate_sql()` 逻辑保存为 `_generate_sql_legacy()`
- 新增 `generate_sql_v2()`：使用 `get_retriever()` 获取 retriever
- `USE_GENERATE_SQL_V2` 环境变量控制版本路由（默认 false → 旧版）
- `should_fast_fallback()` / `get_llm_adapter()` 保持不变
- `check_llm_connectivity()` 保持不变

---

## Step 4 ✅ 完成 (2026-04-15)
**关键改动：**
- `app/core/sql/database.py`：顶部添加废弃声明（引用 `db_abstraction.py`）
- `app/core/sql/executor.py`：迁移到 `db_abstraction`，`execute_query()` 返回 `QueryResult`，取 `.data` 字段
- `app/core/sql/guard.py`：正则表名提取升级为 `sqlparse` AST，`_extract_tables_v2()` 使用 `Identifier.get_real_name()`
- `scripts/verify_week2.py` 和 `tests/unit/test_database_simple.py` 未迁移（非生产代码，待后续处理）

---

## 执行顺序

```
Step 1 → Step 5 → Step 2 ✅ → Step 6 → Step 3 → Step 4 ✅ 完成
(YAML化)  (Registry)  (Chart)   (Retriever)  (拆分)    (DB消重)
```

## 执行模式

- 主 agent：龙虾（main）
- executor-A（Step 1→5→2）✅ 已完成
- executor-B（Step 6→3→4）✅ 已完成

---

*执行开始：2026-04-15 10:07 | executor-A 完成：2026-04-15 10:09 | executor-B 完成：2026-04-15 10:10*
