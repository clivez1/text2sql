# 13. 中大型数据库检索与语义层方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 当前问题

当前检索方案仍以演示库为中心，主要问题有：

- schema 规模小，字段别名与 DDL fallback 足够
- Chroma 检索没有和 join graph、业务语义层结合
- 结果更像“文档片段召回”，不是“可执行的 schema grounding”

这在中大型库上会失效。

---

## 2. 目标能力

系统需要能把自然语言问题稳定映射到：

- 候选业务实体
- 候选表
- 候选列
- 候选指标与维度
- 可行 join path
- 相关时间语义
- 推荐过滤条件

---

## 3. 必须采集的元数据

### 3.1 结构元数据

- catalog / schema / table / column
- 主键、外键、索引、唯一约束
- 视图、物化视图、函数、分区信息

### 3.2 统计元数据

- 行数
- 列基数
- 时间范围
- 常见空值比例
- 频繁值摘要

### 3.3 语义元数据

- 业务别名
- 指标口径
- 维度层级
- 时间字段角色
- 租户与权限标签

### 3.4 行为元数据

- 历史成功 SQL
- 历史失败 SQL
- 人工修正规则
- 常见图表表达

---

## 4. 检索链路目标形态

1. 问题解析生成 retrieval plan
2. 先做 lexical / BM25 召回
3. 再做向量召回
4. 基于 join graph 扩展可联接候选
5. 使用 reranker 压缩上下文
6. 组装 grounding package
7. 交给 SQL draft 阶段

grounding package 至少应包含：

- top tables
- top columns
- join edges
- relevant metrics / dimensions
- examples
- risk hints

---

## 5. 存储与缓存建议

### 5.1 Catalog Store

保存 schema snapshot、关系图、统计摘要和语义映射。

### 5.2 Retrieval Index

保存 lexical index、vector index、rerank 输入。

### 5.3 Runtime Cache

保存：

- 热门表列召回结果
- 热门问法 grounding 结果
- 历史成功 plan

---

## 6. 关键工程决策

1. 不再把 `FIELD_ALIASES` 作为核心能力，而是升级为业务语义层的一小部分。
2. 不再把“返回几段 schema 文本”视为检索成功，而是以 grounding 质量为目标。
3. 检索系统必须支持增量刷新和 schema 版本化。
4. 检索系统必须与 policy 和 tenant 信息协同工作。

---

## 7. 实施顺序

### Step 1：Catalog 数据模型

- schema snapshot
- table / column entity
- join edge
- semantic alias

### Step 2：采集脚本

- 从数据库采集元数据
- 从规则、示例 SQL、人工词表采集语义资产

### Step 3：检索接口抽象

- lexical retriever
- vector retriever
- reranker
- join path resolver

### Step 4：grounding package 标准化

- 定义统一输出对象
- 给 Router 和 SQL draft 复用

### Step 5：benchmark

- 小库 / 中库 / 大库分别评测

---

## 8. 验收标准

- 能在中大型库上稳定召回候选表列和 join path
- grounding package 可直接支持 SQL draft
- schema 变化后可增量刷新索引
- 对不同数据库方言不依赖硬编码演示库映射
