# 03. 进行中任务

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 当前阶段

当前进行中阶段：stage1

阶段目标：仓库物理整理与代码重构。

---

## 2. 当前执行任务

### A. 物理整理线

1. 复查 app、scripts、tests、docs、devfile 的物理落位是否与阶段方案一致。
2. 继续把旧执行文档和历史结构从根目录移出，保持 devfile 根目录整洁。
3. 确认 stage1 内部文档引用全部切到新路径。

### B. 代码重构线

1. 执行 M0：补齐首批新路径和 import 骨架。
2. 执行 M1：迁移 observability 与 security 低风险模块。
3. 执行 M2：建立最小 domain 对象边界。
4. 执行 M3：迁移 LLM transport 与 retrieval。

---

## 3. 当前批次的直接入口

1. stage1/00-stage-plan.md：stage1 总入口。
2. stage1/01-repository-physical-reorg/00-README.md：物理整理入口。
3. stage1/02-code-refactor/07-refactor-kickoff.md：直接重构入口。

---

## 4. 当前阶段完成标准

stage1 结束前应满足：

1. 新路径开始承接真实实现文件，而不是只有目录骨架。
2. 至少一组旧 core 模块已转为兼容壳。
3. 主链路开始从旧平铺结构切向新分层结构。
4. 后续 stage2 所需的 router、catalog、domain 边界具备落位条件。

---

## 5. 当前阶段的下一步

下一步默认动作是：

1. 先执行 stage1 的低风险代码迁移。
2. 每完成一批后复查 import、测试和文档引用。
3. 复查通过后，再推进下一批。