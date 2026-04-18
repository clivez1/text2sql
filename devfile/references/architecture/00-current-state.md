# 当前状态与边界

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 当前仓库是一个什么系统

当前仓库已经具备一个可运行的 Text2SQL 演示闭环，但仍然是原型底座，不是最终产品形态。

它现在更准确的定位是：

- 一个可运行的 BI 查询 Demo
- 一个本地规则优先、LLM 补充兜底的问答系统
- 一个支持 API 和 Streamlit 的轻量数据分析入口

它还不是：

- 通用数据分析 Agent 平台
- 复杂多轮推理型 Copilot
- 可直接用于生产高风险写操作的数据系统

---

## 2. 根目录现状梳理

### 2.1 当前顶层职责

| 区域 | 当前路径 | 当前职责 | 判断 |
|---|---|---|---|
| 产品源码 | app/ | 主应用代码 | 已开始分层，但新旧并存 |
| 演示数据 | data/ | demo db 和 ddl | 边界清晰 |
| 私有数据 | datasets/ | 真实测试数据占位 | 边界清晰 |
| 运行时数据 | .deploy/ | chroma、日志等运行态产物 | 边界清晰 |
| 工具脚本 | scripts/ | 初始化、导入、验证脚本 | 基本清晰 |
| 测试 | tests/ | unit、integration、api、fixtures | 基本清晰 |
| 使用文档 | docs/ | API、配置、部署、架构说明 | 与规划文档有口径漂移 |
| 规划文档 | devfile/ | 总控、执行方案、专题约束、归档 | 已完成第一轮收束，后续需持续控增 |
| 工程交付 | .github/、Dockerfile、docker-compose.yml、pyproject.toml、requirements.txt | CI、容器化、依赖 | 物理位置较散，但仍可接受 |

### 2.2 当前根目录的主要问题

1. app 已开始进入新分层，但根目录层面还没有统一的整体架构叙事。
2. docs 和 devfile 的职责边界不够稳定，README 和实际规划文档口径出现过漂移。
3. devfile 已完成重编编号和子目录分流，但后续仍需防止专题细节和执行细节重新回流根级。
4. 工程交付文件仍然平铺在根目录，但在当前单仓阶段还没有到必须重构物理位置的程度。

---

## 3. app 当前状态

### 3.1 已建立的新分层骨架

当前 app 下已经出现新的目标层级：

- presentation/
- application/
- domain/
- infrastructure/
- shared/
- config/

这说明代码结构已经从“全塞进 core”转向“分层加分域”的方向。

### 3.2 仍然存在的旧结构

当前核心运行逻辑仍主要在以下旧目录中：

- app/api/
- app/ui/
- app/core/llm/
- app/core/sql/
- app/core/retrieval/
- app/core/orchestrator/
- app/core/chart/
- app/core/auth/
- app/core/security/
- app/core/memory/

因此当前 app 实际处于“新骨架已建立，旧主链路尚未迁移”的过渡期。

---

## 4. 当前运行链路

当前主链路仍然是：

1. 用户输入自然语言问题
2. 进入单轮 pipeline
3. 本地分类判断问题类型和是否需要 LLM
4. 检索 schema 上下文
5. 规则、模板或 fast fallback 优先生 SQL
6. 复杂问题再尝试 LLM
7. 只读安全校验
8. 执行查询
9. 推荐图表并返回结果

这条链路说明当前系统依然是：

- 单轮主链路
- 本地规则优先
- 只读执行
- 演示库友好，而非大库泛化友好

---

## 5. 当前已经具备的能力

### 5.1 查询与执行

- 中文自然语言转 SQL
- SQLite、MySQL、PostgreSQL 支持
- 只读 SQL 安全校验
- 查询结果返回与基本解释

### 5.2 检索与模型

- ChromaDB schema 检索
- 本地 DDL 和字段别名 fallback
- 多 provider 配置和 fallback 链路
- provider 协议层首轮骨架已经落地

### 5.3 输出与工程化

- Streamlit UI
- FastAPI API
- 自动图表推荐
- Excel、PDF 导出
- 健康检查、metrics、trace
- Docker 和 GitHub Actions 基础能力

---

## 6. 当前边界与缺口

### 6.1 业务边界

- 主要仍面向演示销售域
- 复杂分析泛化能力有限
- 不能稳定支撑中大型复杂业务库

### 6.2 产品边界

- session_id 已存在，但没有真正的会话引擎
- 当前没有多轮澄清、追问、任务状态管理
- 当前没有受治理写操作链路

### 6.3 架构边界

- app 新旧结构并存
- 仓库级结构没有正式冻结
- docs 和 devfile 之前存在角色重叠
- devfile 根级已完成收束，但后续仍要保持“总控在根、执行在 10/20、专题在 30”这一约束

---

## 7. 当前结论

当前仓库最需要的不是继续补几条规则，而是把以下三件事做实：

1. 冻结仓库级结构和文档边界
2. 冻结 app 分层迁移方向
3. 把规则优先链路切到 LLM 优先加 grounding 主链路

这就是本轮重编 devfile 和整体架构讨论的出发点。

---

## 8. 当前进入代码重构的准备度

从文档和目录状态看，当前已经具备进入代码重构的前提：

1. 新分层目录已经存在，不需要再从零设计骨架。
2. 旧主链路仍集中在 app/core、app/api、app/ui，迁移对象明确。
3. devfile 已经具备统一重构入口，可直接按 stage1/02-code-refactor/07-refactor-kickoff.md 开工。

因此下一步不再是继续补方案，而是开始首批低风险模块迁移。