# 10-05. 工程交付区与历史残留区整理方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. .github/

### 当前状态

.github/ 当前只有 workflows/，这本身没有问题，说明仓库还处在轻量单仓阶段。

### 目标结构

```text
.github/
├── workflows/
├── actions/          # 后续如有复用 action 再增加
└── scripts/          # 仅当 CI 脚本复杂到需要抽离时再增加
```

### 规则

1. CI 工作流继续保留在 .github/workflows/。
2. 不为了“整齐”提前新建 actions/ 和 scripts/。
3. 只有当测试、评测、发布工作流明显复杂化时，才往下扩层。

---

## 2. 根级工程文件

以下文件继续留在根目录：

- Dockerfile
- docker-compose.yml
- pyproject.toml
- requirements.txt
- .env.example
- .impKey.example

处理原则：

1. 它们是仓库入口文件，不应被塞进 docs 或 scripts。
2. 如果未来依赖拆分明显，再考虑 requirements/ 子目录。
3. 当前阶段优先减少路径扰动，不做无收益搬迁。

---

## 3. evolution/

### 当前问题

evolution/ 是早期演进工作区，但实际已经脱离主线：

1. README 里列出的 TECH_EVOLUTION_PLAN、GAP_ANALYSIS、IMPLEMENTATION_LOG 已不存在。
2. templates/ 中的模板没有形成持续引用链。
3. 主线规划已经转移到 devfile/。

### 目标决策

evolution/ 不再作为活跃一级功能区。

处理路径：

1. 审计 templates/ 中是否还有未吸收的可复用模式。
2. 如仍有价值，迁入 app/shared/ 或 docs/ 的参考区。
3. 如已无主线价值，快照后归档并删除 evolution/。

---

## 4. 历史残留目录与文件

### 4.1 app/app/

判定为历史嵌套壳目录，目标是删除。

### 4.2 pytest_output.txt

判定为一次性测试输出，目标是迁出根目录或停止持久化。

### 4.3 __pycache__

判定为生成物，不进入结构文档和规划主线。

---

## 5. 清退顺序

1. 先冻结 .github 和根级工程文件不动。
2. 再审计 evolution/ 是否还有需要提取的模板。
3. 再删除 app/app/ 和一次性根级输出文件。
4. 最后更新所有主文档中的目录图。

---

## 6. 验收标准

1. .github 仍保持轻量，但扩展策略明确。
2. 根级工程文件不再被误判为“应该搬走的杂项”。
3. evolution/ 已被明确归档、吸收或删除，不再作为模糊功能区存在。
4. app/app/、pytest_output.txt 这类历史残留已退出主结构。