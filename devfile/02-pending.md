# Text2SQL-0412 待完成文档

> **Round 4 修正版** | 2026-04-15 更新
> 相比 Round 3：执行顺序重排、删除过度工程化项目（FAISS/PGVector/Embedding wrappers）、Provider Registry 降级

---

## 执行清单

### Step 1：规则 YAML 化 + Classifier 接入 ✅ (2026-04-15)
**完成改动：**
- `app/rules/default_rules.yaml` 新增（27条规则迁移完成）
- `app/rules/__init__.py` 新增（`RuleStore` 单例类，支持 `priority` 优先级匹配）
- `app/core/sql/generator.py` 修改（移除硬编码 `RULES` list，改为 `RuleStore.match()` 调用）
- `try_template_sql()` 保留 Python 层，`generate_sql_by_rules()` 从 YAML 匹配
**文件：** `app/core/sql/generator.py` → `rules/default_rules.yaml`
**改动：**
- RULES 从 Python list 迁移到 YAML 配置文件
- `generate_sql_by_rules()` 入口调用 `classify_question()`
- `needs_llm=True` 时真正触发 LLM 路径
- `try_template_sql()` 保留 Python 层（无法 YAML 化），YAML 仅接管 RULES list
**收益：** 规则可配置，业务人员可维护，无需改代码 + 重部署
**风险：** 🟡 中（YAML 和 RULES list 双系统并行期间需同步）

---

### Step 5：Provider Registry + Fix Astron Bug ✅ (2026-04-15)
**完成改动：**
- `app/core/llm/client.py` 修改：在 `get_llm_adapter()` 中添加 `astron` 分支（与 `openai_compatible` 相同逻辑）
- Provider Registry 保持 if-elif 链（不强制装饰器，2个Provider不需要）
**文件：** `app/core/llm/client.py`、`app/config/settings.py`
**改动：**
- **Astron bug P1 fix**：`settings.py` 有 astron 分支但 `client.py` 缺失，需先单独 fix
- 引入 `LLMProviderRegistry` + `@register("provider_name")` 装饰器（或保持 if-elif 链——当前 2 个 Provider 不需要装饰器复杂度，**可选**）
- 新增 Provider 只需添加新文件，无需修改已有文件
**收益：** OCP 违规收敛；隐藏 bug 修复
**风险：** 🟢 低（纯添加性，保留原有 if-elif 作为 fallback）

> **注：** Provider Registry 装饰器方案降为 P2 未来选项。当前 2 个 Provider 保持 if-elif 链即可，不强制上装饰器。

---

### Step 2：Chart 下沉 + 错误处理修复 ✅ (2026-04-15)
**完成改动：**
- `app/shared/schemas.py`：`AskResult` 增加 `chart_config: Optional[dict[str, Any]] = None` 字段
- `app/core/orchestrator/pipeline.py`：`ask_question()` 内直接调用 `ChartRecommender`，结果写入 `AskResult.chart_config`
- `app/api/main.py`：`/ask` handler 移除独立 chart 调用（已下沉到 pipeline）；`startup_event` 中调用 `register_error_handlers(app)`
**文件：** `app/api/main.py`、`app/core/orchestrator/pipeline.py`、`app/shared/schemas.py`
**改动：**
- `AskResult` 增加 `chart_config` 字段
- `ask_question()` 返回时直接附上 chart 配置
- API handler 移除重复的 ChartRecommender 调用
- `register_error_handlers(app)` 在 startup event 中注册
**收益：** API handler 变薄，chart 逻辑不再重复
**风险：** 🟢 低（代码搬家，不改核心逻辑）

---

### Step 6：抽象 SchemaRetriever（P0 核心）✅
**文件：** `app/core/retrieval/base.py`（新增）、`app/core/retrieval/chroma_retriever.py`（新增）、`app/core/retrieval/schema_loader.py`
**改动：**
- 定义 `class SchemaRetriever(Protocol)` 接口 + `RetrievedChunk` dataclass
- `ChromaSchemaRetriever` 实现 `retrieve()` 和 `ingest()`
- `schema_loader.py` 新增 `get_retriever()` 单例，`retrieve_schema_context()` 改为调用 retriever
- `retrieve_schema_context()` 保持返回 `str`（向后兼容）
**完成日期：** 2026-04-15

