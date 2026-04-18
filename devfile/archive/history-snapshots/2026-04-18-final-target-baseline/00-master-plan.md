# Text2SQL-0412 架构优化方案 1

> 项目：text2sql-0412
> 状态：**第四轮方案已收敛，待执行**
> 生成时间：2026-04-14 | **更新：2026-04-15**

---

## 一、背景与目标

项目已完成第一轮工程化收口（覆盖率 80%，265 passed），但架构存在 5 个核心问题，限制了其易维护性、易理解性和可扩展性。同时，LEE 提出了新的需求：支持多 RAG embedding 对比评测，以及增大 langchain 使用比重。

**目标：**
- 易维护：模块边界清晰、职责单一
- 易理解：新进开发者能快速定位代码
- 可扩展：新增 RAG 实现 / 新增 LLM Provider 不破坏现有结构
- LangChain Native：直接使用 LCEL / Embeddings / VectorStore，不通过 Vanna 间接
- 可评测：不同 embedding/retriever 可对比性能

---

## 二、需求汇总

### 原始 5 大架构问题

| # | 问题 | 根因 | 影响 |
|---|------|------|------|
| 1 | `generate_sql()` 混合 7 种职责 | 无模块边界，路由逻辑全部堆在一个函数 | 扩展困难，单点腐败 |
| 2 | 27 条规则硬编码在 `generator.py` | 规则与代码耦合，无法运行时修改 | 业务人员无法维护 |
| 3 | `QuestionClassification` 结果未被使用 | classifier 仅用 `needs_llm`，其余字段丢弃 | 分类器是"死代码" |
| 4 | 两套 DB 抽象层并行 | `database.py` + `db_abstraction.py` 并存 | 维护混乱 |
| 5 | UI（Streamlit）绕过 API 直接 import pipeline | 模块间无调用规范 | 路径不一致，无法独立测 |

### 新增需求（Round 3/4）

| # | 需求 | 背景 | 优先级 |
|---|------|------|--------|
| 6 | 多 RAG embedding 对比评测 | 需要切换不同 embedding 模型（bge/m3e）和向量库做性能对比 | P0 |
| 7 | 增大 langchain 使用比重 | 直接使用 LCEL / Embeddings / VectorStore | P2（暂缓） |

---

## 三、当前代码真实问题优先级

经过 Round 4 深度代码扫描，修正了 Round 3 方案中对问题深度的误判：

| 优先级 | 问题 | 真实根因 | 建议 |
|--------|------|---------|------|
| **P0** | `retrieve_schema_context()` ChromaDB 硬编码 | 唯一 retrieval 路径写死 ChromaDB client | **立即抽象** |
| **P1** | `_build_vanna()` 每次调用重建 + 重新 train | Vanna 实例在 `generate_sql()` 内部每次重建 | 缓存 Vanna 实例或 LCEL 替换 |
| **P1** | 两套 DB 抽象层并行 | `database.py` + `db_abstraction.py` 设计意图不同却并存 | 消重，保留一套 |
| **P2** | 27 条规则硬编码 | 与代码耦合 | Step 1 已规划，YAML 化 |
| **P2** | `QuestionClassification` 结果未充分使用 | `category` 字段全程未参与路由决策 | 作为 `SqlGenerator.supports()` 参数传入 |
| **P2** | `generate_sql()` 7 职责混合 | 有测试覆盖，拆分时机依赖 P0/P1 完成后 | 延后到 Step 3 |
| **P2** | Provider Registry 装饰器 | 2 个 Provider 不需要 `@register` 复杂度 | 保持 if-elif 链即可 |

---

## 四、Round 4 关键修正（对比 Round 3 方案）

### 修正 1：删除过度工程化项目
Round 3 方案的以下内容被 **删除**：
- ❌ `FAISSRetriever` / `PGVectorRetriever` 实现（无 benchmark 需求，等真正需要时再实现）
- ❌ `BGEEmbedding` / `M3EEmbedding` / `OpenAIEmbedding` 三个 wrapper 类（直接用 LangChain 类即可）
- ❌ `BailianLLMGenerator` 独立类（与 `LLMGenerator` 完全雷同）
- ❌ LCEL Chain 替代 Vanna（Vanna 是生成核心实现，替换成本极高，收益不确定）

### 修正 2：Provider Registry 降级
- `@register` 装饰器方案降为 P2 未来选项
- 当前 2 个 Provider 保持 if-elif 链，不增加复杂度
- `astron` 隐藏 bug（settings 有分支但 client.py 缺失）单独 P1 fix

### 修正 3：执行顺序重排
详见 `02-pending.md`，核心变化：
- **Step 5（Registry）提前到 Step 1.5**（纯添加性基础设施）
- **Step 6（SchemaRetriever）提前到 Step 2**（P0 核心，解锁 retrieval 抽象）
- **Step 3（generate_sql 拆分）延后到 Step 5**（依赖前置抽象就绪）
- **Step 7（Pipeline Stage）标注为长期目标**

### 修正 4：LangChain 整合策略调整
- **推迟** LCEL 替代 Vanna（R2 目标），直到 retrieval 层抽象稳定
- **立即做**：用 LangChain `Embeddings` 接口替换 ChromaDB 内嵌 embedding（通过 `SchemaRetriever` 注入）
- **核心收益**：`SchemaRetriever` 可切换 embedding 模型（bge/m3e/text-embedding-3）

---

## 五、最终执行顺序

```
Step 1  →  Step 5  →  Step 2  →  Step 6  →  Step 3  →  Step 4  →  Step 7
(YAML化)   (Registry)  (Chart)   (Retriever)  (拆分)     (DB消重)   (Pipeline)
 ↓          ↓          ↓          ↓          ↓          ↓
 低风险    纯添加     代码搬家   P0核心    依赖就绪   收尾消重    长期目标
```

---

## 六、方案成熟度

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 问题优先级修正 | ✅ | Round 4 深度扫描后重新分级 |
| 执行顺序优化 | ✅ | Step 5/6 前置，Step 3 延后 |
| 过度工程清理 | ✅ | 删除 3 类过度设计 |
| 向后兼容策略 | ✅ | 双版本 + feature flag |
| LangChain 策略 | ✅ | 推迟 Vanna 替换，先做 retrieval 抽象 |
| Step 文档更新 | ✅ | `02-pending.md` 已同步 |

**结论：方案已成熟，可以开始执行。**

---

*本方案归档于 `devfile/00-master-plan.md`，作为后续开发依据。*
*最后更新：2026-04-15*
