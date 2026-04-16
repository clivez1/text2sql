# 数据分析Agent（Text2SQL）技术调研报告

> 调研日期：2026-03-13
> 目标：为人工智能专业研究生提供项目决策依据

---

## 一、技术可行性卡片

### 1.1 核心技术栈

| 层级 | 技术选型 | 推荐库/版本 | 说明 |
|------|----------|-------------|------|
| **LLM层** | OpenAI API / 本地模型 | openai>=1.0 / ollama | 推荐GPT-4o-mini或Qwen2.5-7B降低成本 |
| **Agent框架** | LangGraph | langgraph>=0.4.7 | 状态机+多Agent协作，比LangChain更适合复杂流程 |
| **SQL引擎** | SQLAlchemy | sqlalchemy>=2.0 | 支持多种数据库后端 |
| **向量检索** | ChromaDB | chromadb>=0.5 | RAG存储Schema和示例SQL |
| **前端** | Streamlit/Gradio | streamlit>=1.49 / gradio>=5.43 | 快速构建Demo界面 |
| **可视化** | Plotly | plotly>=5.17 | 交互式图表 |
| **数据库** | SQLite/PostgreSQL | - | SQLite用于Demo，PG用于生产 |

### 1.2 关键依赖

```
核心依赖：
- LLM API: OpenAI / Anthropic / 本地Ollama
- 数据库连接: SQLAlchemy (支持MySQL/PG/ClickHouse等)
- 向量存储: ChromaDB 或 Qdrant（RAG存储Schema信息）

可选依赖：
- 数据库: PostgreSQL（生产级）或SQLite（开发）
- 缓存: Redis（可选，用于缓存SQL结果）
- 监控: LangSmith（可选，用于调试Agent）
```

### 1.3 技术风险点

| 风险 | 等级 | 缓解方案 |
|------|------|----------|
| **Schema理解错误** | 高 | RAG检索相似表结构+示例SQL，Few-shot学习 |
| **复杂SQL生成失败** | 中 | 分步生成（先Schema Linking，再SQL生成） |
| **中文语义理解** | 中 | 使用中文优化的模型（Qwen/GLM） |
| **LLM API成本** | 低 | 本地模型或GPT-4o-mini降低成本 |
| **数据库安全** | 高 | 只读权限+SQL注入检测+白名单表 |

### 1.4 6周MVP范围

| 周次 | 交付物 | 可验收标准 |
|------|--------|-----------|
| W1 | 环境搭建+Demo跑通 | 本地运行Vanna或SQLBot Demo |
| W2 | Schema导入+基础SQL生成 | 能回答单表查询问题 |
| W3 | 多表JOIN+可视化 | 能处理2-3表关联，输出图表 |
| W4 | RAG优化+中文支持 | 提高准确率，支持中文问题 |
| W5 | 错误修复+UI优化 | Demo可演示，界面友好 |
| W6 | 文档+演示准备 | 项目README、演示PPT、面试话术 |

---

## 二、参考项目调研

### 2.1 核心推荐项目（必看）

#### ⭐ Vanna (22,950 stars) - 首选
- **仓库**: https://github.com/vanna-ai/vanna
- **功能覆盖**: NL→SQL→Chart→Summary 全流程
- **技术栈**: Python + FastAPI + OpenAI/Anthropic + ChromaDB
- **可复现难度**: ⭐⭐（低）
- **亮点**:
  - 开箱即用，3行代码可跑Demo
  - 内置Web组件`<vanna-chat>`
  - 支持多种LLM和数据库
  - RAG存储训练数据（DDL+示例SQL）
- **复现建议**: 直接基于Vanna二次开发

#### ⭐ SQLBot (5,670 stars) - 中文场景首选
- **仓库**: https://github.com/dataease/SQLBot
- **功能覆盖**: NL→SQL→Chart + 工作空间隔离
- **技术栈**: Python + Docker + 多种LLM
- **可复现难度**: ⭐⭐（低）
- **亮点**:
  - 中文文档完善
  - Docker一键部署
  - 支持工作空间隔离
  - 可嵌入第三方系统
