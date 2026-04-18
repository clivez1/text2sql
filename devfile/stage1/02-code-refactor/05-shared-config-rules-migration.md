# shared、config、rules 与横切模块迁移方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 当前问题

当前仓库还有几类横切模块没有稳定归属：

1. app/shared/schemas.py 把 API schema 和内部对象混在一起。
2. app/config/settings.py 正在变成越来越重的单文件配置中心。
3. app/rules/default_rules.yaml 已经不是独立顶层逻辑目录，而是 query 资产。
4. app/core/errors.py、app/core/validators.py、app/middleware/rate_limiter.py 的归属仍未完全统一。

---

## 2. 目标结构

```text
app/
├── shared/
│   ├── schemas/
│   ├── types/
│   └── utils/
├── config/
│   ├── settings.py
│   ├── llm.py
│   ├── database.py
│   ├── runtime.py
│   └── feature_flags.py
└── domain/query/
    └── rule_assets/
        └── default_rules.yaml
```

---

## 3. 文件映射

| 当前文件 | 目标位置 | 说明 |
|---|---|---|
| app/shared/schemas.py | app/presentation/api/schemas.py + domain/* + shared/types/* | 需要拆分 |
| app/config/settings.py | app/config/settings.py + app/config/llm.py + database.py + runtime.py + feature_flags.py | settings.py 保留为 facade |
| app/rules/default_rules.yaml | app/domain/query/rule_assets/default_rules.yaml | 规则资产进入 query 域 |
| app/rules/__init__.py | app/application/orchestration/rule_store.py | 规则装载逻辑进入 application |
| app/core/errors.py | app/presentation/api/error_handlers.py | FastAPI 绑定逻辑归 presentation |
| app/core/validators.py | app/presentation/api/validators.py | 输入校验归 presentation |
| app/middleware/rate_limiter.py | app/presentation/api/middleware/rate_limiter.py | HTTP 限流归 presentation |

---

## 4. 关键拆分要求

### 4.1 app/shared/schemas.py

拆分原则：

1. AskRequest、AskResponse、HealthResponse、SchemaResponse 留在 presentation/api/schemas.py。
2. AskResult 不再留在 API schema 文件中，而迁到 domain/visualization/ 或 domain/query/。
3. 通用 type 和 helper 才保留在 shared/。

### 4.2 app/config/settings.py

第一阶段保留 settings.py 作为统一入口，避免大面积改 import。

第二阶段逐步拆为：

- llm.py
- database.py
- runtime.py
- feature_flags.py

settings.py 只做 facade 和聚合。

### 4.3 app/rules/

规则 YAML 的新定位是资产，而不是顶层执行目录。

迁移后：

- 资产文件进入 domain/query/rule_assets/
- 装载与匹配逻辑进入 application/orchestration/rule_store.py

---

## 5. 推荐批次

### Batch S1：错误处理、验证器、限流归口

- 先把 core/errors.py、core/validators.py、middleware/rate_limiter.py 迁到 presentation/

### Batch S2：shared/schemas 拆分

- API schema 与内部对象分离
- presenter 开始接管转换逻辑

### Batch S3：rules 迁移

- 迁移 default_rules.yaml
- 建立 rule_store

### Batch S4：config 拆分

- 在不改外部入口的前提下，把 settings.py 拆成多配置子文件

---

## 6. 验收标准

1. 不再有“API schema + 内部对象 + helper”共存于同一文件的情况。
2. settings.py 不再继续无限膨胀。
3. rules 被明确收束为 query 资产区，而不是顶层孤立目录。
4. 错误处理、验证器、限流都落入 presentation 层的明确位置。