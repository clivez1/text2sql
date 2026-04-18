# stage3-02. 可视化与分析工件

> 状态：未开始
> 更新：2026-04-18

---

## 1. 目标

1. 建立统一 analysis artifact。
2. 让 chart plan、chart spec、summary、export payload 进入同一结果对象。
3. 让 UI 渲染和导出都基于稳定工件，而不是临时字段。

---

## 2. 关键工作项

1. 定义 AnalysisArtifact、ChartPlan、ChartSpec、ExportArtifact。
2. 将结果总结、图表规划和导出逻辑迁入 application/analytics。
3. 保留启发式图表推荐作为降级策略，但主规划由新工件驱动。

---

## 3. 代码落点

1. domain/visualization/
2. application/analytics/
3. presentation/ui/

---

## 4. 参考

1. references/themes/02-copilot-visualization-and-actions.md