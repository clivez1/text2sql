# Devfile 导航

> 状态：当前开发主入口
> 更新：2026-04-18

---

## 1. 阅读顺序

建议按下面顺序读：

1. 00-master-plan.md：先理解终态目标和总方针
2. 01-current-state.md：再看当前仓库结构、能力边界和主要问题
3. 02-target-architecture.md：看整体目标架构和方案取舍
4. 03-execution-roadmap.md：看当前窗口、阶段安排和迁移顺序
5. 10-repository-physical-reorg/：按仓库目录逐个执行物理整理
6. 20-code-migration/07-refactor-kickoff.md：直接进入代码重构启动包
7. 30-capability-topics/：按能力专题补充目标约束与验收口径
8. 07-08：回看历史完成项和参考资料

---

## 2. 当前文档结构

### 2.1 主控文档

- 00-master-plan.md：终态定义、版本路径和全局约束
- 01-current-state.md：当前边界、根目录职责、app 过渡状态
- 02-target-architecture.md：仓库级加代码级目标架构方案
- 03-execution-roadmap.md：阶段路线、当前窗口和迁移顺序

### 2.2 执行子目录

- 10-repository-physical-reorg/：逐目录物理整理、旧区清退和仓库落位清单
- 20-code-migration/：infrastructure、application、domain、presentation 的分批迁移方案，直接启动入口是 07-refactor-kickoff.md

### 2.3 专题子目录

- 30-capability-topics/：按能力主题收纳 LLM 与检索、Copilot 与治理动作、评测与发布

### 2.4 历史和参考

- 07-completed-history.md：关键完成记录和里程碑
- 08-reference.md：仍有价值的旧经验和参考摘要

### 2.5 归档区

- archive/history-snapshots/2026-04-18-final-target-baseline/：最终目标主线切换前快照
- archive/history-snapshots/2026-04-18-devfile-reindex/：本次重编编号前的 devfile 快照

---

## 3. 文档职责约束

- devfile 只承载规划、阶段、架构与决策，不承载用户使用说明。
- docs 只承载当前可运行系统的使用、配置、API 与部署说明。
- 00-03 负责总览、现状、目标和路线；10- 和 20- 子目录负责执行方案；30- 目录负责能力专题；07-08 负责历史和参考。
- archive 只保留历史材料，不再继续作为当前主线入口。

---

## 4. 当前阶段

当前阶段已经从“只优化 app 目录”切到“同步优化仓库级结构和 app 分层”的窗口。

本轮之后，主线重点变成：

1. 冻结根目录与文档边界
2. 推进 app/core 到新分层目录的迁移
3. 完成 LLM 优先和大库检索底座
4. 在统一会话与工具层上叠加 Copilot、可视化与治理能力

当前直接执行时，先看 10-repository-physical-reorg/，再看 20-code-migration/07-refactor-kickoff.md；需要专题目标时，再进入 30-capability-topics/。
