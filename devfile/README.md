# README

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 项目总体

本目录用于推进 Text2SQL 项目的开发方案与阶段执行，不承载用户使用手册。

当前目标是把项目推进为：

1. 支持中大型数据库的成熟轻量级 Text2SQL 系统。
2. 以 LLM 优先和 grounding 为核心的数据分析 Copilot。
3. 具备审批、审计和回滚能力的受治理数据操作系统。

---

## 2. 根目录说明

devfile 根目录只保留入口型文档：

1. 00-master-plan.md：主方案文档。
2. 01-completed.md：已完成任务与已完成阶段。
3. 02-pending.md：未完成任务与未启动阶段。
4. 03-in-progress.md：当前进行中阶段与当前执行任务。
5. 04-temp-memory.md：临时记忆、当前决策和下一步提醒。

根目录不放具体执行清单。

---

## 3. 子目录说明

1. stage0 到 stage5：按主方案阶段拆分的详细执行文档。
2. references/：按主题组织的参考方案文档。
3. archive/：历史快照和旧版文档结构归档。

---

## 4. 当前阅读顺序

1. 先读 00-master-plan.md。
2. 再看 03-in-progress.md 确认当前阶段。
3. 进入对应 stage 目录执行。
4. 如需补充背景，再看 references/ 下的主题参考文档。

---

## 5. 当前状态

当前已完成 stage0，已启动 stage1。

当前直接开工时，先看 stage1/00-stage-plan.md，再进入 stage1/02-code-refactor/07-refactor-kickoff.md。
