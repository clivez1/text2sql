# Vanna自定义LLM适配调研报告

**日期**: 2026-03-14
**版本**: Vanna v2.0.2

---

## 1. Vanna LLM扩展机制

### 1.1 架构概述

Vanna v2 采用**模块化架构**，LLM服务层与业务逻辑完全解耦：

```
vanna/
├── core/
│   └── llm/
│       ├── base.py      # LlmService 抽象基类
│       └── models.py    # LlmRequest, LlmResponse, LlmStreamChunk
├── integrations/
│   ├── openai/          # OpenAI 实现
│   ├── anthropic/       # Anthropic 实现
│   ├── ollama/          # Ollama 本地模型
│   └── ...
└── legacy/              # 向后兼容的旧架构
```

### 1.2 LlmService 抽象基类

```python
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, List

class LlmService(ABC):
    """LLM服务的抽象基类 - 所有LLM适配器必须继承此类"""

    @abstractmethod
    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """发送非流式请求到LLM"""
        pass

    @abstractmethod
    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        """发送流式请求到LLM"""
        pass

    @abstractmethod
    async def validate_tools(self, tools: List[Any]) -> List[str]:
        """验证工具schema，返回错误列表"""
        pass
```

### 1.3 核心数据模型

```python
class LlmMessage(BaseModel):
    role: str                          # system/user/assistant/tool
    content: str                       # 消息内容
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None

class LlmRequest(BaseModel):
    messages: List[LlmMessage]         # 消息历史
    tools: Optional[List[ToolSchema]]  # 可用工具
    user: User                         # 用户信息
    stream: bool = False               # 是否流式
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None

class LlmResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
```

### 1.4 已支持的LLM后端

| 后端 | 位置 | 特点 |
|------|------|------|
| OpenAI | `integrations/openai/` | 支持Chat Completions API，Tool Calling |
| Anthropic | `integrations/anthropic/` | Claude系列，Messages API |
| Ollama | `integrations/ollama/` | 本地部署，支持开源模型 |
| Azure OpenAI | `integrations/azureopenai/` | Azure部署的OpenAI |
| Google | `integrations/google/` | Gemini系列 |
| Mistral | `legacy/mistral/` | Mistral系列 |

---

## 2. 适配方案设计

### 2.1 阿里云百炼Code Plan适配

百炼提供OpenAI-compatible接口，可直接复用OpenAI实现：

```python
from vanna.integrations.openai import OpenAILlmService

class BailianLlmService(OpenAILlmService):
    """阿里云百炼 LLM服务适配器
    
    百炼提供OpenAI兼容接口，只需修改base_url即可
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "qwen-plus",  # 或 qwen-max, qwen-turbo
        **kwargs
    ):
        super().__init__(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=model,
            **kwargs
        )


# 使用示例
llm_service = BailianLlmService(
    api_key="sk-xxx",
    model="qwen-plus"
)
```

### 2.2 自定义LLM适配器模板

对于不支持OpenAI兼容接口的平台，需完整实现LlmService：

