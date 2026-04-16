# Text2SQL-0412 架构重构多轮方案讨论

> 追踪文档 | 更新每轮讨论结果
> 项目：text2sql-0412 | 目标：易维护、易理解、可扩展的整体架构重构

---

## 讨论规则

1. 每轮各 Agent 提出**完整可落地的架构提案**（非建议清单）
2. 提案必须包含：**模块划分 + 职责定义 + 层间依赖规则 + 具体改动文件**
3. 各 Agent 互相审查提案，有权**质疑和否决**不合理部分
4. 经过**多轮辩论**收敛到**唯一所有人都接受的方案**
5. 主 Agent（龙虾）做最终拍板

---

## 各轮进度

### 第一轮：架构提案提出
**状态：✅ 完成**

### 第二轮：互相审查与质疑
**状态：⏳ 进行中**

---

## 第一轮提案汇总

### 提案 A：分层架构（Layered Architecture）

**核心思路：** 经典三层架构，API Layer / Service Layer / Data Access Layer 分离清晰。

**模块结构：**
```
app/
├── api/           # API Layer：路由、请求验证、响应格式化
├── service/       # Service Layer：业务逻辑编排
│   ├── query_service.py
│   ├── generation_service.py
│   └── chart_service.py
├── dal/           # Data Access Layer：数据库操作
│   ├── connectors/
│   └── executor.py
├── domain/        # 领域模型（纯数据结构）
└── infra/         # 基础设施（LLM、配置、日志）
```

**解决了什么：**
- generate_sql() 拆分到 service/generation_service.py
- UI 绕过 API → 强制走 API Layer
- 两套 DB 抽象 → 统一到 dal/

**潜在问题：**
- Service Layer 可能变成"大泥球"（所有业务逻辑堆在一起）
- 层间依赖容易变成"穿透调用"（API 直接调 DAL）

---

### 提案 B：Clean Architecture

**核心思路：** 领域驱动 + 用例分离，依赖倒置原则严格执行。

**模块结构：**
```
app/
├── domain/           # 核心领域（实体、值对象、领域服务）
│   ├── question.py
│   ├── sql_result.py
│   └── ports/        # 端口（接口定义）
├── usecases/         # 用例（业务编排）
│   └── ask_usecase.py
├── adapters/         # 适配器（实现端口）
│   ├── llm_adapter.py
│   ├── db_adapter.py
│   └── api_adapter.py
└── infrastructure/   # 基础设施
```

**解决了什么：**
- 依赖方向严格：domain ← usecases ← adapters ← infrastructure
- Provider 扩展 OCP → 新增 Provider 只需新增 adapter 文件
- 可测试性极高（domain 纯粹，无外部依赖）

**潜在问题：**
- 迁移成本高（几乎所有文件要重构）
- 对 2-5 人小团队可能"过度设计"
- 学习曲线陡峭

---

### 提案 C：模块化单体（Modular Monolith）

**核心思路：** 按业务能力划分模块，模块内高内聚、模块间低耦合。

**模块结构：**
```
app/
├── query/            # 查询处理模块（核心）
│   ├── ask.py        # 入口
│   ├── classifiers/
│   ├── generators/
│   ├── retrieval/
│   ├── executors/
│   └── charts/
├── auth/             # 认证模块
├── llm/              # LLM 模块
├── rules/            # 规则模块
├── config/           # 配置模块
└── ui/               # UI 模块
```

**解决了什么：**
- generate_sql() 拆分到 query/generators/
- 规则硬编码 → rules/ + YAML
- 两套 DB 抽象 → 统一到 query/executors/
- UI 绕过 API → HTTP 调用

**潜在问题：**
- 模块间循环依赖风险
- 模块边界可能退化

---

### 提案 D：流水线架构（Pipeline Stage）

**核心思路：** 业务逻辑分解为独立可组合的 Stage，Pipeline Orchestrator 编排。

**模块结构：**
```
app/
├── pipeline/
│   ├── orchestrator.py    # PipelineOrchestrator
│   ├── stages/
│   │   ├── classification_stage.py
│   │   ├── retrieval_stage.py
│   │   ├── generation_stage.py
│   │   ├── execution_stage.py
│   │   └── chart_stage.py
│   └── context.py        # PipelineContext
├── strategies/           # 策略对象（LLM/Rule）
└── adapters/             # 外部适配器
```

**解决了什么：**
- generate_sql() 7 种职责 → 7 个独立 Stage
- 每个 Stage 单一职责、可独立测试
- 支持条件跳过、并行执行、回滚

**潜在问题：**
- Stage 粒度划分需要经验
- 简单问题可能"过度拆分"
- Orchestrator 可能变成新的"上帝对象"

---

