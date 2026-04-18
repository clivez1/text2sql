# Round 4 方案分析总结

> 更新：2026-04-15
> 基于深度代码扫描 vs Round 3 方案的对比分析

---

## 核心结论

**Round 3 方案方向正确，但存在 3 类问题需要修正：**
1. **过度工程化**：多 Retriever 实现 + Embedding wrapper 类 = 无实际需求支撑
2. **执行顺序倒置**：Step 3 排在 Step 5/6 之前，但 Step 3 依赖 Step 5/6 的前置抽象
3. **问题优先级失准**：Vanna 替换被列为 P0，但实际是 R2（重写成本极高）

**Round 4 修正后：执行顺序 1→5→2→6→3→4→7，删除 4 类过度工程化项目。**

---

## Round 3 vs Round 4 对比

| 维度 | Round 3 | Round 4 |
|------|---------|---------|
| 执行顺序 | 1→2→3→4→5→6→7 | 1→5→2→6→3→4→7 |
| 过度工程化项目 | ~15 新文件 | ~9 新文件（删除 R3/R4/3 wrappers） |
| Provider Registry | P0 强制装饰器 | P2 可选，保持 if-elif |
| LCEL vs Vanna | P0 替换 Vanna | R2 推迟，等 retrieval 稳定 |
| FAISS/PGVector | P1 实现 | ❌ 删除，等 benchmark |
| Step 3 定位 | 第 3 位 | 第 5 位（依赖就绪后） |

---

## 代码深度扫描发现（Round 4 独有）

### 1. `_build_vanna()` 每次调用重建 — 真实 P1 问题
```python
# adapters.py: generate_sql() 内部
def generate_sql(self, question: str) -> str:
    vn = self._build_vanna()  # 每次调用都重建
    # ...
    vn.train(documentation=prompt.system_prompt)  # 每次都 train
    vn.train(documentation=prompt.user_prompt)     # 每次都 train
```
- 27 条 rule 每次都 `vn.train()`
- DDL + TEXT2SQL_SYSTEM_PROMPT 每次都 `vn.train()`
- **建议**：Vanna 实例缓存到 adapter 生命周期，或等 LCEL 替换

### 2. 两套 DB 抽象层完全独立并存
- `database.py`：简单版 `DatabaseConnector` ABC + 3 个子类
- `db_abstraction.py`：完整版 `DatabaseConnector` ABC + `DatabaseManager` 单例 + `QueryResult` + `HealthStatus`
- 两者**没有继承关系**，互相不感知
- **建议**：保留 `db_abstraction.py`，废弃 `database.py`

### 3. `BailianCodePlanAdapter` 零 override
```python
@dataclass(frozen=True)
class BailianCodePlanAdapter(OpenAICompatibleAdapter):
    provider_name: str = "bailian_code_plan"
    # 没有任何方法 override
```
**建议**：删除独立类，保留 provider_name 区分即可。

### 4. `QuestionClassification.category` 全程未使用
```python
# client.py
if should_fast_fallback(question):  # should_fast_fallback 内部调用了 classify_question
    ...
# 但 classification.category 从未参与路由决策
```
**建议**：Step 3 拆分时，让 `SqlGenerator.supports(classification)` 真正使用 `category` 字段。

---

## Round 4 Subagent 分析结论

### arch-reviewer-structure
- Step 5（Registry）应提前到 Step 1.5（纯添加性基础设施）
- Step 6（SchemaRetriever）与 Step 3 存在隐藏依赖（Protocol 应先于使用处定义）
- Step 7 标注为长期目标，避免与短期优化混淆

### arch-reviewer-simplicity
- 文档数字注水：宣称 7 步实际 11 步，宣称 3 接口实际 2 接口
- 3 个 Embedding wrapper 是"LangChain 上面再包一层 LangChain"
- 4 个 Retriever 实现无 benchmark 需求，属于预防性过度工程
- **Phase 边界（R→G→P）是 Round 3 的真实改进**，应保留

### arch-reviewer-risk
- Step 3 最高风险：generate_sql 是唯一核心入口，无抽象保护
- 缓解策略：双版本并存 + `USE_GENERATE_SQL_V2` 环境变量
- **所有 Step 均可灰度切换**，不需要停机

### round4-langchain（LangChain 实用性）
- LCEL 的 chain 组合能力在**线性流程**下零收益（当前 Pipeline：ask→generate→run）
- `_build_vanna()` 重复训练是**真实 P1 问题**，不应被 LangChain 整合分散注意力
- **最小可行 LangChain 整合**：仅用 `Embeddings` 接口替换 ChromaDB 内嵌 embedding，不引新抽象

### round4-migration（迁移路径）
- 安全迁移路径：1→5→2→6→3→4→7
- 双版本策略（`generate_sql_v2` + feature flag）使得所有改动均可单独回滚
- 每个 Step 执行后必须完整跑 265 个测试

### round4-architecture（架构匹配度）
- Vanna 耦合程度被低估：Vanna 是生成**核心实现**，不是可替换的"适配层"
- 两套 DB 抽象层方案完全没提（Round 3 专注 retrieval 层，忽略 DB 层）
- 真实 P0：Retrieval 层 ChromaDB 硬编码抽象

---

## 执行入口

详见 `devfile/02-pending.md`。

**Round 4 方案已成熟，可以开始执行。**

---

*更新时间：2026-04-15*
