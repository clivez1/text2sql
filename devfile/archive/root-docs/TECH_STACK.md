# Dify Text2SQL Agent 技术栈

## 核心技术栈

### 主要语言
- **Python 3.10+**: 主要开发语言，无算法门槛，纯开发导向

### LLM 集成
- **统一 LLM Adapter**: 支持多提供商动态切换
  - **Bailian Code Plan**: 默认端点 `https://coding.dashscope.aliyuncs.com/v1`
  - **OpenAI Compatible**: 标准 OpenAI API 兼容接口
- **Vanna AI**: SQL 生成核心库（基于 LLM 的 NL2SQL）

### 数据库
- **SQLite**: 内置 Demo 数据库（销售数据示例）
- **PostgreSQL**: 企业级数据库支持
- **MySQL**: 企业级数据库支持
- **SQLAlchemy**: 数据库抽象层，统一连接管理

### Web 框架
- **Streamlit**: 快速构建交互式 UI 界面
- **FastAPI**: 后端 API 服务（健康检查、schema 接口）

### 安全与校验
- **SQL 注入防护**: 查询语句安全校验
- **权限控制**: 只读模式、表级别访问控制
- **敏感字段过滤**: 自动识别和屏蔽敏感数据

## 辅助工具

### 开发工具
- **Virtual Environment**: Python 虚拟环境隔离
- **pip**: 依赖包管理
- **pytest**: 单元测试框架

### 部署工具
- **Docker**: 容器化部署
- **docker-compose**: 多服务编排
- **CloudBase**: 面向中国大陆用户的云部署方案

### 监控与日志
- **Python logging**: 标准日志记录
- **Health Check**: FastAPI 健康检查接口

## 依赖管理

### 核心依赖
- `vanna`: NL2SQL 核心库
- `streamlit`: Web UI 框架
- `fastapi`: API 服务框架
- `sqlalchemy`: 数据库 ORM
- `psycopg2`: PostgreSQL 驱动
- `pymysql`: MySQL 驱动

### 开发依赖
- `pytest`: 测试框架
- `black`: 代码格式化
- `flake8`: 代码质量检查

## 架构设计原则

### CLI-first
- 每个功能模块都可通过命令行独立验证
- 支持脚本化测试和调试

### 模块化设计
- **LLM Adapter**: 统一 LLM 接口抽象
- **Database Connector**: 统一数据库连接抽象  
- **Security Layer**: 统一安全校验层
- **Visualization Engine**: 图表生成引擎

### 爆炸半径控制
- 小步提交，渐进式开发
- 每个功能都有完整的回退机制
- LLM 失败时自动 fallback 到规则引擎

## 技术栈优势

1. **求职友好**: Python + SQL + Web 开发，岗位匹配度高
2. **学习曲线平滑**: 无需算法背景，纯工程实现
3. **企业实用**: 符合实际生产环境技术选型
4. **展示效果好**: UI 界面直观，Demo 效果明显
5. **扩展性强**: 模块化设计便于后续功能扩展