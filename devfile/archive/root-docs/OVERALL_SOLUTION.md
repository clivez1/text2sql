# Dify Text2SQL Agent 整体方案

## 1. 架构概览

### 系统架构图
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │    │   LLM Adapter    │    │  Database Layer │
│ (Natural Lang)  │───▶│ (Vanna + Bailian)│───▶│ (MySQL/SQLite)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌──────────────────┐    ┌─────────────────┐
         │              │ Security Layer   │    │ Query Execution │
         │              │ (SQL Injection   │    │ & Result Fetch  │
         │              │  Protection)     │    └─────────────────┘
         │              └──────────────────┘            │
         │                       │                      │
         ▼                       ▼                      ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Visualization   │◀───│  Result Processor│◀───│  Query Results  │
│ Engine          │    │ (Data Analysis & │    │ (Structured)    │
│ (Charts/Tables) │    │  Formatting)     │    └─────────────────┘
└─────────────────┘    └──────────────────┘
         │
         ▼
┌─────────────────┐
│ Output Delivery │
│ (UI/API/Export) │
└─────────────────┘
```

### 核心组件说明
1. **LLM Adapter**: 统一接口层，支持 Bailian Code Plan 和 OpenAI Compatible
2. **Security Layer**: SQL 注入防护、权限控制、敏感字段过滤
3. **Database Layer**: MySQL/SQLite 抽象层，统一连接管理
4. **Visualization Engine**: 自动图表生成和结果格式化
5. **Output Delivery**: 多渠道结果输出（Streamlit UI、FastAPI、导出文件）

## 2. 详细设计方案

### 2.1 LLM 集成层
**组件**: `app/core/llm/`
- **Adapter Interface**: 统一 LLM 调用接口
- **Bailian Provider**: 专为代码生成优化的端点集成
- **OpenAI Provider**: 标准 OpenAI API 兼容
- **Fallback Mechanism**: LLM 失败时回退到规则引擎

**关键技术点**:
- 动态切换 LLM 提供商
- 上下文学习（基于数据库 schema）
- 错误处理和重试机制

### 2.2 安全校验层
**组件**: `app/core/security/`
- **SQL Validator**: 语法和语义校验
- **Permission Manager**: 表级别和字段级别权限控制
- **Sensitive Data Filter**: 自动识别和屏蔽敏感字段
- **Query Logger**: 所有查询操作审计日志

**安全规则**:
- 只读模式强制启用
- 禁止 DDL 操作（CREATE/DROP/ALTER）
- 限制查询复杂度（JOIN 数量、子查询深度）
- 敏感字段白名单机制

### 2.3 数据库抽象层
**组件**: `app/core/database/`
- **Connection Manager**: 连接池管理
- **MySQL Connector**: MySQL 特定实现
- **SQLite Connector**: SQLite 特定实现  
- **Schema Analyzer**: 数据库结构分析器

**功能特性**:
- 统一连接接口
- 自动连接重试
- Schema 信息提取（用于 LLM 上下文）
- 查询性能监控

### 2.4 可视化引擎
**组件**: `app/core/visualization/`
- **Data Analyzer**: 自动识别数据类型和分布
- **Chart Recommender**: 基于数据特征推荐图表类型
- **Chart Renderer**: 生成交互式图表
- **Table Formatter**: 结构化表格展示

**图表类型支持**:
- 柱状图（分类数据比较）
- 折线图（时间序列趋势）
- 饼图（比例分布）
- 散点图（相关性分析）
- 表格（详细数据展示）

### 2.5 输出交付层
**组件**: `app/ui/` + `app/api/`
- **Streamlit UI**: 交互式 Web 界面
- **FastAPI Service**: RESTful API 接口
- **Export Module**: PDF/Excel 导出功能
- **Notification Service**: 企业微信/钉钉通知

**交付渠道**:
- Web 界面（Demo 展示）
- API 接口（集成使用）
- 文件导出（报告生成）
- 即时通知（结果推送）

## 3. 数据流设计

### 主要数据流
1. **用户输入**: 自然语言问题
2. **LLM 处理**: 转换为 SQL 查询
3. **安全校验**: 验证 SQL 安全性和权限
4. **数据库执行**: 执行查询并获取结果
5. **结果处理**: 分析数据特征并格式化
6. **可视化输出**: 生成图表和表格
7. **多渠道交付**: UI/API/导出/通知

### 异常处理流
- **LLM 失败**: 回退到规则引擎或返回错误
- **SQL 错误**: 返回具体错误信息和建议
- **权限拒绝**: 明确告知权限不足
- **超时处理**: 设置查询超时和重试机制

## 4. 部署架构

### 开发环境
- **本地运行**: Python 虚拟环境 + Streamlit
- **快速启动**: 一键脚本初始化 Demo 数据库
- **调试支持**: 详细日志和错误追踪

### 生产环境
- **Docker 容器**: 标准化部署单元
- **docker-compose**: 多服务编排（UI + API + DB）
- **CloudBase**: 面向中国大陆用户的云部署方案
- **健康检查**: FastAPI 健康检查接口

### 监控与运维
- **日志收集**: 标准化日志格式
- **性能指标**: 查询响应时间、成功率
- **资源监控**: CPU/内存使用情况
- **告警机制**: 关键错误自动告警

## 5. 开发里程碑

### Week 1: MVP 基础
- [ ] SQLite Demo 数据库
- [ ] Streamlit 基础界面
- [ ] Vanna AI 集成
- [ ] Bailian Code Plan 适配

### Week 2: MySQL 支持
- [ ] MySQL 连接器实现
- [ ] 数据库抽象层完善
- [ ] 安全校验层基础功能
- [ ] 多数据库切换测试

### Week 3: 可视化增强
- [ ] 数据分析引擎
- [ ] 图表推荐算法
- [ ] 交互式图表渲染
- [ ] 结果导出功能

### Week 4: 生产就绪
- [ ] 完整安全校验
- [ ] Docker 容器化
- [ ] CloudBase 部署方案
- [ ] 完整文档和测试

## 6. 风险与应对

### 技术风险
- **LLM 准确率不足**: 通过上下文学习和反馈循环持续优化
- **数据库兼容性问题**: 严格的测试覆盖和抽象层隔离
- **性能瓶颈**: 查询优化和缓存机制

### 项目风险
- **时间约束**: 严格遵循 4 周里程碑，优先核心功能
- **需求蔓延**: 严格按照项目章程边界控制范围
- **技术选型变更**: 保持架构灵活性，便于替换组件

### 应对策略
- **渐进式开发**: 小步快跑，持续验证
- **回退机制**: 每个关键组件都有备用方案
- **质量保证**: 自动化测试和代码审查