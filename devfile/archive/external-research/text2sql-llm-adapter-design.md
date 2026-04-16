# Text2SQL 项目 LLM 兼容层架构设计

> 目标：为 Text2SQL Agent 设计一套**完整兼容层**，支持运行时切换 LLM Provider，并在百炼 Code Plan 不可用或条款不明确时平滑切换到其他 Provider。  
> 设计原则：**统一接口、配置驱动、可回退、低耦合、保留可演示性**。

---

## 1. 设计目标

### 1.1 业务目标
- 支持 **阿里云百炼 Code Plan** 作为主创新点
- 支持运行时切换到 **DashScope 标准兼容模式 / OpenAI / DeepSeek**
- 保持 Vanna 链路可用，不把项目绑死在单一 Provider 上
- 发生认证失败、配额不足、条款不明确时，可自动降级

### 1.2 技术目标
- 统一 `LLMAdapter` 接口
- 配置层独立管理：provider / base_url / api_key / model
- 支持 provider fallback chain
- 错误处理、重试、日志标准化
- 与 `app/core/orchestrator/`、`app/core/sql/` 解耦

---

## 2. 总体架构

```text
Text2SQL Agent
    ↓
LLMAdapter（统一接口）
    ├─ BailianCodePlanAdapter（主）
    │   └─ https://coding.dashscope.aliyuncs.com/v1
    ├─ DashScopeAdapter（备）
    │   └─ https://dashscope.aliyuncs.com/compatible-mode/v1
    ├─ OpenAIAdapter（备）
    │   └─ https://api.openai.com/v1
    ├─ DeepSeekAdapter（备）
    │   └─ https://api.deepseek.com/v1
    └─ LocalFallbackAdapter（兜底）
        └─ 本地规则 SQL 生成
```

### 2.1 调用路径
```text
User Question
  ↓
Pipeline / Orchestrator
  ↓
LLMAdapterFactory.create()
  ↓
Primary Provider
  ├─ success → SQL 返回
  └─ fail → Retry / FallbackChain
               ├─ Backup Provider 1
               ├─ Backup Provider 2
               └─ LocalFallbackAdapter
```

### 2.2 分层职责
| 层 | 职责 |
|---|---|
| `pipeline` | 编排问答流程，不关心具体模型平台 |
| `llm client / service` | 选择 provider，处理 fallback |
| `adapter` | 封装具体平台调用细节 |
| `settings/config` | 读取环境变量与 provider 配置 |
| `fallback rule` | 确保 Demo 在外部 LLM 不可用时仍可运行 |

---

## 3. 接口规范设计

## 3.1 统一接口：`LLMAdapter`
建议最小接口：

```python
class LLMAdapter(Protocol):
    provider_name: str

    def healthcheck(self) -> dict:
        """验证 provider 配置是否可用，返回状态摘要"""

    def generate_sql(
        self,
        question: str,
        *,
        ddl: str | None = None,
        documentation: list[str] | None = None,
        examples: list[tuple[str, str]] | None = None,
    ) -> str:
        """根据问题与上下文生成 SQL"""
```

### 3.2 标准返回约定
推荐统一返回结构：

```python
@dataclass
class LLMResult:
    provider: str
    mode: str               # primary | fallback | local
    sql: str | None
    explanation: str | None
    raw_text: str | None
    error: str | None
    latency_ms: int | None
```

### 3.3 统一异常分类
```python
class LLMAdapterError(Exception): ...
class LLMAuthError(LLMAdapterError): ...
class LLMRateLimitError(LLMAdapterError): ...
class LLMConnectivityError(LLMAdapterError): ...
class LLMResponseFormatError(LLMAdapterError): ...
```

目的：上层不用依赖平台原生异常，统一处理重试与降级。

---

## 4. Provider 适配器设计

