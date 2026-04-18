# 11. 目标架构方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 架构目标

目标架构需要同时满足五个要求：

1. 支持中大型数据库自然语言分析
2. 支持 LLM 优先和多模型协议接入
3. 支持多轮 Copilot / Agent 编排
4. 支持受治理的数据写操作
5. 保持单仓可部署和可渐进演进

---

## 2. 五层架构

> 说明：这里的“五层架构”描述的是运行时职责分层，不等于物理目录必须继续平铺在 `app/core/`。物理代码结构将采用“分层 + 分域”的立体目录，而不是继续把能力模块堆在同一层。

### 2.1 入口层

职责：接收问题、展示结果、发起审批、查看审计、管理会话。

组件：

- FastAPI API
- 管理工作台 / 分析工作台
- 当前 Streamlit UI（过渡期保留）

### 2.2 编排层

职责：把一次请求变成一个可追踪任务流。

核心能力：

- session 管理
- 分析计划生成
- 工具路由
- 澄清与追问
- 审批与执行状态机

### 2.3 语义智能层

职责：完成任务理解、schema grounding、SQL 草拟、修复和解释。

核心能力：

- LLM Router
- Prompt Registry
- Catalog 检索
- Join Path 选择
- SQL Draft + Validate + Repair
- Answer / Chart Plan 生成

### 2.4 执行治理层

职责：所有真实执行都从这里通过，不区分读或写。

核心能力：

- policy gate
- query budget
- action catalog
- 审计日志
- 事务执行
- 快照与回滚

### 2.5 平台支撑层

职责：为全链路提供数据、缓存、评测和监控能力。

核心能力：

- metadata catalog
- vector / lexical index
- cache
- eval runner
- metrics / traces / logs
- model gateway

---

## 3. 读路径目标流程

1. 接收请求与会话上下文
2. 生成分析意图与缺失参数
3. 进行 schema grounding 和检索
4. 生成 SQL draft
5. 经过 AST / policy / budget 校验
6. 必要时进入 repair loop
7. 执行查询
8. 生成自然语言答案与图表方案
9. 记录会话事件与指标

---

## 4. 写路径目标流程

1. 接收自然语言操作请求
2. 映射到受支持的 action type
3. 提取参数并做业务校验
4. 生成 dry-run 计划与影响预估
5. 进入审批流
6. 通过 policy gate、事务和幂等校验
7. 执行并记录审计与快照
8. 生成回滚令牌和结果摘要

---

## 5. 目标代码目录架构

当前仓库继续把新能力平铺在 `app/core/` 下会越来越难维护，因为：

1. 同一层会混放业务编排、技术适配、执行细节和通用工具
2. `llm`、`sql`、`retrieval`、`security` 既像基础设施，又夹带业务逻辑
3. 后续加入 session、catalog、policy、actions 后，目录语义会进一步混乱

因此，目标代码结构不再建议采用“所有能力都进 `app/core`”的方式，而应改为“按层分顶层、按业务域分子层”的结构。

### 5.1 推荐结构

```text
app/
├── presentation/                # 表达层：对外入口、UI、请求/响应适配
│   ├── api/                     # FastAPI、routes、dependencies、transport schemas
│   └── ui/                      # Streamlit / 后续前端适配层
│
├── application/                # 应用层：编排、流程、用例、任务调度
│   ├── orchestration/          # ask_question、workflow、pipeline、router
│   ├── conversations/          # session、clarification、memory coordination
│   ├── analytics/              # read-only analysis use cases
│   └── actions/                # write action、approval、rollback use cases
│
├── domain/                     # 领域层：核心对象、规则、策略接口
│   ├── conversation/           # SessionContext、ConversationEvent 等
│   ├── catalog/                # CatalogMatch、schema snapshot、join edge
│   ├── query/                  # QueryIntent、SQLDraft、AnalysisArtifact
│   ├── governance/             # PolicyDecision、AuditEvent、RollbackToken
│   └── visualization/          # chart plan、chart spec、display artifact
│
├── infrastructure/             # 基础设施层：模型、检索、存储、执行、日志
│   ├── llm/                    # provider adapters、prompt registry、model gateway
│   ├── retrieval/              # lexical/vector/rerank/join path resolvers
│   ├── persistence/            # session store、catalog store、audit store
│   ├── execution/              # SQL execution、action execution、connectors
│   ├── security/               # auth、secrets、tenant isolation、guards
│   └── observability/          # logging、metrics、tracing、audit export
│
├── shared/                     # 跨层共享但不承载核心业务语义
│   ├── schemas/                # 纯传输对象 / DTO
│   ├── types/                  # 通用类型
│   └── utils/                  # 无业务含义的工具函数
│
└── config/                     # 配置、环境、feature flags
```

