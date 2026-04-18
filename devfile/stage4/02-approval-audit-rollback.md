# stage4-02. 审批、审计与回滚

> 状态：未开始
> 更新：2026-04-18

---

## 1. 目标

1. 让高风险动作具备审批链。
2. 让每次执行都具备审计记录和快照。
3. 让每次真实写入都具备 rollback 能力。

---

## 2. 写路径生命周期

1. 识别 action type。
2. 提取参数并做 policy pre-check。
3. 生成 dry-run 和影响预估。
4. 进入审批。
5. 执行事务。
6. 写入审计与快照。
7. 返回 rollback token。

---

## 3. 代码落点

1. application/actions/
2. domain/governance/
3. infrastructure/execution/

---

## 4. 参考

1. references/themes/02-copilot-visualization-and-actions.md