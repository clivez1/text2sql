# 20. 代码迁移执行入口

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 本目录负责什么

本目录只回答一个问题：

在已经冻结了目标目录结构之后，现有代码应该怎么按层、按批、按风险迁过去。

这里不再抽象讨论“应该分层”，而是直接给出：

1. 哪些旧模块先迁。
2. 每个模块迁到哪一层。
3. 哪些文件需要拆分而不是平移。
4. cutover 时怎样保留兼容壳。
5. 每一批迁完后如何验证。

---

## 2. 阅读顺序

1. 07-refactor-kickoff.md：先确认现在该怎么直接开工
2. 01-infrastructure-migration.md：先迁技术边界最清晰的基础设施层
3. 02-application-migration.md：再迁 workflow、会话和用例编排
4. 03-domain-migration.md：再固化领域对象和中间工件
5. 04-presentation-and-entrypoints.md：再切 API 和 UI 入口
6. 05-shared-config-rules-migration.md：最后收束 shared、config、rules 和横切模块
7. 06-cutover-batches-and-acceptance.md：按统一批次执行与验收

---

## 3. 总体迁移原则

1. 先建立新路径，再迁旧代码。
2. 优先迁叶子模块，再迁编排模块。
3. 能平移的先平移，必须拆分的再拆分。
4. 迁移期间允许旧路径做 re-export wrapper，但 wrapper 只能临时存在。
5. 每个 batch 结束后都要有最小测试和 import 验证。

---

## 4. 本目录覆盖范围

| 范围 | 对应文档 |
|---|---|
| llm、retrieval、execution、security、observability、data_import 技术组件 | 01-infrastructure-migration.md |
| orchestration、analytics、conversations、actions、nlu、explain | 02-application-migration.md |
| query、catalog、conversation、governance、visualization 核心对象 | 03-domain-migration.md |
| FastAPI、Streamlit、HTTP middleware、错误处理和 presenter | 04-presentation-and-entrypoints.md |
| shared、config、rules、validators、rate_limiter 等横切区 | 05-shared-config-rules-migration.md |
| 统一批次、兼容策略、删除旧目录时机和验收标准 | 06-cutover-batches-and-acceptance.md |
| 现在就开始重构时的直接入口和首批动作 | 07-refactor-kickoff.md |

---

## 5. 与 10-repository-physical-reorg/ 的关系

10- 目录定义“目标目录应该长什么样”。

20- 目录定义“旧代码怎样迁到那个目标目录”。

执行时顺序固定为：

1. 先看 10-02 冻结 app 物理落位。
2. 再先看 07-refactor-kickoff.md 确认当前启动批次。
3. 再按 20- 的批次迁代码。
4. 等 20-06 的 cutover 条件满足后，再删除旧目录。