# 30. 能力专题入口

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 本目录负责什么

本目录只承载能力专题方案，不再承担总控导航和迁移批次职责。

这里的文档回答的是：

1. LLM 优先链路和 grounding 应该长成什么样。
2. 多轮 Copilot、可视化和受治理动作应共享什么底座。
3. 评测、发布、灰度和回归门禁应该如何冻结。

如果你的目标是：

- 按目录整理仓库，去看 10-repository-physical-reorg/
- 按批次迁移代码，去看 20-code-migration/
- 先理解整体边界，去看 00-03 根级总控文档

---

## 2. 阅读顺序

1. 01-llm-and-retrieval.md：理解 LLM 优先和中大型库 grounding
2. 02-copilot-visualization-and-actions.md：理解会话、artifact、治理动作
3. 03-evaluation-and-release.md：理解评测、门禁、发布与回归

---

## 3. 与其他目录的分工

1. 根级 00-03 只负责总控、边界和路线。
2. 10-repository-physical-reorg/ 只负责物理目录整理。
3. 20-code-migration/ 只负责按层迁移代码和 cutover。
4. 本目录只负责定义专题目标和专题约束，不直接展开文件级搬迁步骤。

---

## 4. 维护规则

1. 新的能力专题优先进入本目录，不回流根级。
2. 如果专题文档开始出现文件级迁移步骤，应把执行内容下沉到 20-code-migration/。
3. 如果专题文档开始出现目录搬迁说明，应把物理整理内容下沉到 10-repository-physical-reorg/。