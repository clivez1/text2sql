# 30-03. 评测、发布与回归方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 目标

如果没有评测和发布约束，整个方案会再次退化成“演示可跑、线上不可控”。

本文件负责冻结：

- 如何评测
- 如何验收
- 如何灰度
- 如何比较云模型和本地模型

---

## 2. 评测维度

### 2.1 Read-only

- intent 正确率
- grounding 命中率
- SQL 语法正确率
- 执行成功率
- 答案可用率
- latency
- cost

### 2.2 Conversation

- 澄清成功率
- 会话恢复成功率
- 多轮任务完成率
- 工具调用成功率

### 2.3 Visualization

- 图表采纳率
- 图表规划可复现率
- 大结果集展示稳定性

### 2.4 Governed Write

- dry-run 准确率
- 审批链完整率
- 审计完整率
- 回滚成功率
- 越权拦截率

---

## 3. 数据集分层

建议建立四类数据集：

1. read_basic
2. read_complex
3. conversation
4. write_action

每类都区分：

- 演示库样本
- 中型库样本
- 大型库样本

---

## 4. 环境分层

### 4.1 本地开发环境

- 快速回归
- 小规模评测

### 4.2 集成环境

- 中型库 benchmark
- fallback 和预算验证

### 4.3 预发布环境

- 全量质量门禁
- 审批与回滚演练

---

## 5. 发布门禁

每个版本至少满足：

1. 关键评测集达标
2. 安全回归通过
3. 成本预算在范围内
4. 关键路径 observability 就绪
5. 文档和配置同步更新

---

## 6. 观测要求

必须覆盖以下链路指标：

- provider latency
- retrieval latency
- grounding quality
- validation 或 repair 次数
- query runtime
- chart planning latency
- approval latency
- rollback latency

---

## 7. 版本验收建议

### V1

- 只读主链路达标
- 中大型库检索基础达标

### V1.5

- 多轮会话与图表规划达标

### V2

- 受治理写操作达标

### V2.5

- 本地模型优先和发布治理达标

---

## 8. 第一阶段必须补齐的东西

- 统一 eval case 结构
- 基线报告模板
- 版本前后对比模板
- 云模型和本地模型对比模板

---

## 9. 关联文档

- 30-capability-topics/01-llm-and-retrieval.md：只读链路和 grounding 主链路
- 30-capability-topics/02-copilot-visualization-and-actions.md：多轮、图表和写操作评测对象
- 03-execution-roadmap.md：阶段安排和门禁落点