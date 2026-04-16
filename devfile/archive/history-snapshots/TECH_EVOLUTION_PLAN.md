# 技术演进方案 - Text2SQL Agent

> 从 Demo 到生产级系统的渐进式增强路线图

**版本**: v1.0  
**日期**: 2026-03-27  
**状态**: 待实施

---

## 1. 现状评估

### 1.1 当前架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI (单进程)                    │
├─────────────────────────────────────────────────────────────┤
│  FastAPI REST API                                          │
│  ├── POST /ask - 自然语言查询                               │
│  ├── GET /health - 健康检查                                 │
│  └── GET /schemas - Schema 获取                            │
├─────────────────────────────────────────────────────────────┤
│  核心模块                                                    │
│  ├── orchestrator/pipeline.py - 流程编排                    │
│  ├── llm/ - Vanna AI 适配                                   │
│  ├── sql/ - SQL 生成/执行/安全                              │
│  ├── retrieval/ - ChromaDB Schema 检索                       │
│  └── chart/ - 图表推荐                                      │
├─────────────────────────────────────────────────────────────┤
│  LLM 调用 (Vanna/OpenAI/百炼)                              │
│  └── 无重试、无降级、无缓存                                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈清单

| 组件 | 当前技术 | 版本 |
|------|----------|------|
| 语言 | Python | 3.11+ |
| Web框架 | FastAPI + Streamlit | 0.115+ / 1.32+ |
| LLM框架 | Vanna AI | 0.7+ |
| 向量库 | ChromaDB | 1.0+ |
| 数据库 | SQLite/MySQL/PostgreSQL | - |
| ORM | SQLAlchemy | 2.0+ |

### 1.3 技术债清单

| 编号 | 问题 | 影响 | 严重程度 | 来源 |
|------|------|------|----------|------|
| TD-01 | 测试导入错误 | 无法运行测试套件 | 🔴 高 | `ModuleNotFoundError: No module named 'app'` |
| TD-02 | 无统一错误处理 | 异常直接暴露，可能泄露信息 | 🔴 高 | API 返回非标准格式 |
| TD-03 | LLM 调用无重试 | 网络抖动导致服务不可用 | 🔴 高 | Vanna/OpenAI 调用可能失败 |
| TD-04 | 无输入验证 | 脏数据可能导致崩溃 | 🔴 高 | AskRequest 字段未严格校验 |
| TD-05 | 无请求限流 | 资源耗尽风险 | 🟡 中 | API 无保护 |
| TD-06 | 无结构化日志 | 排障困难 | 🟡 中 | 使用 print/基础 logging |
| TD-07 | 无 CI/CD | 部署质量依赖人工 | 🟢 低 | 无 .github 文件夹 |
| TD-08 | 测试无覆盖率统计 | 质量不可见 | 🟢 低 | 无 pytest-cov |
| TD-09 | 配置分散 | 环境切换困难 | 🟢 低 | 部分配置硬编码 |

### 1.4 代码质量现状

| 指标 | Text2SQL | Data Viz (对标) |
|------|----------|-----------------|
| Python 文件数 | 55 | 30+ |
| 测试文件数 | 5 | 10+ |
| 测试用例数 | 104 (有错误) | 180 passed |
| 测试覆盖率 | 未统计 | 已统计 |
| 错误处理 | 散落 | 统一 AppError |
| 输入验证 | 基础 | Pydantic 全覆盖 |
| LLM 弹性 | 无 | 重试+降级+超时 |

---

## 2. 目标架构

### 2.1 生产级架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        负载均衡 / 网关                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │ Streamlit   │    │ FastAPI     │    │ Prometheus  │            │
│  │ Web UI      │    │ REST API    │    │ Metrics     │            │
│  └──────┬──────┘    └──────┬──────┘    └─────────────┘            │
│         │                  │                                       │
├─────────┼──────────────────┼───────────────────────────────────────┤
│         ▼                  ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    中间件层                                   │  │
│  │  RateLimiter │ RequestLogger │ ErrorHandler │ Validator    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│         │                                                          │
├─────────┼──────────────────────────────────────────────────────────┤
│         ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    业务逻辑层                                 │  │
│  │  Orchestrator │ LLMAdapter │ SQLExecutor │ ChartRecommender│  │
│  └─────────────────────────────────────────────────────────────┘  │
│         │                                                          │
├─────────┼──────────────────────────────────────────────────────────┤
│         ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    基础设施层                                 │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │  │
│  │  │ LLM     │ │ ChromaDB│ │ SQL DB  │ │ Cache   │           │  │
│  │  │ Client  │ │ (向量)  │ │ (多类型)│ │ (可选)  │           │  │
│  │  │(重试/限 │ │         │ │         │ │         │           │  │
│  │  │ 流/降级)│ │         │ │         │ │         │           │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 与 Data Viz 对标

