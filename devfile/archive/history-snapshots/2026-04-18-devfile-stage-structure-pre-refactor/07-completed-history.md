# 07. 已完成历史

> 状态：持续追加
> 更新：2026-04-18

---

## 1. 主线切换记录

- 2026-04-18：完成代码重构启动包，新增 20-code-migration/07-refactor-kickoff.md，把 devfile 从“可读”推进到“可直接开工”
- 2026-04-18：完成 devfile 根级收束，新增 30-capability-topics/ 专题子目录，根级只保留总控、执行入口、历史与参考
- 2026-04-18：完成 devfile 执行层细化，新增 10-repository-physical-reorg/ 与 20-code-migration/ 两套子文档树，用于直接承接逐目录整理和逐层代码迁移
- 2026-04-18：完成 devfile 重编编号，主文档收束为 00-08，旧 00-09、旧 10-17 和 frp 文档已快照归档
- 2026-04-18：完成仓库级架构讨论定版，不再只优化 app，而是同时冻结根目录、app、docs、devfile 的边界
- 2026-04-18：完成 app 分层骨架建立，新增 presentation、application、domain、infrastructure
- 2026-04-18：完成 provider 协议层首轮骨架，已支持 OpenAI compatible、Anthropic messages、local gateway

---

## 2. 关键阶段里程碑

| 阶段 | 状态 | 时间 |
|---|---|---|
| MVP 主链路 | 完成 | 2026-04-07 |
| 多数据库支持 | 完成 | 2026-04-08 |
| SQL 安全校验 | 完成 | 2026-04-08 |
| 图表推荐 | 完成 | 2026-04-09 |
| LLM 兼容层 | 完成 | 2026-04-09 |
| Phase 0-3 工程化 | 完成 | 2026-04-11 |
| 覆盖率 80%+ 基线 | 完成 | 2026-04-11 |
| 可观测性和认证骨架 | 完成 | 2026-04-11 |
| Round 4 架构评审 | 完成 | 2026-04-15 |
| Round 5 数据与运行态分离 | 完成 | 2026-04-16 |
| Round 6 移除 Vanna 和 N-provider fallback | 完成 | 2026-04-17 |

---

## 3. 关键完成项摘要

### 3.1 Round 4

- 规则从硬编码迁到 YAML
- SchemaRetriever 抽象落地
- 数据库层完成阶段性消重

### 3.2 Round 5

- .deploy、data、datasets 边界建立
- 运行时向量库和日志从版本化数据中分离

### 3.3 Round 6

- Vanna 完全移除
- LLM provider 支持按 1..N 配置 fallback
- 旧的 resilient_llm 和 resilient_client 清理完成

### 3.4 当前主线切换

- 最终目标方案落入 00-master-plan.md
- 仓库级加代码级目标架构落入 02-target-architecture.md
- 执行方案落入 10-repository-physical-reorg/ 和 20-code-migration/
- 专题方案下沉到 30-capability-topics/

---

## 4. 验证记录

- 历史全量测试基线：265 passed，2 skipped，覆盖率 80%
- Provider 协议层定向验证：tests/unit/test_settings.py、tests/unit/test_llm_client.py、tests/unit/test_llm_adapters.py 共 12 项通过
- 分层骨架最小导入验证：新增的 presentation、application、domain、infrastructure 包可成功导入

---

## 5. 历史明细位置

本文件只保留主干里程碑。

更细的历史文本见：

- archive/history-snapshots/2026-04-18-final-target-baseline/
- archive/history-snapshots/2026-04-18-devfile-reindex/