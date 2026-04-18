# references/themes. 主题参考入口

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 本目录负责什么

本目录只承载主题参考方案，不承担当前阶段的直接执行职责。

这里的文档回答的是：

1. LLM 优先链路和 grounding 应该长成什么样。
2. 多轮 Copilot、可视化和受治理动作应共享什么底座。
3. 评测、发布、灰度和回归门禁应该如何冻结。

如果你的目标是：

- 执行当前阶段，去看对应 stage 目录
- 理解整体边界，去看 00-master-plan.md
- 查看架构背景，去看 references/architecture/

---

## 2. 阅读顺序

1. 01-llm-and-retrieval.md：理解 LLM 优先和中大型库 grounding
2. 02-copilot-visualization-and-actions.md：理解会话、artifact、治理动作
3. 03-evaluation-and-release.md：理解评测、门禁、发布与回归
4. 04-lessons-learned.md：查看阶段推进中的经验和约束

---

## 3. 与其他目录的分工

1. 根级 00-04 只负责总控、进度和临时记忆。
2. stage* 目录负责当前与未来阶段的详细执行方案。
3. 本目录只负责主题背景和长期参考，不直接展开文件级搬迁步骤。

---

## 4. 维护规则

1. 新的主题型方案优先进入本目录，不回流根级。
2. 如果主题文档开始出现阶段执行步骤，应把执行内容下沉到对应 stage 目录。
3. 如果主题文档开始出现临时工作记忆，应转入 04-temp-memory.md。