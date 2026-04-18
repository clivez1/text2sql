# 目标架构方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 为什么这次要从根目录重看架构

上一轮已经证明，只优化 app 内部结构是不够的。

原因很简单：

1. 代码可以逐步分层，但仓库根目录如果没有统一边界，开发者仍然不知道脚本、文档、规划、数据和归档应该放在哪里。
2. docs、devfile、README、AGENTS 如果继续各讲一套，架构就会再次失真。
3. 中大型数据库、Copilot、写操作治理这种能力不是单个模块问题，而是仓库级组织问题。

因此，这次目标不是只给 app 画一张图，而是同时冻结：

- 仓库级结构
- 代码级结构
- 文档级结构
- 迁移原则

---

## 2. 三轮架构优化讨论

### 2.1 第一轮：只优化 app，根目录不动

#### 做法

- 继续推进 app 的 presentation、application、domain、infrastructure 分层
- 根目录维持现状
- devfile 继续叠加专题文档

#### 优点

- 改动小
- 不影响现有根目录和部署路径

#### 缺点

- 只能解决代码阅读问题，不能解决仓库整体认知问题
- docs、devfile、README 仍然容易漂移
- 后续越做越容易在根目录再堆“例外”目录

#### 结论

这一轮已经不够。

### 2.2 第二轮：仓库分区加 app 分层

#### 做法

- 仓库根目录维持单仓形态，不急着引入 src、.devops、.config 等新顶层
- 先明确每个现有顶层目录的职责边界
- app 内部继续走分层加分域结构
- docs 和 devfile 正式分工

#### 优点

- 改动成本可控
- 与现有 Docker、CI、导入路径兼容
- 足以支撑接下来 3 到 6 个月的演进

#### 缺点

- 工程交付文件仍然部分平铺在根目录
- 过渡期 app/core 仍然存在

#### 结论

这是当前仓库最合适的执行方案。

### 2.3 第三轮：完全规范化根目录

#### 做法

- 引入 src、.devops、.config 等更强规范的根目录
- 重排导入路径、容器路径和 CI 路径
- 进一步把工程交付文件独立分区

#### 优点

- 最整齐
- 对多应用、多语言、多部署形态更友好

#### 缺点

- 当前收益不如成本高
- 会过早引入根目录迁移成本
- 与当前“轻量级单仓”目标不完全匹配

#### 结论

保留为长期可选项，不作为当前主线。

---

## 3. 当前推荐方案

当前主线采用第二轮方案：仓库分区加 app 分层。

也就是：

- 根目录先做职责冻结，而不是大搬家
- app 继续做真实分层迁移
- docs 和 devfile 明确各自职责
- archive 统一承接历史方案

这既能避免继续失控，也不会引入过度工程化。

---

## 4. 目标仓库级结构

```text
text2sql-0412/
├── app/                        # 产品源码区
│   ├── presentation/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   ├── core/                  # 过渡区，只减不增
│   ├── shared/
│   └── config/
├── data/                       # 版本化 demo 数据
├── datasets/                   # 非版本化私有测试数据
├── .deploy/                    # 非版本化运行时产物
├── scripts/                    # 初始化、验证、运维脚本
├── tests/                      # 质量验证区
├── docs/                       # 当前运行态文档
├── devfile/                    # 架构规划与归档
├── .github/                    # CI/CD
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── README.md
├── AGENTS.md
├── .env.example
└── .impKey.example
```

---

## 5. 顶层职责冻结

### 5.1 app

只承载产品代码，不再继续把规划、临时脚本、历史实验塞入其中。

### 5.2 data、datasets、.deploy

三者必须长期分离：

- data：可入 git 的 demo 资产
- datasets：不可入 git 的测试或隐私资产
- .deploy：运行时可清理产物

### 5.3 scripts

只承载初始化、验证、导入和运维工具，不承载核心业务流程实现。

### 5.4 tests

围绕产品能力组织验证，而不是围绕临时实现堆测试。

### 5.5 docs

只描述当前可运行系统：

- 快速启动
- 配置
- API
- 部署
- 当前运行态架构

### 5.6 devfile

只描述未来方案、阶段路线、架构决策、历史归档。

---

## 6. 目标代码级结构

### 6.1 分层结构

app 下的目标结构为：

- presentation：对外入口和传输适配
- application：流程编排、用例、状态机和任务调度
- domain：领域对象、策略、规则接口
- infrastructure：模型、检索、执行、存储、安全、观测
- shared：跨层共享 DTO、types、utils
- config：配置、环境变量、feature flags

### 6.2 为什么不是简单 MVC

MVC 对页面驱动应用足够，但对 AI 加数据执行系统过于粗糙。

如果继续用简单 MVC：

- model 会同时塞入领域对象、执行逻辑和 provider 适配
- controller 会膨胀成 LLM 路由、SQL 执行、审批和会话状态机的总垃圾桶
- retrieval、policy、audit 这类能力没有稳定落点

所以这里采用的是分层加分域，而不是简单 MVC。

---

## 7. 当前到目标的迁移映射

| 当前路径 | 目标路径 | 说明 |
|---|---|---|
| app/api/ | app/presentation/api/ | FastAPI 入口 |
| app/ui/ | app/presentation/ui/ | Streamlit 入口 |
| app/core/orchestrator/ | app/application/orchestration/ | pipeline、workflow、router |
| app/core/memory/ | app/application/conversations/ + app/domain/conversation/ + app/infrastructure/persistence/ | 会话编排、对象、存储分离 |
| app/core/llm/ | app/infrastructure/llm/ + app/application/orchestration/ | provider 下沉，router 上移 |
| app/core/retrieval/ | app/infrastructure/retrieval/ + app/domain/catalog/ | 检索实现与 catalog 对象分离 |
| app/core/sql/ | app/infrastructure/execution/ + app/domain/query/ + app/application/analytics/ | 执行器、对象、用例拆开 |
| app/core/chart/ | app/domain/visualization/ + app/application/analytics/ | 图表对象和图表用例拆开 |
| app/core/auth/、app/core/security/ | app/infrastructure/security/ + app/domain/governance/ | 技术安全与治理规则拆开 |
| app/core/logging.py、metrics.py | app/infrastructure/observability/ | 观测能力统一收口 |

---

## 8. 迁移原则

1. 先冻结边界，再逐步迁移，不搞一次性大搬家。
2. 新能力优先进入新分层目录，不再落到 app/core。
3. docs 和 devfile 分工先稳定，再逐步修正 README、AGENTS 等入口文档。
4. 根目录暂不引入额外复杂顶层，保持单仓轻量结构。
5. 等第二执行阶段完成后，再判断是否需要第三轮根目录规范化。

---

## 9. 本文件的作用

本文件负责冻结整体架构边界。

- 现状边界看 references/architecture/00-current-state.md
- 执行顺序看 references/architecture/02-execution-roadmap.md
- LLM 与检索看 references/themes/01-llm-and-retrieval.md
- Copilot、可视化与写操作看 references/themes/02-copilot-visualization-and-actions.md
- 评测与发布看 references/themes/03-evaluation-and-release.md
- 仓库逐目录物理整理看 stage1/01-repository-physical-reorg/
- 逐层代码迁移与 cutover 看 stage1/02-code-refactor/