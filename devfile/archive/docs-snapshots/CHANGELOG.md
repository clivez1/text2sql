# Changelog

> 版本历史与变更记录

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [Unreleased]

### 计划中
- 支持多轮对话上下文
- 支持自定义 Prompt 模板
- 支持 API 认证

---

## [3.0.0] - 2026-03-22

### Added（新增）
- **ChromaDB 向量检索**：Schema 和示例 SQL 的 RAG 存储
- **Vanna AI 集成**：基于 Vanna 的 Text2SQL 核心引擎
- **多 LLM Provider**：支持百炼 Code Plan、OpenAI 兼容 API
- **智能图表推荐**：自动识别数据类型推荐柱状图/折线图/饼图
- **多数据库支持**：SQLite / MySQL / PostgreSQL 连接器
- **SQL 安全校验**：注入防护、表白名单、只读模式
- **FastAPI REST API**：/ask, /health, /schemas 端点
- **Streamlit Web UI**：可视化查询界面
- **PDF/Excel 导出**：查询结果导出功能
- **Docker 部署**：Dockerfile + docker-compose.yml

### Changed（变更）
- 从 FAISS 轻量化版本切换回 ChromaDB 版本
- LLM 适配层重构，支持统一 Provider 接口

### Fixed（修复）
- SQLAlchemy 2.x API 兼容性问题
- SQLite 只读模式连接问题

---

## [2.0.0] - 2026-03-19

### Added
- MySQL 数据库连接器
- PostgreSQL 数据库连接器
- SQL 注入防护模块
- 表级权限白名单
- 查询超时限制

### Changed
- 数据库抽象层重构
- 配置管理优化

---

## [1.0.0] - 2026-03-13

### Added
- 项目初始化
- 基础目录结构
- SQLite Demo 数据库
- Streamlit UI 骨架
- 基础 SQL 生成（规则匹配）
- 简单查询执行

---

## 版本命名规则

- **主版本号 (Major)**：不兼容的 API 变更
- **次版本号 (Minor)**：向后兼容的功能新增
- **修订号 (Patch)**：向后兼容的问题修复

---

## 版本历史一览

| 版本 | 日期 | 主要特性 |
|------|------|----------|
| 3.0.0 | 2026-03-22 | ChromaDB + Vanna AI + 多 Provider |
| 2.0.0 | 2026-03-19 | 多数据库 + 安全校验 |
| 1.0.0 | 2026-03-13 | 项目初始化 + 基础功能 |