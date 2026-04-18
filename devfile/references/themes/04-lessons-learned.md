# 参考摘要与经验教训

> 状态：保留参考
> 更新：2026-04-18

---

## 1. 仍然有价值的旧经验

### 1.1 本地优先经验

旧方案里的“本地优先”并没有失效，但角色已经改变。

现在应理解为：

- 本地规则仍然有价值
- 但它们不再是主路由判断器
- 它们更适合作为 few-shot、修复、兜底和回归资产

### 1.2 快速 fallback 经验

旧系统在简单问题上依靠 fast fallback 获得过明显延迟收益。

这条经验仍然保留，但新的位置应该是：

- 作为 LLM 优先主链路失败时的兜底
- 而不是继续决定是否要调用 LLM

---

## 2. 性能基线参考

历史记录中的参考值：

- GET /health 平均约 23 ms
- GET /schemas 平均约 9 ms
- 旧 ask 主链路曾在 28 到 36 秒之间
- fast fallback 之后，简单问题曾压到约 1.19 秒

这些数字不是当前验收标准，但仍可作为旧基线参考。

---

## 3. 一致性教训

历史上出现过的典型问题：

1. settings 与实际调用链不一致
2. pipeline 返回类型和实际返回不一致
3. README、docs、devfile 口径漂移
4. UI 直接 import pipeline，导致入口边界混乱

这也是本轮必须同时收束仓库结构和文档结构的原因。

---

## 4. 当前开发约定

1. docs 讲当前运行态。
2. devfile 根级只讲主方案、进度和临时记忆；详细执行放 stage*，主题背景放 references/。
3. archive 存历史，不存当前主线。
4. 新能力优先进入 app 新分层，不再继续扩旧 core。

---

## 5. 历史材料位置

如果需要看更原始的旧轮次讨论，可去：

- archive/history-snapshots/2026-04-18-final-target-baseline/
- archive/history-snapshots/2026-04-18-devfile-reindex/
- archive/ 其他历史目录