```python
from vanna.core.llm import LlmService, LlmRequest, LlmResponse, LlmStreamChunk
from vanna.core.tool import ToolCall, ToolSchema
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx

class CustomLlmService(LlmService):
    """自定义LLM服务适配器模板"""
    
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        **extra_kwargs
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.extra_kwargs = extra_kwargs
        self._client = httpx.AsyncClient()
    
    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """发送非流式请求"""
        payload = self._build_payload(request)
        
        response = await self._client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        response.raise_for_status()
        data = response.json()
        
        return self._parse_response(data)
    
    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        """发送流式请求"""
        payload = self._build_payload(request)
        payload["stream"] = True
        
        async with self._client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk_data = line[6:]
                    if chunk_data == "[DONE]":
                        break
                    chunk = self._parse_stream_chunk(chunk_data)
                    if chunk:
                        yield chunk
    
    async def validate_tools(self, tools: List[ToolSchema]) -> List[str]:
        """验证工具schema"""
        errors = []
        for tool in tools:
            if not tool.name or len(tool.name) > 64:
                errors.append(f"Invalid tool name: {tool.name!r}")
        return errors
    
    def _build_payload(self, request: LlmRequest) -> Dict[str, Any]:
        """构建API请求payload"""
        messages = []
        
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": request.temperature,
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters
                    }
                }
                for t in request.tools
            ]
        
        return payload
    
    def _parse_response(self, data: Dict) -> LlmResponse:
        """解析API响应"""
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        return LlmResponse(
            content=message.get("content"),
            tool_calls=self._extract_tool_calls(message),
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage")
        )
    
    def _parse_stream_chunk(self, chunk_data: str) -> Optional[LlmStreamChunk]:
        """解析流式chunk"""
        import json
        try:
            data = json.loads(chunk_data)
            delta = data.get("choices", [{}])[0].get("delta", {})
            return LlmStreamChunk(
                content=delta.get("content"),
                finish_reason=data.get("choices", [{}])[0].get("finish_reason")
            )
        except:
            return None
    
    def _extract_tool_calls(self, message: Dict) -> Optional[List[ToolCall]]:
        """提取工具调用"""
        import json
        tool_calls = []
        
        for tc in message.get("tool_calls", []):
            fn = tc.get("function", {})
            args_raw = fn.get("arguments", "{}")
            
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            except:
                args = {"_raw": args_raw}
            
            tool_calls.append(ToolCall(
                id=tc.get("id", "tool_call"),
                name=fn.get("name", "tool"),
                arguments=args
            ))
        
        return tool_calls if tool_calls else None
```

### 2.3 DeepSeek适配示例

```python
from vanna.integrations.openai import OpenAILlmService

class DeepSeekLlmService(OpenAILlmService):
    """DeepSeek LLM服务适配器"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",  # 或 deepseek-coder
        **kwargs
    ):
        super().__init__(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            model=model,
            **kwargs
        )
```

### 2.4 通义千问适配示例

```python
from vanna.integrations.openai import OpenAILlmService

class QianwenLlmService(OpenAILlmService):
    """通义千问 LLM服务适配器"""
    
    # 模型映射
    MODELS = {
        "qwen-turbo": "qwen-turbo",
        "qwen-plus": "qwen-plus",
        "qwen-max": "qwen-max",
        "qwen-long": "qwen-long",
    }
    
    def __init__(
        self,
        api_key: str,
        model: str = "qwen-plus",
        **kwargs
    ):
        super().__init__(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=self.MODELS.get(model, model),
            **kwargs
        )
```

---

## 3. 多LLM切换架构

### 3.1 工厂模式

```python
from enum import Enum
from vanna.core.llm import LlmService

class LLMProvider(Enum):
    OPENAI = "openai"
    BAILIAN = "bailian"
    DEEPSEEK = "deepseek"
    QIANWEN = "qianwen"
    OLLAMA = "ollama"

class LlmServiceFactory:
    """LLM服务工厂"""
    
    @staticmethod
    def create(
        provider: LLMProvider,
        config: Dict[str, Any]
    ) -> LlmService:
        if provider == LLMProvider.OPENAI:
            from vanna.integrations.openai import OpenAILlmService
            return OpenAILlmService(**config)
        
        elif provider == LLMProvider.BAILIAN:
            return BailianLlmService(**config)
        
        elif provider == LLMProvider.DEEPSEEK:
            return DeepSeekLlmService(**config)
        
        elif provider == LLMProvider.QIANWEN:
            return QianwenLlmService(**config)
        
        elif provider == LLMProvider.OLLAMA:
            from vanna.integrations.ollama import OllamaLlmService
            return OllamaLlmService(**config)
        
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

### 3.2 配置管理方案

```yaml
# config/llm.yaml
default_provider: bailian

providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4
    temperature: 0.7
    max_tokens: 4096
  
  bailian:
    api_key: ${BAILIAN_API_KEY}
    model: qwen-plus
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  
  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    model: deepseek-chat
    base_url: https://api.deepseek.com/v1
  
  ollama:
    model: llama3
    host: http://localhost:11434