| 维度 | Data Viz (已实现) | Text2SQL (目标) |
|------|------------------|-----------------|
| 错误处理 | AppError + 标准响应 | AppError + 标准响应 |
| 输入验证 | Pydantic 全覆盖 | Pydantic 全覆盖 |
| LLM 弹性 | 重试+降级+超时 | 重试+降级+超时 |
| 请求限流 | 60 req/min | 60 req/min |
| 结构化日志 | JSON + request_id | JSON + request_id |
| CI/CD | GitHub Actions | GitHub Actions |
| 测试覆盖率 | pytest-cov ≥ 80% | pytest-cov ≥ 80% |

---

## 3. 演进路径

### 3.1 Phase 0: 修复基础设施（预计 0.5 天）

**目标**: 解决测试导入错误，恢复测试能力

| 任务 | 描述 | 验收标准 |
|------|------|----------|
| E-0.1 修复测试导入 | 解决 `ModuleNotFoundError: No module named 'app'` | `pytest tests/` 正常运行 |
| E-0.2 验证测试通过 | 运行全部测试 | 104 tests passed |

**交付物**:
- [ ] `pytest tests/ -v` 全部通过
- [ ] 记录当前测试覆盖率

---

### 3.2 Phase 1: 基础加固（预计 3 天）

**目标**: 解决高风险技术债，提升稳定性

| 增强项 | 描述 | 工作量 | 验收标准 |
|--------|------|--------|----------|
| E-1.1 统一错误处理 | 全局异常捕获 + 标准错误响应 | 0.5天 | 所有异常返回标准格式，无堆栈暴露 |
| E-1.2 输入验证 | Pydantic 模型校验所有 API 输入 | 0.5天 | 无效输入被拒绝并返回明确错误 |
| E-1.3 LLM 弹性调用 | 重试机制 + 超时控制 + 降级策略 | 1天 | 网络抖动自动恢复，LLM 不可用时降级 |
| E-1.4 结构化日志 | JSON 格式 + 请求 ID | 0.5天 | 所有日志可解析，支持 ELK |
| E-1.5 配置统一 | 统一使用 settings.py + .env | 0.5天 | 配置完全从环境变量读取 |

**交付物**:
- [ ] `app/core/errors.py` - 统一错误处理
- [ ] `app/core/validators.py` - 输入验证器
- [ ] `app/core/llm/resilient_client.py` - 弹性 LLM 客户端
- [ ] `app/core/logging.py` - 结构化日志
- [ ] `app/config/settings.py` - 配置管理增强

---

### 3.3 Phase 2: 生产就绪（预计 2 天）

**目标**: 提升服务可靠性和可运维性

| 增强项 | 描述 | 工作量 | 验收标准 |
|--------|------|--------|----------|
| E-2.1 请求限流 | 自定义内存限流（~30行代码） | 0.5天 | 单 IP 不超过 60 req/min |
| E-2.2 CI/CD 流水线 | GitHub Actions 自动测试 + 构建 | 0.5天 | PR 自动测试，main 自动构建 |
| E-2.3 测试覆盖率 | 补充单元测试 + 集成测试 | 1天 | 覆盖率 ≥ 80% |

**交付物**:
- [ ] `app/middleware/rate_limiter.py` - 限流中间件
- [ ] `.github/workflows/` - CI/CD 配置
- [ ] 测试用例补充

---

### 3.4 Phase 3: 企业级增强（可选，预计 5 天）

**目标**: 支持多租户、可观测性、高可用

| 增强项 | 描述 | 工作量 | 验收标准 |
|--------|------|--------|----------|
| E-3.1 用户认证 | JWT 认证 + API Key | 1.5天 | 支持用户/API Key 认证 |
| E-3.2 权限控制 | 表级权限 + SQL 审计 | 1.5天 | 可控制用户可访问的表 |
| E-3.3 性能指标 | Prometheus 指标暴露 | 1天 | Grafana 可监控 |
| E-3.4 链路追踪 | OpenTelemetry 集成 | 1天 | Jaeger 可追踪请求 |

---

## 4. 增强项详细规格

### E-1.1 统一错误处理

**问题**: 当前异常直接暴露给用户，可能泄露敏感信息

**方案**: 复用 Data Viz Agent 的 `errors.py` 模式

