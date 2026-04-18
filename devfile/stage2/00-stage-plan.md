# stage2. LLM 优先与 grounding 底座

> 状态：未开始
> 更新：2026-04-18

---

## 1. 阶段目标

stage2 负责把系统从“规则优先、LLM 补充”推进到“LLM 优先、grounding 约束”。

核心目标：

1. 建立真正的 LLM router。
2. 建立 grounding package 和 catalog 对象。
3. 建立 validation 与 repair loop。

---

## 2. 阶段前置条件

1. stage1 已完成首批代码迁移。
2. infrastructure/llm、infrastructure/retrieval、domain/query、domain/catalog 有明确稳定落位。

---

## 3. 阶段执行入口

1. stage2/01-router-and-protocols.md
2. stage2/02-grounding-and-catalog.md

---

## 4. 阶段验收标准

1. 简单问题不再依赖 needs_llm=False 才能进入主链路。
2. grounding package 可以稳定支撑 SQL 草拟。
3. 本地规则角色降级为 few-shot、repair、fallback 和 regression 资产。