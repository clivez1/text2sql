# stage3-01. 会话与 Copilot 编排

> 状态：未开始
> 更新：2026-04-18

---

## 1. 目标

1. 引入可追踪的会话状态机。
2. 让 Copilot 具备澄清、追问、规划和工具协同能力。
3. 让 session_id 进入真正的主链路，而不只停留在 API schema。

---

## 2. 关键工作项

1. 定义 SessionContext、ConversationEvent、ToolInvocation。
2. 建立 received、clarifying、planning、retrieving、drafting、executing、summarizing 等状态。
3. 建立会话级摘要和工具调用轨迹。

---

## 3. 代码落点

1. application/conversations/
2. application/orchestration/
3. domain/conversation/

---

## 4. 参考

1. references/themes/02-copilot-visualization-and-actions.md
2. references/architecture/01-target-architecture.md