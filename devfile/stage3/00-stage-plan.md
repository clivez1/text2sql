# stage3. 多轮 Copilot 与结果表达

> 状态：未开始
> 更新：2026-04-18

---

## 1. 阶段目标

stage3 负责把系统从“单轮问答 + 附带图表”推进到“多轮分析 Copilot + 统一结果工件”。

核心目标：

1. 建立会话状态机和 session state。
2. 建立 analysis artifact、chart plan、chart spec。
3. 让总结、图表和导出进入同一条分析主链路。

---

## 2. 阶段前置条件

1. stage2 的 router、grounding、domain 对象边界已具备稳定输入输出。
2. application/conversations、application/analytics、domain/visualization 已有稳定落位。

---

## 3. 阶段执行入口

1. stage3/01-conversation-and-copilot.md
2. stage3/02-visualization-and-artifacts.md

---

## 4. 阶段验收标准

1. 系统可以对歧义问题发起澄清。
2. 多轮追问可以复用上一轮 grounding 与结果。
3. 图表与导出不再是零散附属逻辑，而是统一 artifact 的一部分。