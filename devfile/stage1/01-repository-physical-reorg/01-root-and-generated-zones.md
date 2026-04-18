# 根目录与生成区整理方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 当前问题

当前仓库根目录同时混放了四类东西：

1. 稳定入口文件：README、AGENTS、Dockerfile、compose、依赖定义。
2. 主业务目录：app、data、datasets、scripts、tests、docs、devfile。
3. 本地生成目录：.venv、.pytest_cache、.ruff_cache、.sisyphus。
4. 一次性输出文件：pytest_output.txt、临时报告、手工导出物。

问题不在于根目录项多，而在于这些东西没有被明确分级。

---

## 2. 根目录目标原则

根目录只允许保留三类对象：

### 2.1 仓库稳定入口

- README.md
- AGENTS.md
- Dockerfile
- docker-compose.yml
- pyproject.toml
- requirements.txt
- .env.example
- .impKey.example
- .gitignore
- .dockerignore

### 2.2 仓库一级功能区

- app/
- data/
- datasets/
- .deploy/
- scripts/
- tests/
- docs/
- devfile/
- .github/

### 2.3 本地隐藏但可接受的技术区

- .git/
- .venv/
- .pytest_cache/
- .ruff_cache/
- .sisyphus/

这些目录可以存在，但不能被当作架构区写入主文档，也不能成为流程依赖。

---

## 3. 不应继续留在根目录的对象

### 3.1 一次性输出文件

像 pytest_output.txt 这类文件不应继续平铺在根目录。

目标去向：

- pytest 文本输出：.deploy/reports/pytest/
- 评测输出：.deploy/reports/eval/
- 临时导出：.deploy/exports/

### 3.2 临时脚本与人工记录

不允许在根目录新增：

- ad-hoc 调试脚本
- 手工验证结果
- 临时 Markdown 笔记
- 导出文件

这些内容要么进入 scripts/，要么进入 devfile/，要么进入 .deploy/。

---

## 4. 根目录目标形态

```text
text2sql-0412/
├── app/
├── data/
├── datasets/
├── .deploy/
├── scripts/
├── tests/
├── docs/
├── devfile/
├── .github/
├── README.md
├── AGENTS.md
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .impKey.example
├── .gitignore
└── .dockerignore
```

本地生成目录可以存在，但不进入“稳定仓库结构图”。

---

## 5. 执行规则

1. 新增文件前先判断它是否属于稳定入口、一级功能区或本地生成区。
2. 根目录不再接收任何报告产物和临时文本。
3. 所有新生成报告统一落到 .deploy/reports/。
4. 所有新导出内容统一落到 .deploy/exports/。
5. 所有本地密钥文件继续留在根目录，但只能保留 .example 版本入 git。

---

## 6. 首批整理动作

### Batch R1

- 停止向根目录写入 pytest_output.txt 一类文件
- 为 .deploy/reports/ 预留未来落位
- 在文档中把 .venv、缓存目录标记为本地生成区

### Batch R2

- 清理根目录一次性输出文件
- 审计是否有新文件越界落到根目录

---

## 7. 验收标准

达到以下条件时，根目录整理完成：

1. 根目录只剩稳定入口、一级功能区和本地生成区。
2. 不再有测试输出、评测输出和导出文件平铺在根目录。
3. 主文档不再把 .venv、.pytest_cache、.ruff_cache、.sisyphus 当成正式架构组成部分。