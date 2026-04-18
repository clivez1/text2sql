# 20-03. domain 层迁移方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 迁移目标

domain 层负责把当前散落在 shared、pipeline、nlu 和 chart 中的临时数据结构收束成稳定对象。

目标不是一次性建很多类，而是先把核心中间工件标准化，停止在主链路中传裸 dict。

---

## 2. 目标对象清单

### 2.1 query/

- QuestionClassification
- QueryIntent
- SQLDraft
- ValidationIssue
- RepairHistory

### 2.2 catalog/

- CatalogMatch
- GroundingPackage
- JoinEdge
- SchemaSnapshot
- LocalSemanticAlias

### 2.3 conversation/

- SessionContext
- ConversationEvent
- ToolInvocation
- ClarificationState

### 2.4 governance/

- PolicyDecision
- ApprovalTicket
- AuditEvent
- RollbackToken
- ActionRequest

### 2.5 visualization/

- ChartPlan
- ChartSpec
- AnalysisArtifact
- ExportArtifact

---

## 3. 当前来源与迁移入口

| 当前来源 | 迁移目标 |
|---|---|
| app/shared/schemas.py 中的 AskResult | domain/visualization/analysis_artifact.py |
| app/core/nlu/question_classifier.py 中的 QuestionClassification | domain/query/question_classification.py |
| app/core/chart/schemas.py | domain/visualization/chart_spec.py |
| app/core/sql/local_semantics.py | domain/catalog/local_semantics.py |
| pipeline 中的 preview/result dict | domain/query/sql_draft.py + domain/visualization/analysis_artifact.py |

---

## 4. 迁移规则

1. domain 只放对象、约束和命名，不放数据库、HTTP、LLM SDK 细节。
2. Pydantic API schema 不直接等同于 domain model。
3. domain model 先用 dataclass 或轻量对象落地，再通过 presenter 转成 API 响应。
4. 凡是会在 application 和 infrastructure 之间反复传递的中间结果，都优先变成 domain object。

---

## 5. 推荐批次

### Batch D1：最小对象集

- QuestionClassification
- SQLDraft
- AnalysisArtifact

目标：先消除 pipeline 和 shared 里最明显的裸 dict。

### Batch D2：检索对象集

- CatalogMatch
- GroundingPackage
- JoinEdge
- LocalSemanticAlias

目标：为 retrieval 和 LLM grounding 提供稳定输入输出。

### Batch D3：会话对象集

- SessionContext
- ConversationEvent
- ToolInvocation

目标：为多轮能力开路。

### Batch D4：治理对象集

- PolicyDecision
- ApprovalTicket
- AuditEvent
- RollbackToken

目标：为写操作和审批流开路。

### Batch D5：结果表达对象集

- ChartPlan
- ChartSpec
- ExportArtifact

目标：让分析结果不再只是表格加临时 chart_config。

---

## 6. 验收标准

1. application 与 infrastructure 之间的重要中间工件不再传裸 dict。
2. AskResult 这类内部对象不再和 API 响应模型混在同一文件里。
3. 检索、解释、图表、审批等跨模块能力都有明确 domain object 作为边界。