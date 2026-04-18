# 代码重构启动包

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 本文件负责什么

本文件不再解释为什么要重构，而是直接回答：

1. 现在是否已经可以开始代码重构。
2. 第一轮应该先改哪几批文件。
3. 每一批改完后如何验证。
4. 什么时候算正式进入重构阶段。

如果你现在准备开始改代码，先读本文件，再进入 01-06 的分层细则。

---

## 2. 当前已满足的启动条件

截至 2026-04-18，以下条件已经满足：

1. devfile 已完成根级收束，主控、执行、专题三层入口已分离。
2. app 下的 presentation、application、domain、infrastructure、shared、config 骨架已经存在。
3. stage1/01-repository-physical-reorg/ 已冻结目标目录落位。
4. stage1/02-code-refactor/ 已冻结按层迁移和 cutover 规则。
5. references/themes/ 已冻结 LLM、Copilot、评测三类专题约束。

当前结论：

可以正式从“架构讨论阶段”进入“代码迁移阶段”。

---

## 3. 进入重构前的事实基线

### 3.1 已存在的新目录

当前 app 下已经有：

- application/
- infrastructure/
- domain/
- presentation/
- shared/
- config/

因此 M0 不再是从零搭骨架，而是补齐缺失子目录和首批落点文件。

### 3.2 仍承载主逻辑的旧目录

当前仍需迁移的旧主路径主要包括：

- app/core/
- app/api/
- app/ui/
- app/middleware/
- app/rules/
- app/app/

其中最先应动的是 app/core/ 下依赖最浅的模块，而不是入口层。

---

## 4. 直接开工顺序

### Step R0：完成最小重构准备

目标：确认新路径可承接首批文件。

执行项：

1. 检查 infrastructure/observability、infrastructure/security、infrastructure/llm、infrastructure/retrieval、infrastructure/execution 是否具备首批文件落位。
2. 检查 application/orchestration、application/analytics、application/actions、application/conversations 是否具备首批文件落位。
3. 为 execution/imports、presentation/api/middleware、presentation/api/schemas 预留新路径。

验收：

1. 所有首批目标目录存在。
2. 新目录可被 Python import。

### Step R1：执行第一批低风险迁移

目标：先迁依赖最浅、收益最高的一批模块，建立“新路径 + 旧 wrapper”模式。

首批文件：

- app/core/logging.py -> app/infrastructure/observability/logging.py
- app/core/metrics.py -> app/infrastructure/observability/metrics.py
- app/core/auth/api_key.py -> app/infrastructure/security/api_key.py
- app/core/auth/middleware.py -> app/infrastructure/security/middleware.py
- app/core/auth/permission.py -> app/infrastructure/security/permission.py
- app/core/security/sql_sanitizer.py -> app/infrastructure/security/sql_sanitizer.py

配套动作：

1. 旧路径改成 re-export wrapper。
2. 新增引用一律优先切到 infrastructure/ 新路径。

验收：

1. 新旧路径都能导入。
2. 受影响测试最小子集通过。

### Step R2：建立最小 domain 对象边界

目标：先把最关键的中间对象从裸 dict 中抽出来，避免后续 application 拆分继续扩散临时结构。

首批对象：

- QuestionClassification
- SQLDraft
- AnalysisArtifact

优先来源：

- app/core/nlu/question_classifier.py
- app/shared/schemas.py
- pipeline 中的 preview/result 中间对象

验收：

1. application 和 infrastructure 之间至少有一批主链路对象不再传裸 dict。
2. 内部对象不再和 API schema 混放在同一文件。

### Step R3：迁移 LLM transport 和 retrieval

目标：为真正的 LLM 优先主链路让路。

优先文件：

- app/core/llm/adapters.py
- app/core/llm/health_check.py
- app/core/llm/prompts.py
- app/core/retrieval/base.py
- app/core/retrieval/chroma_retriever.py
- app/core/retrieval/schema_loader.py

特殊处理：

- app/core/llm/client.py 不整体平移，先拆 transport 部分到 infrastructure/llm/client.py。

验收：

1. provider transport 逻辑进入 infrastructure。
2. routing 决策没有被一起带进 infrastructure。

### Step R4：再进入 application 主链路迁移

在 R1-R3 稳定后，再进入：

- pipeline 平移
- sql_router 拆分
- result_summary_service、sql_explanation_service 拆分
- data_import_use_case 落地

这一阶段开始，才算真正切主链路。

---

## 5. 第一轮不应先做的事

1. 不先改 FastAPI 和 Streamlit 入口。
2. 不先拆 shared/config 大文件。
3. 不先删除 app/core、app/api、app/ui 旧目录。
4. 不在 application 和 domain 还未稳定时急着做大规模 import 全切换。

---

## 6. 直接执行时的文档顺序

如果现在开始重构，建议按以下顺序开文档：

1. stage1/01-repository-physical-reorg/02-app-physical-structure.md
2. stage1/02-code-refactor/07-refactor-kickoff.md
3. stage1/02-code-refactor/01-infrastructure-migration.md
4. stage1/02-code-refactor/03-domain-migration.md
5. stage1/02-code-refactor/02-application-migration.md
6. stage1/02-code-refactor/06-cutover-batches-and-acceptance.md
7. references/themes/01-llm-and-retrieval.md

---

## 7. 第一轮建议测试集

进入代码重构后，建议最先反复使用的验证集是：

- tests/unit/test_settings.py
- tests/unit/test_llm_adapters.py
- tests/unit/test_llm_client.py
- tests/unit/test_fast_fallback_strategy.py
- tests/unit/test_errors.py
- tests/unit/test_api_key.py

这些测试覆盖首批最容易受影响的配置、provider、安全和兼容逻辑。

---

## 8. 进入代码重构阶段的完成定义

当以下条件满足时，可以认为已经正式进入代码重构阶段：

1. 首批新路径已有真实实现文件，而不是空目录。
2. 至少一组旧 core 模块已经变成 wrapper。
3. 至少一组测试在新旧兼容状态下通过。
4. 新增代码不再继续写回 app/core。

达到以上四条之后，后续工作就不再是“准备重构”，而是“执行重构”。