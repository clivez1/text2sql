# 仓库物理整理执行入口

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 本目录负责什么

本目录只负责“物理整理”，不直接讨论算法或模型能力。

它解决的是下面这些问题：

1. 仓库根目录哪些文件和目录可以长期留在根上。
2. 哪些目录是产品目录，哪些只是运行时、测试、临时或历史区域。
3. 每个现有目录未来应该长成什么样。
4. 仓库整理应该按什么顺序做，避免一边迁代码一边把路径打乱。

如果你的目标是“开始真正搬目录、收拾历史区、整理脚本和文档区”，先看这里。

如果你的目标是“开始迁代码实现”，转到 stage1/02-code-refactor/。

---

## 2. 阅读顺序

1. 01-root-and-generated-zones.md：先冻结根目录与本地生成区边界
2. 02-app-physical-structure.md：再冻结 app 的物理落位与旧目录退出方式
3. 03-data-runtime-and-assets.md：再处理 data、datasets、.deploy
4. 04-scripts-tests-docs-devfile.md：再整理 scripts、tests、docs、devfile
5. 05-engineering-and-legacy-zones.md：最后处理 .github、evolution、app/app 和历史残留
6. 06-repo-reorganization-checklist.md：按批次执行并验收

---

## 3. 覆盖范围

| 路径 | 对应文档 |
|---|---|
| 根目录稳定入口、隐藏目录、缓存输出 | 01-root-and-generated-zones.md |
| app/ | 02-app-physical-structure.md |
| data/、datasets/、.deploy/ | 03-data-runtime-and-assets.md |
| scripts/、tests/、docs/、devfile/ | 04-scripts-tests-docs-devfile.md |
| .github/、evolution/、app/app/、根目录遗留产物 | 05-engineering-and-legacy-zones.md |

---

## 4. 使用方式

每份文档都按同一结构展开：

1. 当前问题
2. 目标结构
3. 迁移规则
4. 执行顺序
5. 验收标准

这样做的目的是让目录整理不是“想搬就搬”，而是可以按阶段做、做完可验收。

---

## 5. 与 stage1/02-code-refactor/ 的关系

本目录回答的是“文件夹应该放在哪里”。

stage1/02-code-refactor/ 回答的是“代码职责应该迁到哪里，以及怎么分批 cutover”。

执行时遵守以下原则：

1. 先冻结物理落位，再动大规模代码迁移。
2. 物理整理不应先于 import cutover 破坏运行路径。
3. 只要某个目录仍承接运行流量，就先用兼容壳而不是直接删除。