- **复现建议**: 部署后学习其Prompt工程

#### ⭐ OpenChatBI (516 stars) - 架构参考
- **仓库**: https://github.com/zhongyu09/openchatbi
- **功能覆盖**: NL→SQL→Chart + 时序预测 + 代码执行
- **技术栈**: LangGraph + LangChain + Streamlit/Gradio
- **可复现难度**: ⭐⭐⭐（中）
- **亮点**:
  - 基于LangGraph的现代Agent架构
  - 支持MCP工具集成
  - Schema Linking设计优秀
  - 代码可直接学习
- **复现建议**: 学习其Agent工作流设计

### 2.2 辅助参考项目

| 项目 | Stars | 用途 |
|------|-------|------|
| WrenAI | 14,597 | 企业级GenBI参考 |
| DB-GPT-Hub | 1,966 | Text2SQL微调资源 |
| Awesome-Text2SQL | 3,530 | 论文+基准测试大全 |
| NL2SQL_Handbook | 1,349 | 技术路线指南 |

### 2.3 Dify工作流

已有Dify Text2SQL工作流可直接导入：
- `kiwiwu02/Dify` - 5个可导入的Agent/Workflow（含RAG→SQL查询）

---

## 三、差异化建议

### 3.1 市面产品不足

| 痛点 | 现状 | 机会 |
|------|------|------|
| **冷启动难** | 需要大量示例SQL训练 | 提供智能Schema分析向导 |
| **中文体验差** | 多数项目英文为主 | 深度优化中文语义理解 |
| **可视化单一** | 图表类型有限 | 推荐最佳图表类型 |
| **缺少解释** | 只输出SQL，不懂为什么 | 添加SQL解释+业务洞察 |
| **调试困难** | 错误后难以排查 | 提供交互式调试面板 |

### 3.2 差异化功能点（可快速实现）

1. **SQL解释器** - 用自然语言解释生成的SQL，帮助用户理解
2. **智能图表推荐** - 根据数据特征自动推荐最佳图表类型
3. **追问澄清** - 模糊问题时主动追问，而非盲目生成
4. **SQL修正对话** - 错误时提供修复建议，用户可手动调整
5. **查询历史学习** - 用户修正后的SQL自动加入训练集

### 3.3 面试核心亮点

```
技术亮点：
1. RAG增强的Schema理解 - 解决大模型不懂数据库结构的问题
2. Few-shot学习 - 用少量示例快速适配新数据库
3. Agent工作流编排 - LangGraph实现多步推理
4. 安全沙箱 - 只读权限+SQL白名单

业务亮点：
1. 真实场景落地 - 可现场演示实际业务数据
2. 产品思维 - 不只做SQL生成，还做用户体验
3. 工程化能力 - Docker部署+API设计+错误处理
```

---

## 四、MVP规格定义

### 4.1 核心功能清单

| 优先级 | 功能 | 说明 |
|--------|------|------|
| P0 | 自然语言转SQL | 核心能力，单表查询必过 |
| P0 | SQL执行+结果展示 | 必须能执行并展示数据 |
| P1 | 多表JOIN查询 | 2-3表关联，覆盖80%场景 |
| P1 | 图表自动生成 | 根据数据生成柱状图/折线图/饼图 |
| P2 | SQL解释 | 解释SQL含义，增强可信度 |
| P2 | 中文支持 | 中文问题→中文回复 |

### 4.2 演示场景设计

**场景1：销售数据查询**
```
用户："上个月销售额最高的前5个产品是什么？"
系统：→ 生成SQL → 执行 → 表格展示 → 柱状图 → 自然语言总结
```

**场景2：多维度分析**
```
用户："对比一下北京和上海各季度的订单量"
系统：→ JOIN查询 → 分组聚合 → 对比图表 → 洞察分析
```

