# Text2SQL-0412 待完成文档

> 2026-04-17 更新

---

## 已完成：Round 6 全面重构

Round 6（移除 Vanna + N-Provider Fallback + 代码清理）已完成，详见 `devfile/01-completed.md`。

---

## 待修复（Nice-to-have）

| 问题 | 说明 |
|------|------|
| 修复 7 个预存测试失败 | 3 executor API mismatch + 2 missing openpyxl + 2 missing Linux font on Windows |

---

## 长期目标（不进入当前冲刺）

| 方向 | 说明 |
|------|------|
| Pipeline Stage 化 | 编排能力增强 |
| FAISS / PGVector 实现 | 等 benchmark 数据驱动 |
| JWT 认证替代 API Key | 多用户/租户场景 |
| Prometheus / Grafana | 企业级可观测性 |

---

_最后更新：2026-04-17_
