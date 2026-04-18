# 03. 执行路线图

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 当前阶段

当前阶段已经从“补规则和补演示能力”切换到“冻结整体架构并开始迁移”的窗口。

本轮文档收束完成后，接下来的主线不再是继续扩旧结构，而是按新的仓库分区和 app 分层推进代码迁移。

---

## 2. 阶段划分

### Phase A：文档与边界冻结

目标：

- 完成 devfile 重编编号
- 冻结根目录职责和 docs/devfile 分工
- 冻结整体目标架构和迁移原则

状态：本轮完成

### Phase B：app 分层迁移起步

目标：

- 明确 app/core 迁移次序
- 把新增模块优先放入新分层
- 开始迁移 infrastructure 和 application 相关模块

### Phase C：LLM 优先和大库检索底座

目标：

- 建立 LLM 优先 Router
- 建立 validation 和 repair loop
- 建立 metadata catalog 和 grounding package

### Phase D：多轮 Copilot 和结果表达

目标：

- 真正引入 session state
- 接入工具调用和事件流
- 把图表规划和导出纳入主链路

### Phase E：受治理写操作

目标：

- 引入 action catalog
- 建立审批、审计、快照和回滚能力
- 从只读系统升级为受治理的数据操作系统

### Phase F：评测、发布和回归

目标：

- 建立评测集、基线报告、版本门禁
- 建立只读、多轮、可视化、写操作的统一回归机制

---

## 3. 当前窗口重点

### 3.1 P0

- 完成 app/core 到新分层的优先级映射
- 从 LLM router、会话对象、policy 对象和 analysis artifact 开始真正落代码骨架
- 把新的执行入口优先放到 application 和 infrastructure
- 按 10-repository-physical-reorg/ 冻结逐目录物理整理顺序
- 按 20-code-migration/ 冻结逐层代码迁移批次和 cutover 规则
- 以 20-code-migration/07-refactor-kickoff.md 作为正式进入代码重构阶段的统一入口

### 3.2 P1

- 整理 scripts 的分类方式，区分 bootstrap、verify、evaluate
- 让 tests 的目录组织更贴近新架构分区
- 同步修正 docs/architecture.md 等公开文档的运行态描述

### 3.3 P2

- 评估是否需要进入第三轮根目录规范化
- 再决定是否引入更重的根目录分区策略

---

## 4. 代码迁移顺序

### 4.1 第一批

- infrastructure/llm/
- infrastructure/retrieval/
- infrastructure/execution/
- infrastructure/observability/

理由：这些模块技术边界最清晰，而且已经开始出现新旧并行迹象。

### 4.2 第二批

- application/orchestration/
- application/conversations/
- application/analytics/

理由：编排层决定后续 LLM 优先、多轮和结果表达的主链路。

### 4.3 第三批

- domain/query/
- domain/catalog/
- domain/conversation/
- domain/governance/
- domain/visualization/

理由：领域对象要在主链路和接口稳定后逐步固化。

### 4.4 第四批

- presentation/api/
- presentation/ui/

理由：入口层要跟着编排层变化，避免过早做重复适配。

---

## 5. 当前阶段完成标准

当以下条件满足时，当前阶段结束：

1. 根目录职责、docs/devfile 分工和 archive 策略稳定
2. app/core 的迁移次序明确，且新能力已不再进入旧平铺结构
3. LLM 优先 Router 的骨架开始替代旧规则优先主路由
4. 后续专题文档可以直接承接代码迁移，不再需要重新解释目录边界

---

## 5.1 当前直接启动建议

如果现在开始动代码，当前建议的启动顺序是：

1. 完成 M0 的新路径补齐和 import 可用性检查
2. 立即开始 M1 的 observability + security 迁移
3. 紧接着做 M2 的最小 domain 对象收束
4. 再进入 M3 的 LLM transport + retrieval 迁移

也就是先迁叶子模块和边界对象，再进入 application 主链路。

---

## 6. 当前禁止事项

1. 不再往 app/core 新增大块新能力。
2. 不在没有 policy gate 的情况下开放写操作。
3. 不在没有 grounding 能力的情况下把大库支持仅理解为“加更多别名”。
4. 不为了目录整齐而提前做高成本根目录大搬家。

---

## 7. 关联文档

- 00-master-plan.md：总方案
- 02-target-architecture.md：目标架构边界
- 20-code-migration/07-refactor-kickoff.md：当前直接重构入口
- 30-capability-topics/01-llm-and-retrieval.md：LLM 优先和大库检索
- 30-capability-topics/02-copilot-visualization-and-actions.md：多轮、可视化与治理动作
- 30-capability-topics/03-evaluation-and-release.md：评测与门禁
- 10-repository-physical-reorg/：仓库逐目录物理整理方案
- 20-code-migration/：逐层代码迁移和 cutover 方案