---

### Step 3：拆分 `generate_sql()` ✅
**文件：** `app/core/llm/client.py`
**前置依赖：** Step 6（SchemaRetriever 抽象就绪）
**改动：**
- 旧版 `generate_sql()` 逻辑保存为 `_generate_sql_legacy()`
- 新增 `generate_sql_v2()`，通过 `get_retriever()` 注入 retriever
- `USE_GENERATE_SQL_V2` 环境变量控制版本路由（默认 false=旧版）
- `should_fast_fallback()`、`get_llm_adapter()` 保持不变
**完成日期：** 2026-04-15

---

### Step 4：DB 层消重 ✅
**文件：** `app/core/sql/database.py`（标记废弃）、`app/core/sql/db_abstraction.py`（保留）、`app/core/sql/executor.py`、`app/core/sql/guard.py`
**改动：**
- `database.py` 顶部添加废弃声明
- `executor.py` 迁移到 `db_abstraction`：`create_connector()` + `QueryResult.data` 取 DataFrame
- `guard.py` 正则表名提取升级为 `sqlparse` AST：`SQLValidator._extract_tables_v2()`
**调用点状态：**
- `app/core/sql/executor.py` → ✅ 已迁移
- `scripts/verify_week2.py` → ⚠️ 未迁移（测试脚本，非生产代码）
- `tests/unit/test_database_simple.py` → ⚠️ 未迁移（测试文件）
**完成日期：** 2026-04-15

---

### Step 7：Pipeline Stage 化（长期目标）⏳
**文件：** `app/core/orchestrator/pipeline.py`
**状态：** 标注为长期目标，不在本轮短期冲刺范围
**改动：**
- 引入 `PipelineStage` 抽象基类
- `ask_question()` 逐步演进为 `PipelineOrchestrator`
- 保持对老代码的向后兼容
**收益：** 编排能力增强，支持条件分支、多阶段验证、结果缓存
**风险：** 🟢 低（纯添加，不修改 `ask_question()` 现有逻辑）

---

## 执行顺序（Round 4 修正）

```
Step 1  →  Step 5  →  Step 2  →  Step 6  →  Step 3  →  Step 4  →  Step 7
(YAML化)   (Registry)  (Chart)   (Retriever)  (拆分)     (DB消重)   (Pipeline)
   ↓          ↓          ↓          ↓          ↓          ↓
 低风险高收益  纯添加基础设施  代码搬家   P0核心解锁  依赖就绪后执行  收尾清理    长期目标
```

**与 Round 3 顺序的差异：**
- Step 5（Registry）从第 5 位提前到第 2 位（纯添加性基础设施）
- Step 6（SchemaRetriever）从第 6 位提前到第 4 位（P0 核心）
- Step 3（拆分）从第 3 位延后到第 5 位（需等 Step 6 就绪）
- 删除 R3/R4（FAISS/PGVector）和 3 个 Embedding wrapper 类

---

## 不进入本轮计划的过度工程化项目

| 项目 | Round 3 提案 | Round 4 结论 |
|------|-------------|-------------|
| FAISSRetriever / PGVectorRetriever | P1 实现 | ❌ 删除，等 benchmark 需求再决定 |
| `BGEEmbedding` / `M3EEmbedding` / `OpenAIEmbedding` | 新增 3 个 wrapper | ❌ 删除，直接用 LangChain 类 |
| `BailianLLMGenerator` 独立类 | 继承 `LLMGenerator` | ❌ 删除，与父类完全雷同 |
| LCEL Chain 替代 Vanna | R2 目标 | ❌ 推迟，Vanna 替换成本极高 |
| Provider `@register` 装饰器 | P0 强制 | ⚠️ 降为可选，2 个 Provider 不需要 |

---

## 扩展方向（不进入本轮计划）

| 方向 | 说明 |
|------|------|
| LCEL Chain 替代 Vanna | R2 目标，需 retrieval 抽象稳定后再评估 |
| FAISS / PGVector 实现 | 等 benchmark 数据驱动 |
| JWT 认证替代 API Key | 未来多用户/租户场景 |
| Prometheus / Grafana 接入 | 企业级可观测性 |
| 多轮对话修正 | 用户可对生成 SQL 做确认/修改 |

---

_最后更新：2026-04-15_