### 提案 E：适配器+策略架构（Adapter + Strategy）

**核心思路：** 把"可变行为"抽象为接口，实现是可插拔的策略对象。

**模块结构：**
```
app/
├── core/
│   ├── strategy/          # 策略接口
│   │   ├── sql_generation.py
│   │   ├── retrieval.py
│   │   └── database.py
│   └── model/             # 领域对象
├── adapters/
│   ├── sql_generation/    # SQL 生成策略实现
│   ├── retrieval/         # 检索策略实现
│   ├── database/          # 数据库策略实现
│   └── registry/          # 策略注册表
└── services/              # 服务层（编排策略）
```

**核心接口：**
```python
class ISqlGenerationStrategy(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def priority(self) -> int: ...
    def supports(self, ctx: QuestionContext) -> bool: ...
    def generate(self, ctx: QuestionContext) -> SqlResult: ...
    def should_fallback_to(self, result: SqlResult) -> bool: ...
```

**策略注册机制：**
```python
@ProviderRegistry.register("bailian_code_plan")
class BailianCodePlanAdapter(ISqlGenerationStrategy):
    ...
```

**解决了什么：**
- generate_sql() → GenerationService 编排策略
- Provider 扩展 OCP → @register 装饰器，零成本新增
- 规则硬编码 → RuleAdapter + YAML
- 两套 DB 抽象 → IDatabaseStrategy 统一

**潜在问题：**
- 策略优先级冲突需要显式处理
- ProviderRegistry 是隐式单例，测试时需清理
- 调用链多一层间接

---

## 第二轮：互相审查与质疑

### 提案 A 质疑（来自其他 Agent）

| 质疑方 | 质疑内容 | A 的回应 |
|--------|---------|---------|
| B | Service Layer 可能变成"大泥球"，所有业务逻辑堆在一起 | 可通过进一步拆分 service/ 为子模块缓解 |
| C | 层间依赖容易"穿透"（API 直接调 DAL） | 严格代码审查 + 依赖检查工具 |
| D | 没有解决"条件分支"问题（LLM vs Rule 路由） | 在 Service Layer 内部用策略模式 |
| E | Provider 扩展仍需改 Service Layer | 可在 infra/ 引入注册表 |

**结论：** A 方案可行但需要额外约束防止退化。

---

### 提案 B 质疑

| 质疑方 | 质疑内容 | B 的回应 |
|--------|---------|---------|
| A | 迁移成本太高，几乎所有文件要重构 | 接受，但长期收益大 |
| C | 对 2-5 人小团队可能"过度设计" | 接受，建议团队规模 5 人+ 时采用 |
| D | 用例层可能变得臃肿 | 可按业务能力拆分 usecases/ |
| E | 领域层与策略模式有重叠 | 策略是"行为抽象"，领域是"数据抽象"，可共存 |

**结论：** B 方案适合大团队，对小团队成本过高。

---

### 提案 C 质疑

| 质疑方 | 质疑内容 | C 的回应 |
|--------|---------|---------|
| A | 模块边界定义不够严格，容易退化 | 通过 `__init__.py` 定义 public 接口强制 |
| B | 没有依赖倒置，模块间可能循环依赖 | 模块间通过接口（Protocol）通信 |
| D | 没有显式的"编排层"，query/ask.py 可能变成新的大函数 | 可在 query/ 内部引入 PipelineOrchestrator |
| E | 策略模式没有显式抽象 | 可在模块内部使用策略，不强制全局抽象 |

**结论：** C 方案对现有代码改动最小，适合快速落地。

---

### 提案 D 质疑

| 质疑方 | 质疑内容 | D 的回应 |
|--------|---------|---------|
| A | Stage 粒度划分需要经验，可能过度拆分 | 可从粗粒度开始，逐步细化 |
| B | Orchestrator 可能变成新的"上帝对象" | Orchestrator 只做编排，不包含业务逻辑 |
| C | 对简单问题可能"过度工程化" | 可设置"快速路径"跳过 Pipeline |
| E | Stage 与策略模式有重叠 | Stage 是"步骤"，策略是"行为选择"，可组合 |

**结论：** D 方案适合流程复杂、多路径的场景。

---

### 提案 E 质疑

| 质疑方 | 质疑内容 | E 的回应 |
|--------|---------|---------|
| A | 调用链多一层间接，调试困难 | 可在开发模式启用详细日志 |
| B | 策略接口可能变得庞大 | 按职责拆分多个小接口 |
| C | ProviderRegistry 是隐式单例，测试困难 | 提供 `reset()` 方法清理状态 |
| D | 策略优先级冲突需要显式处理 | `should_fallback_to()` 提供显式回退条件 |

**结论：** E 方案最适合"可变行为多"的场景（如多 Provider、多数据库）。

