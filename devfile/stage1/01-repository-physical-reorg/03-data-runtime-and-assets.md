# data、datasets、.deploy 整理方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 当前问题

data、datasets、.deploy 三者已经初步分离，但还没有形成真正可执行的长期约束。

主要问题：

1. data 与 datasets 都叫“数据”，容易混用。
2. .deploy 目前只覆盖 chroma、db、logs，未来的 reports、exports、sessions 还没有统一落位。
3. benchmark、会话快照、导出产物尚未被正式分区。

---

## 2. 三个目录的最终职责

### 2.1 data/

只放可以入 git 的演示资产。

允许内容：

- ddl/
- demo_db/
- 少量演示用 seed 数据

禁止内容：

- 私有测试集
- 运行时向量库
- 临时导出文件
- 评测报告

### 2.2 datasets/

只放不可入 git 的私有测试与 benchmark 资产。

建议目标结构：

```text
datasets/
├── README.md
├── source/
├── normalized/
├── manifests/
└── benchmarks/
    ├── read_basic/
    ├── read_complex/
    ├── conversation/
    └── write_action/
```

### 2.3 .deploy/

只放可以清理的运行时与报告产物。

建议目标结构：

```text
.deploy/
├── chroma/
├── db/
├── logs/
├── sessions/
├── exports/
└── reports/
    ├── pytest/
    └── eval/
```

---

## 3. 当前到目标的迁移动作

| 当前路径 | 目标动作 |
|---|---|
| data/ddl/ | 保留 |
| data/demo_db/ | 保留 |
| datasets/README.md | 保留，并在后续补 benchmarks 结构 |
| .deploy/chroma/ | 保留 |
| .deploy/db/ | 保留 |
| .deploy/logs/ | 保留 |
| pytest_output.txt | 移入 .deploy/reports/pytest/ 或停止持久化 |
| 未来评测输出 | 落入 .deploy/reports/eval/ |
| 未来会话快照 | 落入 .deploy/sessions/ |
| 未来导出工件 | 落入 .deploy/exports/ |

---

## 4. 执行规则

1. data 永远不接收私有和运行时产物。
2. datasets 永远不接收生成结果，只接收来源数据、归一化数据和 benchmark 资产。
3. .deploy 永远不接收版本化样例数据，只接收可清理产物。
4. 如果一个文件可以通过重新运行脚本再生成，它就不应该进 data 或 datasets，而应进 .deploy。

---

## 5. 整理顺序

### Batch D1

- 冻结 data、datasets、.deploy 的准入规则
- 文档中明确三者边界

### Batch D2

- 为 .deploy/reports/、.deploy/exports/、.deploy/sessions/ 预留落位
- 停止向根目录写报告产物

### Batch D3

- 为 datasets/ 建立 benchmark 子结构
- 把 read_basic、read_complex、conversation、write_action 评测集落位到 datasets/benchmarks/

---

## 6. 验收标准

当以下条件满足时，该区域整理完成：

1. data 中只剩演示资产。
2. datasets 中只剩私有测试和 benchmark 资产。
3. .deploy 中接管所有可清理的运行时、导出和报告产物。
4. 主文档中不再出现 data、datasets、.deploy 的职责漂移。