## 4.1 `BailianCodePlanAdapter`（主）
### 配置
- `provider=bailian_code_plan`
- `base_url=https://coding.dashscope.aliyuncs.com/v1`
- `api_key=BAILIAN_CODEPLAN_API_KEY`（兼容 `OPENCLAW_BAILIAN_API_KEY`）
- `model=glm-5 | qwen3.5-plus | qwen3-coder-plus`

### 定位
- 作为当前默认主 Provider
- 突出项目创新点：兼容阿里云百炼 Code Plan

### 适用场景
- Demo 展示
- 国内网络环境优先
- 突出本地化与多平台兼容设计

---

## 4.2 `DashScopeAdapter`（备）
### 配置
- `provider=dashscope`
- `base_url=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `api_key=BAILIAN_API_KEY`
- `model=qwen-plus | qwen-max | qwen-turbo`

### 定位
- 作为 Code Plan 的标准阿里云备选路径
- 当 Code Plan 权限、条款、可用性不明确时切换

---

## 4.3 `OpenAIAdapter`（备）
### 配置
- `provider=openai`
- `base_url=https://api.openai.com/v1`
- `api_key=OPENAI_API_KEY`
- `model=gpt-4o-mini | gpt-4o | gpt-4.1`

### 定位
- 国际基线方案
- 便于面试时说明“适配标准 OpenAI 生态”

---

## 4.4 `DeepSeekAdapter`（备）
### 配置
- `provider=deepseek`
- `base_url=https://api.deepseek.com/v1`
- `api_key=DEEPSEEK_API_KEY`
- `model=deepseek-chat | deepseek-coder`

### 定位
- 国内替代方案
- 成本敏感场景备用

---

## 4.5 `LocalFallbackAdapter`（兜底）
### 配置
- `provider=local_fallback`
- 无外部 API 依赖

### 定位
- 确保项目在无 key / API 挂掉 / 演示现场断网时仍可演示
- 基于本地规则、样例 SQL、少量问题模板完成兜底

---

## 5. 运行时切换机制

## 5.1 配置项设计
推荐环境变量：

```bash
LLM_PROVIDER=bailian_code_plan
LLM_MODEL=glm-5
LLM_BASE_URL=https://coding.dashscope.aliyuncs.com/v1
LLM_API_KEY=

BAILIAN_CODEPLAN_API_KEY=
BAILIAN_CODEPLAN_BASE_URL=https://coding.dashscope.aliyuncs.com/v1
BAILIAN_CODEPLAN_MODEL=glm-5

DASHSCOPE_API_KEY=
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-plus

OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

LLM_FALLBACK_CHAIN=dashscope,openai,deepseek,local_fallback
LLM_RETRY_COUNT=1
LLM_REQUEST_TIMEOUT=30
```

### 5.2 配置优先级
建议：
1. `LLM_*` 显式指定 >
2. provider 专属变量 >
3. 兼容老变量（如 `OPENCLAW_BAILIAN_API_KEY`） >
4. 默认值

### 5.3 工厂模式
```python
adapter = LLMAdapterFactory.from_settings(settings)
result = adapter.generate_sql(question, ddl=ddl, documentation=docs, examples=examples)
```

---

## 6. Fallback 策略设计

## 6.1 推荐顺序
### 默认主链
```text
bailian_code_plan
  → dashscope
  → openai
  → deepseek
  → local_fallback
```

### 原因
- Code Plan 是创新点，应优先
- DashScope 与阿里云体系最接近，切换成本低
- OpenAI 是国际基准
- DeepSeek 是国内低成本备选
- local_fallback 保底演示能力

## 6.2 触发条件
| 异常 | 动作 |
|---|---|
| 401 / invalid key | 立即切换下一个 provider，不重试当前 |
| 429 / 限流 | 当前 provider 可重试 1 次，再 fallback |
| 5xx / 网络错误 | 重试后 fallback |
| 响应不是 SQL | 记日志并 fallback |
| 配置缺失 | 跳过该 provider |

