# application 层迁移方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 迁移范围

application 层负责用例和编排，不负责底层技术实现。

本文件覆盖：

- orchestration
- conversations
- analytics
- actions
- 由旧 nlu、explain、pipeline、memory 吸收而来的应用逻辑

---

## 2. 当前模块清单

- app/core/orchestrator/pipeline.py
- app/core/nlu/question_classifier.py
- app/core/explain/sql_explainer.py
- app/core/memory/
- 当前 pipeline 中的 summarize_result_natural_language
- 当前 UI 直接调用的数据导入流程

---

## 3. 目标结构

```text
app/application/
├── orchestration/
│   ├── pipeline.py
│   ├── sql_router.py
│   ├── grounding_service.py
│   └── query_workflow.py
├── conversations/
│   ├── session_service.py
│   ├── summary_service.py
│   └── tool_trace_service.py
├── analytics/
│   ├── result_summary_service.py
│   ├── sql_explanation_service.py
│   └── chart_plan_service.py
└── actions/
    ├── data_import_use_case.py
    ├── approval_service.py
    └── rollback_service.py
```

---

## 4. 文件与职责映射

| 当前文件/逻辑 | 目标位置 | 说明 |
|---|---|---|
| app/core/orchestrator/pipeline.py | app/application/orchestration/pipeline.py | 直接迁移为第一落点 |
| pipeline 中的 LLM fallback 路由 | app/application/orchestration/sql_router.py | 从 pipeline 中拆出 |
| pipeline 中的结果摘要逻辑 | app/application/analytics/result_summary_service.py | 不再继续塞在 pipeline |
| app/core/nlu/question_classifier.py | app/application/orchestration/heuristic_classifier.py + app/domain/query/question_classification.py | dataclass 与算法分离 |
| app/core/explain/sql_explainer.py | app/application/analytics/sql_explanation_service.py | 解释属于分析结果表达 |
| app/core/memory/ | app/application/conversations/* | 当前为空壳，迁移时直接补实现 |
| UI 的导入编排 | app/application/actions/data_import_use_case.py | 数据导入属于受控动作用例 |

---

## 5. 关键迁移点

### 5.1 pipeline.py

当前 pipeline.py 既做：

1. LLM 调用入口
2. SQL 生成预览
3. 查询执行确认
4. 图表推荐
5. 自然语言摘要

迁移策略：

- pipeline.py 先原名迁到 application/orchestration/
- 逐步拆出 sql_router、result_summary_service、chart_plan_service
- pipeline 最终只保留工作流编排职责

### 5.2 question_classifier.py

当前是典型过渡期逻辑。

处理方式：

- QuestionClassification dataclass 进入 domain/query/
- 基于关键字的 heuristic classifier 先留在 application/orchestration/
- 后续随着 LLM Router 稳定，heuristic classifier 降级为 fallback 辅助模块

### 5.3 data import

当前文件上传导入流程直接从 UI 调底层导入函数。

迁移后：

- UI 只调用 application/actions/data_import_use_case.py
- 解析、建表、写入等技术动作由 infrastructure/execution/imports/ 承担

---

## 6. 推荐批次

### Batch A1：pipeline 平移

- 先把 pipeline.py 落到 application/orchestration/
- 保持现有函数签名不变

### Batch A2：analytics 拆分

- 拆出 result_summary_service
- 拆出 sql_explanation_service
- 把图表规划入口从 pipeline 中抽到 analytics/

### Batch A3：conversations 落地

- 将 session_id 真正纳入主链路
- 建立 session_service、summary_service、tool_trace_service

### Batch A4：actions 落地

- 建立 data_import_use_case.py
- 为 approval、rollback 预留服务入口

### Batch A5：heuristic nlu 收口

- 把 question_classifier 从核心路由降级为辅助模块

---

## 7. 每批验收

1. presentation 层不再直接拼装业务流程。
2. infrastructure 层不再包含 workflow 决策。
3. pipeline 只负责编排，不再继续累加工具函数。
4. session_id 至少能在 application 层流转，而不是停在 API schema。