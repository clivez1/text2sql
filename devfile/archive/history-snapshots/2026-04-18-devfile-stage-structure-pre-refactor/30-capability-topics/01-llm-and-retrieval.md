# 30-01. LLM 优先与检索底座方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 当前问题

当前系统的主路由仍然是：

- 先分类
- 先判断 needs_llm
- 简单问题走规则、模板或 fast fallback
- 复杂问题才进入 LLM

与此同时，当前检索仍然以演示库为中心：

- Chroma 检索更像文档片段召回
- 检索没有真正结合 join graph 和业务语义层
- grounding 结果还不足以支撑中大型数据库

因此当前两条问题必须一起看：

1. 主路由仍然不是 LLM 优先
2. 检索还不是可执行的 schema grounding

---

## 2. 目标读路径

目标读路径应改成：

question -> plan intent -> retrieve grounding -> draft sql -> validate -> repair -> execute -> explain

在这个链路里：

- LLM 负责意图规划和草拟
- 检索层负责 grounding
- 执行层负责验证和修复
- 规则资产只做辅助，不再掌握主路由控制权

---

## 3. Provider 协议层要求

### 3.1 必须支持的协议

- OpenAI compatible
- Anthropic messages
- local gateway

### 3.2 必须统一的能力

- 健康检查
- 文本补全或对话接口
- 结构化输出能力
- 错误分类
- timeout 和 retry
- 主模型加 fallback 顺序

### 3.3 配置要求

配置不仅表达第几个 provider，还要表达：

- protocol
- purpose
- timeout
- max tokens
- retry
- 预算上限
- fallback 顺序

---

## 4. 规则资产的重新定位

本地规则不删除，但角色必须变化：

### 4.1 few-shot 资产

- 高价值问法和高质量 SQL 示例
- 进入 prompt，而不是直接短路主流程

### 4.2 修复资产

- LIMIT 修正
- 危险关键字修正
- 方言替换
- 字段别名回补

### 4.3 兜底资产

- 检索失败时兜底
- 模型失败时兜底
- 必须明确标记为 fallback 结果

### 4.4 回归资产

- 用于评测和回归
- 防止主链路演进后退化

---

## 5. 检索底座目标

系统需要把自然语言问题稳定映射到：

- 候选业务实体
- 候选表
- 候选列
- 候选指标和维度
- 可行 join path
- 时间语义
- 推荐过滤条件

---

## 6. 必须采集的元数据

### 6.1 结构元数据

- catalog、schema、table、column
- 主键、外键、索引、唯一约束
- 视图、函数、分区信息

### 6.2 统计元数据

- 行数
- 列基数
- 时间范围
- 空值比例
- 高频值摘要

### 6.3 语义元数据

- 业务别名
- 指标口径
- 维度层级
- 时间字段角色
- 权限与租户标签

### 6.4 行为元数据

- 历史成功 SQL
- 历史失败 SQL
- 人工修正规则
- 常见图表表达

---

## 7. 检索链路目标形态

1. 问题解析生成 retrieval plan
2. lexical 或 BM25 召回
3. 向量召回
4. 基于 join graph 扩展可联接候选
5. reranker 压缩上下文
6. 组装 grounding package
7. 交给 SQL draft 阶段

grounding package 至少包含：

- top tables
- top columns
- join edges
- relevant metrics 或 dimensions
- examples
- risk hints

---

## 8. 目标落点

### 8.1 代码落点

- provider adapters 和 model gateway：app/infrastructure/llm/
- retrieval interfaces、rerank、join path：app/infrastructure/retrieval/
- grounding 相关领域对象：app/domain/catalog/
- Router 和任务编排：app/application/orchestration/
- SQL draft、validation、repair 相关对象：app/domain/query/ 和 app/infrastructure/execution/

### 8.2 核心对象

- QueryIntent
- GroundingPackage
- CatalogMatch
- SQLDraft
- ValidationIssue
- RepairHistory

---

## 9. 实施顺序

### Step 1

- 完成 provider 协议抽象
- 固化 Router 输入输出对象

### Step 2

- 建立 metadata catalog 数据模型
- 抽象 grounding package

### Step 3

- 建立 validation 加 repair loop
- 下放规则角色

### Step 4

- 建立 benchmark
- 对比迁移前后成功率、延迟、成本和 fallback 率

---

## 10. 验收标准

- 简单问题不再依赖 needs_llm=False 才能进入主链路
- LLM 可以统一承担 planning 和 drafting
- grounding package 可以直接支撑 SQL 草拟
- OpenAI、Anthropic、local gateway 三类协议都可走健康检查和主链路
- 中大型库上能稳定召回候选表列和 join path