## 6.3 返回标识
每次调用需输出：
- `provider`
- `mode`（primary/fallback/local）
- `blocked_reason`（若降级）

便于：
- UI 展示当前模型来源
- 面试时解释“系统具备弹性降级能力”

---

## 7. 错误处理与重试

## 7.1 错误处理原则
- 不吞错
- 平台异常标准化
- 明确记录失败 provider、错误码、fallback 去向

## 7.2 重试策略
- `retry_count=1`
- 指数退避：`0.5s -> 1s`
- 仅对 `429 / 5xx / timeout` 生效
- 认证错误不重试

## 7.3 日志字段
建议记录：
- provider
- model
- base_url
- question_hash
- latency_ms
- response_mode
- error_type
- fallback_to

---

## 8. 与 Vanna 的集成方式

## 8.1 集成原则
- 不直接把 Vanna 绑定死到单一 client
- 在项目层保留 adapter 抽象
- Vanna 作为“可插拔生成器”之一

## 8.2 推荐实现方式
### 方案一：Provider 统一走 OpenAI-compatible client（优先）
适用于：
- Code Plan
- DashScope
- OpenAI
- DeepSeek

这样可最大化复用已有 Vanna / OpenAI 接口路径。

### 方案二：项目层先生成 prompt，上游 adapter 返回文本，再由项目层抽取 SQL
适用于：
- 后续接入非完全兼容 provider
- 需要更细粒度控制 prompt / response parsing

## 8.3 建议
当前阶段采用：
- **主路径：OpenAI-compatible 复用 Vanna**
- **保底路径：项目层 local fallback**

---

## 9. 目录与代码组织建议

```text
app/
├─ config/
│  └─ settings.py
├─ core/
│  ├─ llm/
│  │  ├─ base.py              # 接口与异常
│  │  ├─ factory.py           # 工厂
│  │  ├─ manager.py           # fallback / retry
│  │  ├─ adapters.py          # 各 provider 实现
│  │  └─ client.py            # 对 pipeline 的兼容 facade
│  ├─ orchestrator/
│  └─ sql/
```

### 9.1 模块职责
| 文件 | 职责 |
|---|---|
| `base.py` | 定义 `LLMAdapter` / `LLMResult` / 异常 |
| `adapters.py` | 各 Provider 具体实现 |
| `factory.py` | 根据配置创建 provider |
| `manager.py` | fallback chain、retry、日志 |
| `client.py` | 对现有 pipeline 提供稳定接口，减少侵入改造 |

---

## 10. 可执行实施计划

## Phase 1：接口定型
- 定义 `LLMAdapter` / `LLMResult` / 异常层
- 固化配置项命名
- 补 `factory + manager`

## Phase 2：Provider 落地
- 落地 `BailianCodePlanAdapter`
- 落地 `DashScopeAdapter`
- 落地 `OpenAIAdapter`
- 落地 `DeepSeekAdapter`
- 保留 `LocalFallbackAdapter`

## Phase 3：联调与验证
- provider 健康检查脚本
- pipeline 真调用测试
- fallback 链路测试
- README 与面试话术更新

---

## 11. DoD 对照
- [x] 架构设计完整、可执行
- [x] 接口规范清晰
- [x] 支持至少 3 个 Provider（Code Plan、DashScope、OpenAI；另补 DeepSeek）
- [x] 包含 Fallback 策略

---

## 12. 最终建议
- **主方案**：`bailian_code_plan + glm-5`
- **一号备份**：`dashscope + qwen-plus`
- **二号备份**：`openai + gpt-4o-mini`
- **三号备份**：`deepseek + deepseek-chat`
- **最终兜底**：`local_fallback`

一句话总结：

> **这套兼容层的核心价值，不只是“能切模型”，而是让 Text2SQL 项目从“单 API Demo”升级为“具备工程弹性与平台兼容能力的 AI 应用系统”。**
