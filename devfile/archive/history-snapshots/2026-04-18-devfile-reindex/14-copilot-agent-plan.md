# 14. 多轮 Copilot / Agent 方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 目标

把当前单轮问答系统升级为多轮数据分析 Copilot。

这里的重点不是“会聊天”，而是：

- 会识别缺失信息
- 会澄清和追问
- 会分步完成分析
- 会调用受控工具
- 会持续输出结构化中间结果和最终结果

---

## 2. 目标状态机

建议状态机：

1. `received`
2. `clarifying`
3. `planning`
4. `retrieving`
5. `drafting`
6. `verifying`
7. `executing`
8. `summarizing`
9. `visualizing`
10. `awaiting_approval`
11. `completed`
12. `failed`

不是每个请求都会走全状态，但所有状态都要可追踪。

---

## 3. 会话记忆分层

### 3.1 请求级记忆

- 当前问题
- 当前 grounding
- 当前 SQL / action 草稿

### 3.2 会话级记忆

- 历史问题摘要
- 用户偏好
- 已确认的业务上下文
- 最近生成过的图表与导出结果

### 3.3 用户级记忆

- 常用数据库
- 常用指标和维度
- 常用可视化偏好

---

## 4. 工具目录

Copilot 必须通过工具完成关键动作。

建议首批工具：

- `search_catalog`
- `resolve_join_path`
- `draft_sql`
- `validate_sql`
- `run_query`
- `summarize_result`
- `plan_chart`
- `export_artifact`
- `request_approval`
- `execute_write_action`
- `rollback_action`

---

## 5. API 与 UI 要求

### 5.1 API

- 每次请求都显式带 `session_id`
- 返回事件流或阶段结果
- 支持查询会话历史、审批状态和执行工件

### 5.2 UI

- 不只是输入框和结果表格
- 需要展示计划、澄清问题、执行阶段、图表、审批和历史工件

---

## 6. 与当前系统的差距

当前仓库只有 `session_id` 字段，没有真正的会话引擎。

当前必须补齐：

- session store
- conversation event store
- summary builder
- tool orchestration
- clarification loop

---

## 7. 实施顺序

### Step 1：会话对象与事件对象

### Step 2：读路径状态机

### Step 3：clarification loop

### Step 4：工具调用记录

### Step 5：与图表、审批、导出打通

---

## 8. 验收标准

- `session_id` 真正进入主链路
- 系统能针对歧义问题发起澄清
- 多轮追问可以复用上一轮 grounding 和结果
- 工具调用和关键中间结果都有事件记录