fallback:
  enabled: true
  chain: [bailian, openai, ollama]
```

```python
# 配置加载器
import yaml
from pathlib import Path

class LlmConfig:
    """LLM配置管理"""
    
    def __init__(self, config_path: str = "config/llm.yaml"):
        self.config = self._load_config(config_path)
    
    def _load_config(self, path: str) -> Dict:
        config_path = Path(path)
        if not config_path.exists():
            return {"default_provider": "openai", "providers": {}}
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # 环境变量替换
        return self._resolve_env_vars(config)
    
    def _resolve_env_vars(self, config: Dict) -> Dict:
        import os
        import re
        
        def replace_env(value):
            if isinstance(value, str):
                pattern = r'\$\{(\w+)\}'
                return re.sub(pattern, lambda m: os.getenv(m.group(1), ''), value)
            elif isinstance(value, dict):
                return {k: replace_env(v) for k, v in value.items()}
            return value
        
        return replace_env(config)
    
    def get_provider_config(self, provider: str) -> Dict:
        return self.config.get("providers", {}).get(provider, {})
    
    def get_default_provider(self) -> str:
        return self.config.get("default_provider", "openai")
```

### 3.3 Fallback策略

```python
from vanna.core.llm import LlmService, LlmRequest, LlmResponse
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class FallbackLlmService(LlmService):
    """带Fallback的LLM服务"""
    
    def __init__(
        self,
        primary: LlmService,
        fallbacks: List[LlmService],
        retry_count: int = 1
    ):
        self.primary = primary
        self.fallbacks = fallbacks
        self.retry_count = retry_count
    
    async def send_request(self, request: LlmRequest) -> LlmResponse:
        errors = []
        
        # 尝试主服务
        for attempt in range(self.retry_count):
            try:
                return await self.primary.send_request(request)
            except Exception as e:
                logger.warning(f"Primary LLM failed (attempt {attempt + 1}): {e}")
                errors.append(str(e))
        
        # 尝试备用服务
        for i, fallback in enumerate(self.fallbacks):
            try:
                logger.info(f"Trying fallback LLM #{i + 1}")
                return await fallback.send_request(request)
            except Exception as e:
                logger.warning(f"Fallback LLM #{i + 1} failed: {e}")
                errors.append(str(e))
        
        raise RuntimeError(f"All LLM services failed: {'; '.join(errors)}")
    
    async def stream_request(self, request: LlmRequest):
        errors = []
        
        # 尝试主服务
        try:
            async for chunk in self.primary.stream_request(request):
                yield chunk
            return
        except Exception as e:
            logger.warning(f"Primary LLM streaming failed: {e}")
            errors.append(str(e))
        
        # 尝试备用服务
        for i, fallback in enumerate(self.fallbacks):
            try:
                logger.info(f"Trying fallback LLM #{i + 1} for streaming")
                async for chunk in fallback.stream_request(request):
                    yield chunk
                return
            except Exception as e:
                logger.warning(f"Fallback LLM #{i + 1} streaming failed: {e}")
                errors.append(str(e))
        
        raise RuntimeError(f"All LLM streaming services failed: {'; '.join(errors)}")
    
    async def validate_tools(self, tools) -> List[str]:
        return await self.primary.validate_tools(tools)
```

### 3.4 完整使用示例

```python
from vanna import Agent, AgentConfig, ToolRegistry
from vanna.core.user import User

# 1. 创建LLM服务
llm_service = LlmServiceFactory.create(
    provider=LLMProvider.BAILIAN,
    config={
        "api_key": "sk-xxx",
        "model": "qwen-plus"
    }
)

# 2. 或使用带Fallback的服务
primary = LlmServiceFactory.create(LLMProvider.BAILIAN, {...})
fallback1 = LlmServiceFactory.create(LLMProvider.DEEPSEEK, {...})
fallback2 = LlmServiceFactory.create(LLMProvider.OPENAI, {...})

llm_service = FallbackLlmService(
    primary=primary,
    fallbacks=[fallback1, fallback2]
)

