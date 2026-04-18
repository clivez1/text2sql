# infrastructure 层迁移方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 迁移范围

本文件覆盖所有技术实现型模块：

- LLM
- retrieval
- execution
- security
- observability
- data import 的底层技术组件

目标原则：

1. 技术细节进入 infrastructure。
2. 路由决策和业务流程不留在 infrastructure。
3. 旧模块能先原名迁移就先原名迁移，减少第一轮 diff 风险。

---

## 2. 当前模块清单

### 2.1 LLM

- app/core/llm/adapters.py
- app/core/llm/client.py
- app/core/llm/health_check.py
- app/core/llm/prompts.py

### 2.2 Retrieval

- app/core/retrieval/base.py
- app/core/retrieval/chroma_retriever.py
- app/core/retrieval/schema_loader.py

### 2.3 Execution

- app/core/sql/connectors/
- app/core/sql/database.py
- app/core/sql/db_abstraction.py
- app/core/sql/executor.py
- app/core/sql/guard.py
- app/core/data_import/file_parser.py
- app/core/data_import/table_creator.py
- app/core/data_import/sanitizer.py

### 2.4 Security

- app/core/auth/api_key.py
- app/core/auth/middleware.py
- app/core/auth/permission.py
- app/core/security/sql_sanitizer.py

### 2.5 Observability

- app/core/logging.py
- app/core/metrics.py

---

## 3. 目标结构

```text
app/infrastructure/
├── llm/
│   ├── adapters.py
│   ├── client.py
│   ├── health_check.py
│   └── prompts.py
├── retrieval/
│   ├── base.py
│   ├── chroma_retriever.py
│   └── schema_loader.py
├── execution/
│   ├── connectors/
│   ├── database.py
│   ├── db_abstraction.py
│   ├── executor.py
│   ├── guard.py
│   └── imports/
│       ├── file_parser.py
│       ├── table_creator.py
│       └── sanitizer.py
├── security/
│   ├── api_key.py
│   ├── middleware.py
│   ├── permission.py
│   └── sql_sanitizer.py
└── observability/
    ├── logging.py
    └── metrics.py
```

---

## 4. 文件映射

| 当前文件 | 第一落点 | 最终说明 |
|---|---|---|
| app/core/llm/adapters.py | app/infrastructure/llm/adapters.py | 直接迁移 |
| app/core/llm/health_check.py | app/infrastructure/llm/health_check.py | 直接迁移 |
| app/core/llm/prompts.py | app/infrastructure/llm/prompts.py | 先直接迁移，后续再拆 Prompt Registry |
| app/core/llm/client.py | app/infrastructure/llm/client.py + app/application/orchestration/sql_router.py | 该文件需要拆分 |
| app/core/retrieval/base.py | app/infrastructure/retrieval/base.py | 直接迁移 |
| app/core/retrieval/chroma_retriever.py | app/infrastructure/retrieval/chroma_retriever.py | 直接迁移 |
| app/core/retrieval/schema_loader.py | app/infrastructure/retrieval/schema_loader.py | 先平移，后续再抽 grounding service |
| app/core/sql/connectors/* | app/infrastructure/execution/connectors/* | 直接迁移 |
| app/core/sql/database.py | app/infrastructure/execution/database.py | 迁后标记为待退役 |
| app/core/sql/db_abstraction.py | app/infrastructure/execution/db_abstraction.py | 作为主抽象保留 |
| app/core/sql/executor.py | app/infrastructure/execution/executor.py | 直接迁移 |
| app/core/sql/guard.py | app/infrastructure/execution/guard.py | 第一阶段保留 guard 名称，后续演进为 policy_gate |
| app/core/data_import/file_parser.py | app/infrastructure/execution/imports/file_parser.py | 技术解析组件 |
| app/core/data_import/table_creator.py | app/infrastructure/execution/imports/table_creator.py | 技术执行组件 |
| app/core/data_import/sanitizer.py | app/infrastructure/execution/imports/sanitizer.py | 技术清洗组件 |
| app/core/auth/api_key.py | app/infrastructure/security/api_key.py | 直接迁移 |
| app/core/auth/middleware.py | app/infrastructure/security/middleware.py | 直接迁移 |
| app/core/auth/permission.py | app/infrastructure/security/permission.py | 直接迁移 |
| app/core/security/sql_sanitizer.py | app/infrastructure/security/sql_sanitizer.py | 直接迁移 |
| app/core/logging.py | app/infrastructure/observability/logging.py | 直接迁移 |
| app/core/metrics.py | app/infrastructure/observability/metrics.py | 直接迁移 |

---

## 5. 拆分要求

### 5.1 app/core/llm/client.py

该文件不能直接整体平移，因为它同时承担：

1. adapter 获取
2. fallback 级联
3. 规则优先路由
4. SQL 生成编排

迁移策略：

- adapter 获取与底层客户端访问逻辑进入 app/infrastructure/llm/client.py
- fallback、intent routing、rule fallback 进入 app/application/orchestration/sql_router.py

### 5.2 app/core/sql/guard.py

第一轮先平移为 guard.py，确保行为不变。

第二轮再从 guard 升级为 policy gate，吸收：

- 预算控制
- 审批状态
- 动作级约束
- AST 风险评分

---

## 6. 推荐批次

### Batch I1：observability + security

- logging.py
- metrics.py
- api_key.py
- middleware.py
- permission.py
- sql_sanitizer.py

理由：依赖浅，最容易先迁。

### Batch I2：LLM transport

- adapters.py
- health_check.py
- prompts.py
- client.py 的 transport 相关部分

### Batch I3：retrieval

- base.py
- chroma_retriever.py
- schema_loader.py

### Batch I4：execution

- connectors/
- db_abstraction.py
- database.py
- executor.py
- guard.py
- imports/

### Batch I5：兼容壳清理

- 旧 app/core 下对应模块改为 re-export wrapper
- 所有新引用切到 infrastructure/ 后，再删除 wrapper

---

## 7. 每批验收

1. 迁移后的新模块可以独立导入。
2. 对应旧路径 wrapper 仍能兼容现有调用。
3. 对应测试至少跑一轮受影响子集。
4. 不允许新的 application 流程逻辑继续写回 infrastructure。