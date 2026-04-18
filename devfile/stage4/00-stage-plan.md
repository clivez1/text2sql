# stage4. 受治理动作与审批回滚

> 状态：未开始
> 更新：2026-04-18

---

## 1. 阶段目标

stage4 负责把系统从只读分析推进到受治理的数据动作系统。

核心目标：

1. 建立 action catalog。
2. 建立 dry-run、审批、审计、回滚骨架。
3. 禁止自由写 SQL，统一走受支持动作类型。

---

## 2. 阶段前置条件

1. stage3 的会话、工件和结果表达稳定。
2. domain/governance 和 infrastructure/execution 有稳定落位。

---

## 3. 阶段执行入口

1. stage4/01-governed-actions.md
2. stage4/02-approval-audit-rollback.md

---

## 4. 阶段验收标准

1. 没有 action catalog 的写请求不能执行。
2. 高风险动作必须经过 dry-run、审批和审计。
3. 真实写动作具有 rollback token 和幂等约束。