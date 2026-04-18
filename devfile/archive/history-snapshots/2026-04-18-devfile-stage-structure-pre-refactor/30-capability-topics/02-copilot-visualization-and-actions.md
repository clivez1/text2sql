# 30-02. Copilot、可视化与受治理动作方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 为什么把这三件事放在一起

多轮 Copilot、结果表达层和受治理写操作，本质上依赖同一套底座：

- session state
- tool orchestration
- policy gate
- artifact model
- audit trail

如果把它们完全拆开讨论，设计上会重复；把它们放在一份文档里，更容易冻结公共底座。

---

## 2. 多轮 Copilot 目标

目标不是“会聊天”，而是：

- 会识别缺失信息
- 会澄清和追问
- 会分步完成分析
- 会调用受控工具
- 会持续输出结构化中间结果和最终结果

### 2.1 目标状态机

建议状态：

1. received
2. clarifying
3. planning
4. retrieving
5. drafting
6. verifying
7. executing
8. summarizing
9. visualizing
10. awaiting_approval
11. completed
12. failed

不是每个请求都走全状态，但所有状态都必须可追踪。

### 2.2 会话记忆分层

- 请求级：当前问题、当前 grounding、当前 SQL 或 action 草稿
- 会话级：历史问题摘要、已确认上下文、最近图表和导出结果
- 用户级：常用数据库、常用指标、可视化偏好

---

## 3. 工具目录

Copilot 必须通过工具完成关键动作。

建议首批工具：

- search_catalog
- resolve_join_path
- draft_sql
- validate_sql
- run_query
- summarize_result
- plan_chart
- export_artifact
- request_approval
- execute_write_action
- rollback_action

---

## 4. 结果表达层

当前系统只有自动图表推荐，还不是完整的分析表达层。

目标是让每个分析请求输出统一 artifact，而不只是表格和附带图表建议。

### 4.1 统一 artifact 建议字段

- answer_summary
- result_table
- chart_plan
- chart_spec
- display_warnings
- export_payload
- source_sql

### 4.2 结果表达能力

- 图表规划
- 采样和聚合
- top-k 压缩
- 钻取和视图切换
- 保存当前分析视图
- 导出分析工件

### 4.3 图表策略

- 默认层：保留当前启发式图表推荐
- 规划层：由 LLM 加规则生成更稳定的 chart spec

---

## 5. 受治理动作系统

最终目标包含写操作，但实现方式必须是：

- 受治理
- 受审批
- 可追踪
- 可回滚

而不是自然语言直接生成任意写 SQL。

### 5.1 非可协商约束

1. 默认禁止所有写操作。
2. 所有写操作必须映射到受支持的 action type。
3. 所有高风险动作必须先 dry-run，再审批，再执行。
4. 所有执行必须生成审计日志和快照。
5. 所有执行必须具备幂等和回滚能力。

### 5.2 Action Catalog

建议首批动作：

- insert_record
- update_record
- bulk_update_by_filter
- soft_delete_record
- restore_record
- import_records
- recompute_field

默认禁止：

- DDL
- 无条件全表更新
- 无条件全表删除
- 跨租户写入
- 无审批批量操作

### 5.3 写路径生命周期

1. 用户提出动作请求
2. 系统识别 action type
3. 系统提取并校验参数
4. 系统做 policy pre-check
5. 系统生成 dry-run
6. 系统生成影响预估与风险级别
7. 进入审批
8. 执行事务
9. 写入审计与快照
10. 返回结果与 rollback token

---

## 6. API 和 UI 要求

### 6.1 API

- 每次请求显式带 session_id
- 返回事件流或阶段结果
- 支持查询会话历史、审批状态和工件

### 6.2 UI

- 不再只是输入框和结果表格
- 需要展示计划、澄清问题、执行阶段、图表、审批和历史工件

---

## 7. 目标落点

- 会话对象和事件对象：app/domain/conversation/
- Copilot 编排：app/application/conversations/ 和 app/application/orchestration/
- analysis artifact 和 chart spec：app/domain/visualization/
- 导出和结果表达用例：app/application/analytics/
- policy、audit、rollback：app/domain/governance/ 和 app/infrastructure/execution/
- 审批和动作执行：app/application/actions/

---

## 8. 实施顺序

### Step 1

- 定义 SessionContext、ConversationEvent、ToolInvocation、AnalysisArtifact、PolicyDecision、AuditEvent、RollbackToken

### Step 2

- 建立读路径状态机和会话存储
- 让 session_id 真正进入主链路

### Step 3

- 建立 chart plan 和 chart spec
- 把导出与 artifact 打通

### Step 4

- 建立 action catalog 和审批流
- 建立 dry-run、审计和回滚骨架

---

## 9. 验收标准

- 系统能针对歧义问题发起澄清
- 多轮追问能复用上一轮 grounding 和结果
- 图表规划结果可复现，可用于 UI 渲染和导出
- 没有 action catalog 的请求一律不能执行
- 所有真实写操作都必须有审批、审计和回滚令牌