### 5.2 为什么不建议直接用简单 MVC

MVC 对页面驱动型应用是清晰的，但对当前这个系统不够精确。

如果直接分成 `model / view / controller`：

- `model` 会变成一个巨大杂物层，里面同时塞 domain、application、infrastructure
- LLM、retrieval、SQL、policy、audit 这类能力没有清晰落点
- 后续多轮 Agent 和写操作治理会让 `controller` 膨胀成流程黑洞

所以更适合当前项目的是：

- `presentation` 近似承担 MVC 中的 `view + controller` 边缘职责
- `domain` 承担真正的业务模型
- `application` 承担用例编排
- `infrastructure` 承担技术实现

这比简单 MVC 更适合 AI + 数据执行型系统。

### 5.3 当前到目标的迁移映射

| 当前路径 | 目标路径 | 说明 |
|---|---|---|
| `app/api/` | `app/presentation/api/` | API 入口、路由、依赖注入 |
| `app/ui/` | `app/presentation/ui/` | Streamlit 与后续工作台 |
| `app/core/orchestrator/` | `app/application/orchestration/` | pipeline、workflow、router |
| `app/core/memory/` | `app/application/conversations/` + `app/domain/conversation/` + `app/infrastructure/persistence/` | 会话编排、对象、存储分离 |
| `app/core/llm/` | `app/infrastructure/llm/` + `app/application/orchestration/` | provider 与 prompt 下沉到 infra，路由上移到 application |
| `app/core/retrieval/` | `app/infrastructure/retrieval/` + `app/domain/catalog/` | 检索实现与 catalog 对象分离 |
| `app/core/sql/` | `app/infrastructure/execution/` + `app/domain/query/` + `app/application/analytics/` | 执行器、领域对象、用例拆开 |
| `app/core/chart/` | `app/domain/visualization/` + `app/application/analytics/` | 图表对象与图表用例拆开 |
| `app/core/auth/` / `app/core/security/` | `app/infrastructure/security/` + `app/domain/governance/` | 技术鉴权与治理规则拆开 |
| `app/core/metrics.py` / `logging.py` | `app/infrastructure/observability/` | 观测能力统一收口 |
| `app/shared/` | `app/shared/` | 保留，但只放 DTO、types、utils |

### 5.4 当前阶段的实现原则

1. 先建立新目录骨架，不一次性暴力搬迁全部代码。
2. 先迁移新增模块，再逐步回收旧的 `app/core/*`。
3. 过渡期允许旧路径存在，但不再往旧平铺结构新增新能力。
4. 每完成一个专题，就把对应模块迁入新层级。

### 5.5 首批应进入新层级的新增模块

- `app/application/conversations/`
- `app/application/actions/`
- `app/domain/conversation/`
- `app/domain/governance/`
- `app/domain/catalog/`
- `app/infrastructure/persistence/`
- `app/infrastructure/observability/`

这些模块如果再落进 `app/core/`，后面几乎一定要二次拆迁。

---

## 6. 关键领域对象

必须统一定义以下对象：

- `SessionContext`
- `ConversationEvent`
- `TaskPlan`
- `ToolInvocation`
- `CatalogMatch`
- `PolicyDecision`
- `AuditEvent`
- `WriteActionRequest`
- `WriteActionApproval`
- `RollbackToken`
- `AnalysisArtifact`

这些对象应优先于具体实现落地，避免继续用字典和临时字段扩流程。

---

## 7. 架构约束

1. 所有模型调用都必须经过统一 provider 接口。
2. 所有执行都必须经过统一 policy gate。
3. 所有写操作都必须从 action catalog 进入，不允许任意 SQL 直通。
4. 所有会话状态都必须可追踪、可裁剪、可恢复。
5. 所有阶段都必须可评测、可观测。

---

## 8. 本文件的作用

本文件负责冻结架构边界。

- 与模型路由相关的迁移细节见 `12-llm-first-migration-plan.md`
- 与大库检索相关的设计见 `13-large-database-retrieval-plan.md`
- 与多轮 Agent 相关的设计见 `14-copilot-agent-plan.md`
- 与写操作治理相关的设计见 `15-governed-write-actions-plan.md`
