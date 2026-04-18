# stage2-01. Router 与协议层

> 状态：未开始
> 更新：2026-04-18

---

## 1. 目标

1. 建立 LLM 优先 router。
2. 保留 provider 协议抽象的统一边界。
3. 把 routing 决策明确放在 application，而不是 infrastructure。

---

## 2. 关键工作项

1. 固化 OpenAI compatible、Anthropic messages、local gateway 三类协议。
2. 统一健康检查、错误分类、重试、预算和 fallback 顺序。
3. 让 router 输出稳定的 QueryIntent、GroundingPackage、SQLDraft 边界对象。

---

## 3. 代码落点

1. infrastructure/llm/：adapter、client、health_check、prompts。
2. application/orchestration/：sql_router、query_workflow。
3. domain/query/：QueryIntent、SQLDraft、ValidationIssue。

---

## 4. 参考

1. references/themes/01-llm-and-retrieval.md
2. references/architecture/01-target-architecture.md