---

## 第三轮：收敛与最终决策

### 各方案对比矩阵

| 维度 | A（分层） | B（Clean） | C（模块化） | D（Pipeline） | E（策略） |
|------|----------|-----------|------------|--------------|----------|
| **复杂度** | 中 | 高 | 低-中 | 中 | 中 |
| **新增文件数** | ~20 | ~25 | ~15 | ~18 | ~20 |
| **迁移成本** | 中 | 高 | 低 | 中 | 中 |
| **适合团队规模** | 3-10 | 5+ | 2-5 | 任意 | 任意 |
| **解决 generate_sql 问题** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **解决 Provider OCP** | ⚠️ 需额外 | ✅ | ⚠️ 需额外 | ⚠️ 需额外 | ✅ |
| **解决 UI 绕过 API** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **可测试性** | 中 | 高 | 中 | 高 | 高 |
| **学习曲线** | 平缓 | 陡峭 | 平缓 | 中等 | 中等 |

---

### 主 Agent 决策

**最终选择：提案 E（适配器+策略架构）**

**理由：**

1. **text2sql 的本质是多路径决策**：生成 SQL 有两条路径（LLM vs 规则），执行有多数据库，检索有多向量库。策略模式天然支持多路径决策和自动降级。

2. **Provider 扩展是核心痛点**：当前新增 Provider 需改 3+ 文件，违反 OCP。E 方案通过 `@register` 装饰器实现零成本扩展。

3. **迁移成本可控**：E 方案不需要重写所有文件，只需：
   - 定义核心接口（~5 个 Protocol）
   - 将现有实现包装为策略对象
   - 引入 GenerationService 编排

4. **可与其他方案组合**：E 的策略模式可与 C 的模块化、D 的 Pipeline 组合。后续可在策略基础上引入 Stage。

5. **适合当前团队规模**：2-5 人团队，不需要 Clean Architecture 的重抽象。

---

## 最终收敛方案

### 架构概览

```
text2sql-0412/
├── app/
│   ├── core/
│   │   ├── strategy/           # 策略接口定义
│   │   │   ├── sql_generation.py   # ISqlGenerationStrategy
│   │   │   ├── retrieval.py        # ISchemaRetrievalStrategy
│   │   │   ├── database.py         # IDatabaseStrategy
│   │   │   └── error.py            # IErrorStrategy
│   │   └── model/              # 领域对象
│   │       ├── question.py
│   │       ├── sql_result.py
│   │       └── context.py
│   │
│   ├── adapters/
│   │   ├── sql_generation/     # SQL 生成策略实现
│   │   │   ├── llm_adapter.py
│   │   │   └── rule_adapter.py
│   │   ├── retrieval/          # 检索策略实现
│   │   │   └── chromadb_retrieval.py
│   │   ├── database/           # 数据库策略实现
│   │   │   ├── sqlite_strategy.py
│   │   │   ├── mysql_strategy.py
│   │   │   └── postgresql_strategy.py
│   │   └── registry/           # 策略注册表
│   │       └── provider_registry.py
│   │
│   ├── services/
│   │   ├── ask_service.py      # 主入口
│   │   └── generation_service.py
│   │
│   ├── rules/
│   │   ├── rule_store.py
│   │   └── default_rules.yaml
│   │
│   ├── api/
│   │   └── main.py
│   │
│   └── ui/
│       └── streamlit_app.py    # HTTP 调用 API
```

### 执行步骤

| Step | 内容 | 优先级 |
|------|------|--------|
| 1 | 定义 `ISqlGenerationStrategy` 接口 | P0 |
| 2 | 实现 `RuleSqlAdapter`（规则策略） | P0 |
| 3 | 实现 `LLMSqlAdapter`（LLM 策略） | P0 |
| 4 | 引入 `ProviderRegistry` + `@register` 装饰器 | P0 |
| 5 | 实现 `GenerationService` 编排策略 | P0 |
| 6 | 规则 YAML 化 | P1 |
| 7 | UI 改为 HTTP 调用 | P1 |
| 8 | 统一 DB 抽象到 `IDatabaseStrategy` | P2 |

---

## 会议摘要

**参与方：** 主 Agent（龙虾）+ 5 个专项提案 Agent

**轮次：**
- 第一轮：5 个完整提案提出
- 第二轮：互相审查与质疑
- 第三轮：主 Agent 决策

**最终方案：** 提案 E（适配器+策略架构）

**核心收益：**
- Provider 扩展零成本（@register 装饰器）
- generate_sql() 7 种职责拆分为独立策略
- 规则可配置（YAML）
- UI 走 HTTP（经过认证/埋点）

**下一步：** 开始执行 Step 1-8

---

*文档更新时间：2026-04-14*