```python
# app/core/errors.py

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

class ErrorCode(Enum):
    # 业务错误 (1xxx)
    INVALID_QUESTION = 1001
    SQL_GENERATION_ERROR = 1002
    SQL_EXECUTION_ERROR = 1003
    LLM_ERROR = 1004
    SCHEMA_NOT_FOUND = 1005
    
    # 安全错误 (2xxx)
    SQL_INJECTION_DETECTED = 2001
    TABLE_NOT_ALLOWED = 2002
    READONLY_VIOLATION = 2003
    
    # 系统错误 (3xxx)
    INTERNAL_ERROR = 3001
    SERVICE_UNAVAILABLE = 3002
    RATE_LIMITED = 3003

@dataclass
class AppError(Exception):
    code: ErrorCode
    message: str
    detail: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    def to_response(self) -> Dict[str, Any]:
        return {
            "success": False,
            "error": {
                "code": self.code.value,
                "message": self.message,
                "detail": self.detail if self.code in [
                    ErrorCode.INVALID_QUESTION,
                    ErrorCode.SQL_GENERATION_ERROR,
                ] else None,
            }
        }
```

**验收标准**:
- [ ] 所有自定义异常继承 `AppError`
- [ ] 500 错误不暴露堆栈信息
- [ ] 错误响应格式统一

---

### E-1.3 LLM 弹性调用

**问题**: Vanna/OpenAI 调用无重试，网络抖动导致服务不可用

**方案**:

```python
# app/core/llm/resilient_client.py

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from typing import Optional
import asyncio
from dataclasses import dataclass

@dataclass
class LLMConfig:
    max_retries: int = 3
    timeout: float = 30.0
    backoff_base: float = 1.0
    fallback_enabled: bool = True

class ResilientLLMClient:
    """弹性 LLM 客户端 - 封装 Vanna 调用"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.vanna_client = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    )
    async def generate_sql(
        self,
        question: str,
        **kwargs
    ) -> str:
        """带重试的 SQL 生成"""
        try:
            return await asyncio.wait_for(
                self._call_vanna(question, **kwargs),
                timeout=self.config.timeout,
            )
        except Exception as e:
            if self.config.fallback_enabled:
                return await self._call_fallback(question, **kwargs)
            raise AppError(
                code=ErrorCode.LLM_ERROR,
                message="SQL 生成失败，请稍后重试",
                detail=str(e),
            )
```

**验收标准**:
- [ ] 网络抖动自动重试
- [ ] 超时后降级处理
- [ ] LLM 不可用时返回友好错误

---

## 5. 决策记录

### DR-01: 为什么先修复测试再增强？

**决策**: Phase 0 优先修复测试导入错误。

**理由**:
1. **回归保护**: 测试是后续重构的安全网
2. **快速验证**: 修复后可立即验证当前功能状态
3. **增量信心**: 每次增强后有测试验证，避免引入新问题

### DR-02: 为什么选择从 Data Viz 复用代码模式？

**决策**: 直接复用 Data Viz Agent 已验证的代码模式。

**理由**:
1. **降低风险**: 已验证的代码模式，减少试错
2. **保持一致**: 两项目架构风格统一
3. **加速开发**: 无需重新设计，直接复制适配

### DR-03: Phase 3 为什么是可选的？

**决策**: 用户认证和权限控制作为可选增强项。

**理由**:
1. **场景依赖**: 单用户/Demo 场景不需要认证
2. **复杂度**: 认证引入用户管理、权限等复杂度
3. **渐进增强**: Phase 1-2 完成后已具备生产基础

---

## 6. 验收标准

### 6.1 Phase 0 完成标准

- [ ] `pytest tests/ -v` 全部通过
- [ ] 记录当前测试覆盖率基线

### 6.2 Phase 1 完成标准

- [ ] 所有异常返回标准 JSON 格式
- [ ] 无堆栈信息暴露给用户
- [ ] 所有 API 输入使用 Pydantic 校验
- [ ] LLM 调用失败时自动重试（最多 3 次）
- [ ] 所有日志为 JSON 格式，包含 request_id

### 6.3 Phase 2 完成标准

- [ ] 单 IP 请求频率限制生效
- [ ] PR 合并自动运行测试
- [ ] 测试覆盖率 ≥ 80%

---

## 7. 新增依赖

| 依赖 | 用途 | 大小 | 阶段 |
|------|------|------|------|
| python-json-logger | 结构化日志 | ~10KB | Phase 1 |
| tenacity | 重试机制 | ~20KB | Phase 1 |
| pytest-cov | 测试覆盖率 | ~30KB | Phase 2 |

**零新增依赖**:
- 请求限流：自定义实现（~30行）
- 配置管理：继续用 python-dotenv（已有）

---

## 8. 实施计划

| 阶段 | 任务 | 预计工时 | 状态 |
|------|------|----------|------|
| Phase 0 | 修复测试导入 | 0.5 天 | ⏳ 待开始 |
| Phase 1 | 基础加固 | 3 天 | ⏳ 待开始 |
| Phase 2 | 生产就绪 | 2 天 | ⏳ 待开始 |
| Phase 3 | 企业级增强 | 5 天 | 🔘 可选 |

**总计**: Phase 0-2 约 5.5 天

---

## 更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-27 | 初始版本，基于 Data Viz 演进方案 |