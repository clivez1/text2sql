# 10-02. app 目录物理整理方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 当前问题

app/ 当前处于“三套结构并存”状态：

1. 旧入口层：app/api、app/ui。
2. 旧核心层：app/core。
3. 新分层骨架：app/presentation、app/application、app/domain、app/infrastructure。

同时还有三个特殊区：

- app/middleware/
- app/rules/
- app/app/

如果不先冻结这些目录的未来落位，接下来的代码迁移会反复横跳。

---

## 2. app 目标结构

```text
app/
├── presentation/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── middleware/
│   │   └── presenters/
│   └── ui/
│       ├── streamlit_app.py
│       ├── chart_renderer.py
│       └── exporter.py
├── application/
│   ├── orchestration/
│   ├── conversations/
│   ├── analytics/
│   └── actions/
├── domain/
│   ├── query/
│   ├── catalog/
│   ├── conversation/
│   ├── governance/
│   └── visualization/
├── infrastructure/
│   ├── llm/
│   ├── retrieval/
│   ├── execution/
│   ├── persistence/
│   ├── security/
│   └── observability/
├── shared/
│   ├── schemas/
│   ├── types/
│   └── utils/
├── config/
├── core/                      # 过渡区，只减不增
└── README.md
```

---

## 3. 当前目录到目标目录映射

| 当前路径 | 目标路径 | 规则 |
|---|---|---|
| app/api/ | app/presentation/api/ | 入口层直接迁入 presentation |
| app/ui/ | app/presentation/ui/ | UI 入口与渲染工具一起迁入 presentation |
| app/core/ | 分拆到 application、domain、infrastructure | 禁止整体平移，必须拆职责 |
| app/middleware/ | app/presentation/api/middleware/ | HTTP 中间件进入 API 表达层 |
| app/rules/ | app/domain/query/rule_assets/ | YAML 规则变成 query 资产区 |
| app/shared/ | app/shared/schemas/、types/、utils/ | 继续保留 shared，但按内容细分 |
| app/config/ | app/config/ | 保留，但从单 settings.py 向多配置文件演进 |
| app/app/ | 删除 | 历史嵌套壳目录，不保留 |

---

## 4. 特殊目录决策

### 4.1 app/core/

短期保留，长期清空。

约束：

1. 新功能不再进入 app/core。
2. 旧模块迁出后，只保留兼容壳或被删除。
3. 最终 cutover 完成后，app/core 只允许留下空壳兼容层，随后移除。

### 4.2 app/middleware/

当前只有 rate_limiter 这类 HTTP 中间件，应归到 presentation/api/middleware/。

### 4.3 app/rules/

当前 default_rules.yaml 是 fallback 与规则资产，不再视为顶层技术目录。

目标：

- 资产文件进入 app/domain/query/rule_assets/
- 规则装载与匹配逻辑进入 application/orchestration/

### 4.4 app/app/

当前只剩空壳 __init__.py，不应继续存在。

处理策略：

1. 先做 import 审计。
2. 若无外部依赖，直接删除。
3. 若有历史引用，先加兼容 wrapper，再删除。

---

## 5. app 物理整理顺序

### Batch A1：冻结入口与资产落位

- 冻结 presentation、application、domain、infrastructure 为唯一新代码入口
- 冻结 middleware、rules 的新目标位置

### Batch A2：迁移叶子目录

- presentation/ui
- presentation/api/middleware
- infrastructure/observability
- infrastructure/security

### Batch A3：迁移核心技术目录

- infrastructure/llm
- infrastructure/retrieval
- infrastructure/execution

### Batch A4：迁移编排与领域目录

- application/orchestration
- application/analytics
- application/conversations
- domain/*

### Batch A5：清退旧目录

- 清空 app/api、app/ui、app/core、app/app
- 只保留必要兼容壳

---

## 6. 验收标准

当以下条件同时满足时，app 物理整理完成：

1. 新代码全部进入 presentation、application、domain、infrastructure、shared、config。
2. app/api、app/ui、app/core 不再接收新增代码。
3. app/rules 和 app/middleware 已有明确新落点。
4. app/app 已被删除或仅剩短期兼容壳，并有退出时间点。