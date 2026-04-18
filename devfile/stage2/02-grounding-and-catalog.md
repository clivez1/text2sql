# stage2-02. Grounding 与 Catalog

> 状态：未开始
> 更新：2026-04-18

---

## 1. 目标

1. 让检索从演示片段召回升级为可执行 schema grounding。
2. 建立 catalog、join path、metric 和 dimension 的稳定对象边界。
3. 让检索结果直接服务于 SQL 草拟和修复。

---

## 2. 关键工作项

1. 建立 metadata catalog 数据模型。
2. 建立 grounding package，至少包含 top tables、top columns、join edges、examples、risk hints。
3. 建立 lexical、vector、join graph 和 rerank 组合检索链路。

---

## 3. 代码落点

1. infrastructure/retrieval/
2. domain/catalog/
3. domain/query/

---

## 4. 参考

1. references/themes/01-llm-and-retrieval.md
2. references/architecture/00-current-state.md