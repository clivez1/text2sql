# 10-04. scripts、tests、docs、devfile 整理方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. scripts/

### 当前问题

scripts/ 当前文件数不多，但已经混合了启动、验证、评测和容器入口脚本。

### 目标结构

```text
scripts/
├── bootstrap/
├── verify/
├── evaluate/
├── ops/
│   └── container/
└── migrations/
```

### 当前映射

| 当前文件 | 目标位置 |
|---|---|
| init_demo_db.py | scripts/bootstrap/init_demo_db.py |
| ingest_schema.py | scripts/bootstrap/ingest_schema.py |
| verify_llm.py | scripts/verify/verify_llm.py |
| verify_week1.sh | scripts/verify/verify_week1.sh |
| verify_week2.py | scripts/verify/verify_week2.py |
| evaluate_week2.py | scripts/evaluate/evaluate_week2.py |
| entrypoint-combined.sh | scripts/ops/container/entrypoint-combined.sh |

### 规则

1. scripts 只承接工具，不承接产品主逻辑。
2. 新脚本必须先归类到 bootstrap、verify、evaluate、ops、migrations。

---

## 2. tests/

### 当前问题

tests/ 已有 unit、integration、api、fixtures，但未来 conversation、write_action、eval 还没有正式区位。

### 目标结构

```text
tests/
├── unit/
├── integration/
├── api/
├── eval/
├── scenarios/
│   ├── conversation/
│   └── write_action/
└── fixtures/
```

### 规则

1. 单元测试继续放 unit/。
2. 多模块联动放 integration/。
3. API 契约放 api/。
4. 评测驱动样例放 eval/。
5. 多轮和治理动作场景放 scenarios/。

---

## 3. docs/

### 当前问题

docs/ 现在文件少，平铺还能接受，但未来会扩成更完整的使用和运行文档。

### 目标结构

短期保持平铺，避免过早打断现有链接。

中期目标：

```text
docs/
├── getting-started/
├── reference/
├── operations/
└── architecture/
```

建议映射：

| 当前文件 | 中期目标位置 |
|---|---|
| QUICKSTART.md | docs/getting-started/quickstart.md |
| api.md | docs/reference/api.md |
| CONFIGURATION.md | docs/operations/configuration.md |
| deployment.md | docs/operations/deployment.md |
| architecture.md | docs/architecture/current-runtime.md |

### 规则

1. docs 只写当前可运行系统。
2. 未来方案与迁移计划一律不进 docs。
3. docs 的物理重排应在 presentation cutover 之后做，避免短期内反复改链接。

---

## 4. devfile/

### 当前目标结构

```text
devfile/
├── 00-08 根级主文档
├── 10-repository-physical-reorg/
├── 20-code-migration/
└── archive/
```

### 规则

1. 根级只保留总纲、现状、目标、路线、专题、历史、参考。
2. 逐目录执行方案放 10- 子目录。
3. 逐层代码迁移方案放 20- 子目录。
4. 历史轮次与快照只放 archive/。

---

## 5. 整理顺序

1. 先整理 devfile 结构。
2. 再整理 scripts 分类。
3. 再为 tests 补 eval 与 scenarios 区位。
4. docs 最后重排，避免和代码迁移同时大面积改链接。

---

## 6. 验收标准

1. scripts 新脚本都有明确类别。
2. tests 能容纳单元、集成、API、评测、多轮和写操作场景。
3. docs 与 devfile 的职责边界不再重叠。
4. devfile 已能直接承接“按目录整理”和“按层迁代码”的执行路线。