# 3. 创建Agent
agent = Agent(
    llm_service=llm_service,
    tool_registry=ToolRegistry(),
    user_resolver=my_user_resolver,
    agent_memory=my_agent_memory,
    config=AgentConfig(
        temperature=0.7,
        max_tokens=4096,
        stream_responses=True
    )
)

# 4. 使用
async for component in agent.send_message(context, "查询销售额前10的客户"):
    print(component)
```

---

## 4. 风险评估

### 4.1 兼容性问题

| 风险 | 影响 | 缓解方案 |
|------|------|----------|
| **Tool Calling格式差异** | 不同LLM的工具调用格式可能不同 | OpenAI-compatible接口通常支持标准格式，需测试验证 |
| **上下文窗口限制** | 不同模型context length不同 | 配置max_tokens时需考虑模型限制 |
| **响应格式差异** | SQL提取可能失败 | 在extract_sql中增加多种格式匹配 |
| **流式响应实现差异** | 流式输出可能不稳定 | 提供非流式fallback |

### 4.2 百炼Code Plan特定风险

1. **工具调用支持**：需确认百炼是否完整支持OpenAI的Tool Calling格式
2. **流式响应**：需测试SSE格式是否完全兼容
3. **Token计数**：百炼的usage返回格式可能略有差异

### 4.3 推荐测试项

```python
# 测试脚本
import asyncio
from vanna.core.llm import LlmRequest, LlmMessage
from vanna.core.user import User

async def test_llm_service(service):
    """测试LLM服务基本功能"""
    
    # 1. 基础对话测试
    request = LlmRequest(
        messages=[LlmMessage(role="user", content="你好")],
        user=User(id="test", name="test")
    )
    response = await service.send_request(request)
    assert response.content, "基础对话失败"
    print("✅ 基础对话测试通过")
    
    # 2. 工具调用测试
    from vanna.core.tool import ToolSchema
    tools = [
        ToolSchema(
            name="get_weather",
            description="获取天气",
            parameters={"type": "object", "properties": {"city": {"type": "string"}}}
        )
    ]
    request = LlmRequest(
        messages=[LlmMessage(role="user", content="北京今天天气怎么样？")],
        tools=tools,
        user=User(id="test", name="test")
    )
    response = await service.send_request(request)
    assert response.tool_calls, "工具调用失败"
    print("✅ 工具调用测试通过")
    
    # 3. 流式响应测试
    request = LlmRequest(
        messages=[LlmMessage(role="user", content="讲个故事")],
        user=User(id="test", name="test"),
        stream=True
    )
    chunks = []
    async for chunk in service.stream_request(request):
        if chunk.content:
            chunks.append(chunk.content)
    assert chunks, "流式响应失败"
    print("✅ 流式响应测试通过")

# 运行测试
asyncio.run(test_llm_service(bailian_service))
```

---

## 5. 总结

### 5.1 最佳实践

1. **优先使用OpenAI-compatible接口**：百炼、DeepSeek等平台提供兼容接口，可直接复用`OpenAILlmService`
2. **实现Fallback机制**：多LLM冗余，提升系统可靠性
3. **配置外部化**：通过YAML管理多LLM配置，支持环境变量
4. **充分测试**：针对Tool Calling和流式响应进行专项测试

### 5.2 实施路径

```
Phase 1: 快速验证
├── 使用OpenAILlmService + base_url适配百炼
└── 验证基本对话和Tool Calling

Phase 2: 完善架构
├── 实现LlmServiceFactory
├── 添加FallbackLlmService
└── 配置外部化

Phase 3: 生产就绪
├── 添加监控和日志
├── 实现熔断和限流
└── 完善错误处理
```

### 5.3 参考资源

- Vanna GitHub: https://github.com/vanna-ai/vanna
- OpenAI API Reference: https://platform.openai.com/docs/api-reference
- 阿里云百炼文档: https://help.aliyun.com/document_detail/2712195.html
- DeepSeek API: https://platform.deepseek.com/api-docs