# 00. 主方案文档

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 项目终态

项目终态定义为三层目标：

1. 成熟轻量级 Text2SQL：支持中大型数据库的自然语言分析。
2. 多轮分析 Copilot：以 LLM 优先和 grounding 为主链路。
3. 受治理数据操作系统：具备审批、审计、回滚和幂等能力。

---

## 2. 主线原则

1. 单仓推进，不为整齐提前做过度工程化。
2. 先冻结边界，再迁移代码。
3. LLM 优先，但必须 grounding。
4. 工具化执行，而不是自由生成高风险动作。
5. 每个阶段都必须可验收、可回退、可追踪。

---

## 3. 阶段划分

| 阶段 | 目标 | 状态 | 入口 |
|---|---|---|---|
| stage0 | 文档治理与架构冻结 | 已完成 | stage0/00-stage-plan.md |
| stage1 | 仓库物理整理与代码重构 | 进行中 | stage1/00-stage-plan.md |
| stage2 | LLM 优先与 grounding 底座 | 未开始 | stage2/00-stage-plan.md |
| stage3 | 多轮 Copilot 与结果表达 | 未开始 | stage3/00-stage-plan.md |
| stage4 | 受治理动作与审批回滚 | 未开始 | stage4/00-stage-plan.md |
| stage5 | 评测、发布与生产门禁 | 未开始 | stage5/00-stage-plan.md |

---

## 4. 阶段流转规则

1. 未开始阶段的任务只出现在 02-pending.md。
2. 一旦启动某阶段，该阶段任务迁入 03-in-progress.md。
3. 阶段完成后，该阶段任务迁入 01-completed.md。
4. 04-temp-memory.md 只保留当前阶段的临时决策、风险和下一步，不保留长期历史。

---

## 5. 当前阶段结论

当前已经完成 stage0，正在执行 stage1。

stage1 的目标是：

1. 完成根目录和 app 的物理整理收束。
2. 把 app/core 的主逻辑分批迁入新分层。
3. 建立“新路径实现 + 旧路径兼容壳 + 最小验证”的重构节奏。

---

## 6. 目录使用规则

1. devfile 根目录只保留 00 到 04 五份入口文档。
2. 所有阶段性详细执行文档只放在 stage* 子目录。
3. 所有主题性背景、架构、经验和参考只放在 references/ 子目录。
4. archive/ 只承接旧版结构和历史快照，不作为当前执行入口。

---

## 7. 直接执行顺序

1. 先看 03-in-progress.md。
2. 再进入当前 stage 的 00-stage-plan.md。
3. 如需具体方案，进入当前 stage 目录下的详细文档。
4. 如需背景解释，再进入 references/ 对应主题文档。

---

## 8. 参考入口

1. references/architecture/：当前状态、目标架构、路线图参考。
2. references/themes/：LLM、Copilot、治理动作、评测与历史经验参考。

