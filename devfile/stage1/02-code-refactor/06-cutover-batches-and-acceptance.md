# 统一 cutover 批次与验收方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 总体策略

代码迁移不按“目录名字”做，而按风险和依赖顺序做。

统一规则：

1. 每一批先创建新路径。
2. 再迁实现。
3. 再保留旧路径 wrapper。
4. 全部引用切过去后，再删除旧路径。

---

## 2. 推荐批次

### Batch M0：新路径准备

- 补齐 presentation/application/domain/infrastructure 下缺失目录
- 为 rules、imports、schemas、middleware 预留新落位

### Batch M1：observability + security

- logging
- metrics
- api_key
- permission
- sql_sanitizer
- middleware

### Batch M2：domain 最小对象集

- QuestionClassification
- SQLDraft
- AnalysisArtifact

### Batch M3：LLM + retrieval

- adapters
- health_check
- prompts
- retrieval base/chroma/schema_loader
- client.py 的 infra 部分

### Batch M4：execution + data import infra

- connectors
- db_abstraction
- database
- executor
- guard
- imports/

### Batch M5：application 编排层

- pipeline
- sql_router
- result_summary_service
- sql_explanation_service
- data_import_use_case
- session_service

### Batch M6：presentation 切换

- FastAPI
- routes
- Streamlit UI
- presenters
- validators
- error_handlers
- rate_limiter

### Batch M7：shared/config/rules 收口

- shared/schemas 拆分
- config 拆分
- rules 迁移

### Batch M8：旧目录退役

- 删除或清空 app/api
- 删除或清空 app/ui
- 删除或清空 app/core
- 删除 app/app
- 删除 app/middleware
- 删除 app/rules

---

## 3. 每批必须做的验证

### 3.1 import 验证

- 新路径可导入
- 旧路径 wrapper 仍可导入

### 3.2 测试验证

至少运行受影响测试子集。

建议优先：

- tests/unit/test_settings.py
- tests/unit/test_llm_adapters.py
- tests/unit/test_llm_client.py
- tests/unit/test_fast_fallback_strategy.py
- tests/unit/test_chart_recommender.py
- tests/api/test_api.py

### 3.3 文档验证

- grep 检查主文档是否仍引用旧路径
- README、docs、devfile 口径同步

---

## 4. 兼容壳规则

1. wrapper 只能 re-export，不再追加新逻辑。
2. wrapper 必须标注“只减不增”。
3. 一旦 grep 和测试确认无活动引用，wrapper 在下一批删除。

---

## 5. 最终完成标准

代码迁移阶段完成时，应满足：

1. 新代码全部进入 presentation、application、domain、infrastructure、shared、config。
2. app/core 不再承接真实主逻辑。
3. app/api、app/ui 只剩兼容壳或已删除。
4. app/rules、app/middleware、app/app 已退出主结构。
5. 主链路已能在新层级中完整跑通。

---

## 6. 与仓库物理整理的配合顺序

执行总顺序建议为：

1. 先完成 stage1/01-repository-physical-reorg/ 的根目录、数据区和 devfile 整理。
2. 再按本文件的 M0-M8 逐批迁代码。
3. 等 M8 完成后，再做最终的 legacy cleanup 和目录图更新。