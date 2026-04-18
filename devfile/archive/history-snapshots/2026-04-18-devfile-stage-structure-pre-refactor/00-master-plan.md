# Text2SQL 最终目标总方案

> 项目：text2sql-0412
> 状态：当前生效
> 更新：2026-04-18

---

## 1. 目标重定义

当前项目已经具备演示级 Text2SQL 闭环，但还不是最终目标系统。

本轮主线把项目终态定义为：

1. 一个支持中大型数据库自然语言分析的成熟轻量级 Text2SQL 系统
2. 一个真正 LLM 优先、支持多轮分析与工具调用的数据分析 Copilot 平台
3. 一个受治理、可审批、可审计、可回滚的数据操作系统

这里的“轻量级”不是能力弱，而是：

- 单仓可部署
- 目录与职责清晰
- 运行面、治理面、规划面边界明确
- 可从云模型平滑过渡到本地模型网关
- 先做强约束，再逐步放开能力

---

## 2. 这轮方案的变化

这次不再只优化 app 目录，而是把整个仓库作为一个完整产品来定版。

需要同时优化四个视角：

1. 仓库级结构：源码、数据、工具、测试、文档、规划的边界
2. 代码级结构：app 内部的 presentation、application、domain、infrastructure 分层
3. 运行时结构：请求如何从入口走到规划、检索、执行、治理和结果表达
4. 文档级结构：docs 和 devfile 如何各司其职，archive 如何承接历史

如果只优化 app，而不处理根目录和 devfile，后续仍会出现“代码渐渐变清楚，但仓库整体越来越乱”的问题。

---

## 3. 最终目标范围

### 3.1 必须达到的能力

#### A. 中大型数据库自然语言分析

- 支持 SQLite、MySQL、PostgreSQL，后续可扩更多 SQL 方言
- 支持千表级 schema grounding、候选表列映射和 join path 选择
- 支持业务语义层、指标维度层和 schema 版本化

#### B. LLM 优先主链路

- 问题理解、检索规划、SQL 草拟、解释生成优先由 LLM 完成
- 本地规则降级为 few-shot 资产、修复资产、兜底模板和回归资产
- 支持主模型加 fallback 模型序列
- 支持 OpenAI 兼容协议、Anthropic messages 协议和本地模型网关

#### C. 多轮分析 Copilot

- 支持会话记忆、澄清、追问、分析步骤拆分、工具调用和输出整理
- 支持从“问一个问题”升级到“完成一个分析任务”
- 支持查询、解释、图表、导出、审批在同一会话里协作

#### D. 受治理写操作

- 默认禁止自由写 SQL
- 只允许受治理的参数化动作和审批式执行
- 必须具备 dry-run、影响预估、审批、事务、审计、快照、回滚和幂等

#### E. 结果表达层

- 不止返回表格，而是返回可解释、可视化、可导出的分析结果
- 图表规划和结果表达进入主链路，而不是继续停留在启发式附属能力

---

## 4. 非目标

以下目标不进入当前主线：

- 开放式通用浏览器 Agent
- 无治理的任意写操作系统
- 一开始就拆成复杂微服务平台
- 一开始就支持全部异构数据源和全部 BI 场景
- 无约束 DDL、跨租户写入和不可逆大批量删除

---

## 5. 核心设计原则

1. LLM 优先，但必须 grounding。
2. 策略先于执行。
3. 工具化而非自由生成。
4. 协议优先于供应商。
5. 单仓渐进式演进，先整理结构，再迁移代码。
6. 先评测，再扩能力。

---

## 6. 最终架构视图

### 6.1 仓库级视图

仓库最终要形成六个稳定区：

- 产品源码区：app
- 数据资产区：data、datasets、.deploy
- 工具脚本区：scripts
- 质量验证区：tests
- 当前使用文档区：docs
- 规划与归档区：devfile

### 6.2 代码级视图

app 内部采用分层加分域结构：

- presentation：API、UI、transport adapters
- application：workflow、use case、会话编排、action orchestration
- domain：核心业务对象、策略和规则
- infrastructure：LLM、检索、执行、存储、安全、观测
- shared：DTO、types、utils
- config：配置与 feature flags

旧的 app/core 在过渡期继续存在，但进入“只减不增”状态。

### 6.3 运行时视图

最终运行链路由五层构成：

1. 入口层：FastAPI、当前 Streamlit、后续工作台
2. 编排层：会话状态机、任务规划、工具路由、审批流
3. 语义智能层：LLM Router、Prompt Registry、Catalog 检索、SQL Repair
4. 执行治理层：Policy Gate、Action Catalog、Query Executor、Audit、Rollback
5. 平台支撑层：Catalog 索引、缓存、评测、监控、模型网关

详细设计见 02-target-architecture.md。

---

## 7. 版本路径

### V1：成熟轻量级只读 Text2SQL

- LLM 优先主链路
- 中大型库检索基础能力
- 只读生产化安全与评测

### V1.5：多轮分析 Copilot 加可视化

- 会话记忆
- 澄清与追问
- 图表规划与导出

### V2：受治理写操作

- 参数化动作
- 审批流
- 审计与回滚

### V2.5：本地模型优先企业版

- 本地模型网关进入主模型位
- 云模型保留为 fallback 或专项能力补充

---

## 8. 执行顺序

从本文件生效开始，项目主线按以下顺序推进：

1. 先冻结仓库级结构和 app 目标分层
2. 再重构 LLM 优先链路和 provider 协议层
3. 再建设 metadata catalog 与大库检索
4. 再补齐多轮 Copilot 与结果表达层
5. 最后解锁受治理写操作
6. 全程配套评测、发布与回归

不再继续以“补规则、补模板、补演示库问题”为主线推进。

---

## 9. 文档地图

- 01-current-state.md：当前仓库结构、能力边界与问题清单
- 02-target-architecture.md：仓库级加代码级目标架构，以及多轮方案取舍
- 03-execution-roadmap.md：执行路线、当前窗口和迁移顺序
- 30-capability-topics/01-llm-and-retrieval.md：LLM 优先链路与中大型库检索方案
- 30-capability-topics/02-copilot-visualization-and-actions.md：Copilot、多轮会话、可视化与受治理动作
- 30-capability-topics/03-evaluation-and-release.md：评测、发布、门禁与回归
- 07-completed-history.md：历史完成记录和里程碑
- 08-reference.md：保留参考资料和旧经验提炼
- 10-repository-physical-reorg/：逐目录物理整理方案与仓库落位清单
- 20-code-migration/：按层分批的代码迁移与 cutover 方案

---

## 10. 当前要求

当前阶段所有新增规划和新增代码都遵守以下约束：

1. docs 只描述当前可运行系统，不承载未来架构主方案。
2. devfile 根级只承载总控、历史和参考；执行与专题细节下沉到子目录，不再回流根级。
3. app/core 不再承接新能力，新增模块优先进入分层目录。
4. scripts 不承载核心业务逻辑，只承载初始化、验证和工具任务。
5. data、datasets、.deploy 三者必须持续分离，不混用。

