# Dify Text2SQL Agent 项目计划

## 项目来源
基于 [Dify应用市场调研报告](/home/clawz/.openclaw/workspace-cos/outputs/dify-research-draft.md) 的 Top 3 推荐方向：
- **定位**：数据分析Agent（Text2SQL/图表生成/报告生成）
- **目标**：构建可展示的技术作品，用于求职展示
- **优势**：BI+AI热门方向、纯Python开发、无算法门槛

## 核心功能路线图

### Week1 MVP（已完成）
- ✅ SQLite Demo 销售数据库
- ✅ Streamlit 最小界面
- ✅ 统一 LLM Adapter（Bailian Code Plan / OpenAI Compatible）
- ✅ 自动 fallback 机制

### Week2 增强
- [ ] 多数据库支持（PostgreSQL/MySQL）
- [ ] SQL 安全校验（防注入/权限控制）
- [ ] 完善测试覆盖率

### Week3 集成
- [ ] 图表生成（基于查询结果自动可视化）
- [ ] 报告导出功能（PDF/Excel）

### Week4 部署
- [ ] 企业微信/钉钉通知集成
- [ ] Docker 容器化部署
- [ ] 云服务部署方案

## 技术栈
- **核心**：Python + Dify工作流
- **辅助**：FastAPI（接口开发）+ PostgreSQL/MySQL（数据存储）
- **扩展**：Docker（部署）+ Git（版本管理）

## 验收标准
- 每个Week有可演示的完整功能
- 代码符合生产级质量标准
- 文档完整（README + API文档）