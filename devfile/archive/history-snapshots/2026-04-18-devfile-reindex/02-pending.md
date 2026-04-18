# Text2SQL 当前待办

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 当前冲刺范围

当前冲刺对应 Phase 1 前半段：

- 冻结最终目标架构和领域对象
- 把当前 Demo 主链路切到可演进的 LLM 优先骨架
- 为大库检索、多轮 Agent、写操作治理预留正式接口

---

## 2. P0 待办

### 2.1 架构与领域对象冻结

- 定义 session、conversation event、tool call、catalog item、policy decision、audit event、write action 的统一数据模型
- 定义目标目录重构方案，明确哪些模块在现有目录下演进，哪些需要新增子域
- 定义读路径与写路径的统一执行状态机

### 2.2 Provider 协议层重构

- 将当前单一的 OpenAI SDK 适配改为协议级适配
- 显式支持 OpenAI 兼容接口、Anthropic 协议接口、本地模型网关接口
- 支持按任务类型配置主模型、fallback 模型、超时和预算

### 2.3 LLM 优先 Router 骨架

- 替换当前“先 needs_llm 再 fast fallback”的主路由
- 建立 intent planning、schema grounding、sql drafting、validation、repair 的显式步骤
- 将 YAML 规则、模板 SQL、别名映射降级为辅助资产

### 2.4 大库检索基础骨架

- 设计 metadata catalog 存储结构
- 设计 schema snapshot、join graph、列统计、样本值摘要的采集流程
- 设计混合检索接口，允许 BM25、向量检索、rerank 和 join path 选择接入

### 2.5 评测框架起步

- 拆分 read-only、conversation、chart、write-action 四类评测集
- 为当前基线建立质量、成本、延迟报告模板
- 给主要阶段加入可量化的退出标准

---

## 3. P1 待办

### 3.1 多轮 Copilot 基础设施

- 建立会话存储与摘要存储
- 引入澄清问题和工具调用记录
- 给 API 和 UI 补齐会话级输入输出模型

### 3.2 图表规划与结果表达层

- 从“推荐图表”升级到“规划图表”
- 引入图表 spec、采样、聚合和导出配置
- 设计查询结果与图表的一体化表达对象

### 3.3 治理与审计骨架

- 定义 write action DSL
- 定义审批流、审计日志、回滚令牌的基本对象
- 设计 policy gate 的阶段接口

---

## 4. P2 待办

- 推进管理工作台和更完整的前端交互
- 建立更细粒度的租户、角色和策略系统
- 建立更完整的本地模型评测与热切换机制
- 建立版本化发布与灰度治理

---

## 5. 已知遗留问题

以下遗留问题继续保留，但不再作为主线目标：

- 7 个预存测试失败
- Windows 下 PDF 字体依赖
- openpyxl 与导出环境依赖

这些问题会在主线架构稳定后统一收口，不抢占当前终态架构重构窗口。

---

_最后更新：2026-04-18_