**场景3：追问澄清**
```
用户："查询用户数据"
系统："请问您想查询哪些字段？按什么条件筛选？"
用户："只要姓名和注册时间，按最近一个月筛选"
系统：→ 精确SQL → 结果展示
```

### 4.3 技术栈清单（精确定版）

```
# requirements.txt
langgraph>=0.4.7
langchain-openai>=0.3.18
langchain-community>=0.3.27
langchain-chroma>=0.2.5
sqlalchemy>=2.0.41
chromadb>=0.5.0
openai>=1.0.0
streamlit>=1.49.0
plotly>=5.17.0
pandas>=2.2.0
python-dotenv>=1.0.0

# 数据库驱动（根据需求选装）
psycopg2-binary  # PostgreSQL
pymysql          # MySQL
```

### 4.4 时间规划

```
Week 1: 项目启动
- Day 1-2: 环境搭建，运行Vanna Demo
- Day 3-4: 阅读Vanna源码，理解架构
- Day 5-7: 导入测试数据库，测试基础查询

Week 2: 核心功能开发
- Day 1-3: 实现Schema导入和RAG存储
- Day 4-5: 优化SQL生成Prompt
- Day 6-7: 测试单表查询准确率

Week 3: 多表+可视化
- Day 1-3: 实现JOIN查询逻辑
- Day 4-5: 集成Plotly图表生成
- Day 6-7: 测试并修复Bug

Week 4: 中文优化+体验
- Day 1-3: 中文Prompt优化，测试中文场景
- Day 4-5: 添加SQL解释功能
- Day 6-7: 添加追问澄清逻辑

Week 5: 打磨+部署
- Day 1-3: UI美化，错误处理优化
- Day 4-5: Docker部署方案
- Day 6-7: 端到端测试

Week 6: 文档+演示
- Day 1-3: README文档，API文档
- Day 4-5: 演示PPT，演示脚本
- Day 6-7: 模拟面试，准备问答
```

---

## 五、决策建议

### 5.1 项目可行性评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 技术成熟度 | ⭐⭐⭐⭐⭐ | 开源项目丰富，可直接复用 |
| 学习价值 | ⭐⭐⭐⭐ | 涵盖LLM+Agent+RAG+数据库 |
| 时间可控性 | ⭐⭐⭐⭐ | 6周足够，有明确里程碑 |
| 面试价值 | ⭐⭐⭐⭐⭐ | 热门方向，可深入讨论 |
| 差异化空间 | ⭐⭐⭐ | 基础功能同质化，需做特色 |

### 5.2 推荐路线

```
推荐方案：基于Vanna二次开发
理由：
1. 开箱即用，节省搭建时间
2. 架构清晰，易于理解和扩展
3. 社区活跃，遇到问题易解决
4. 可专注差异化功能开发

技术投入重点：
1. Prompt工程（SQL生成质量）
2. RAG优化（Schema理解）
3. 用户体验（追问澄清+SQL解释）
4. 中文优化（本地化体验）
```

### 5.3 关键成功因素

1. **选对基线项目** - Vanna vs SQLBot vs 从零开始
2. **控制范围** - MVP只做核心功能，避免蔓延
3. **真实数据** - 用真实业务数据演示，而非玩具数据
4. **可解释性** - 能说清楚为什么这么设计
5. **演示流畅** - 提前演练，准备好容错方案

---

## 六、附录：快速启动命令

```bash
# 方案A: Vanna快速启动
pip install vanna[chromadb,openai,streamlit]
export OPENAI_API_KEY="your-key"
python -c "from vanna.streamlit import VannaStreamlit; VannaStreamlit().run()"

# 方案B: SQLBot Docker启动
docker run -d --name sqlbot -p 8000:8000 -p 8001:8001 dataease/sqlbot

# 方案C: OpenChatBI克隆学习
git clone https://github.com/zhongyu09/openchatbi
cd openchatbi && uv sync
cp example/config.yaml openchatbi/config.yaml
# 编辑config.yaml填入API Key
python run_streamlit_ui.py
```

---

*报告生成时间: 2026-03-13*