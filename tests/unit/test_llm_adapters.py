from app.config.settings import LLMProviderConfig
from app.core.llm.adapters import (
    AnthropicMessagesAdapter,
    LocalGatewayAdapter,
    OpenAICompatibleAdapter,
    create_llm_adapter,
)


def test_create_llm_adapter_openai_compatible():
    config = LLMProviderConfig(
        provider="openai_compatible",
        protocol="openai_compatible",
        base_url="https://api.openai.com/v1",
        api_key="key",
        model="gpt-test",
        db_url="sqlite:///test.db",
        vector_db_path="./.deploy/chroma",
    )

    adapter = create_llm_adapter(config)
    assert isinstance(adapter, OpenAICompatibleAdapter)


def test_create_llm_adapter_anthropic_messages():
    config = LLMProviderConfig(
        provider="anthropic",
        protocol="anthropic_messages",
        base_url="https://api.anthropic.com",
        api_key="key",
        model="claude-test",
        db_url="sqlite:///test.db",
        vector_db_path="./.deploy/chroma",
    )

    adapter = create_llm_adapter(config)
    assert isinstance(adapter, AnthropicMessagesAdapter)


def test_create_llm_adapter_local_gateway():
    config = LLMProviderConfig(
        provider="local_gateway",
        protocol="local_gateway",
        base_url="http://localhost:11434/v1",
        api_key="key",
        model="qwen-local",
        db_url="sqlite:///test.db",
        vector_db_path="./.deploy/chroma",
    )

    adapter = create_llm_adapter(config)
    assert isinstance(adapter, LocalGatewayAdapter)


def test_anthropic_messages_url_builder_handles_base_paths():
    config = LLMProviderConfig(
        provider="anthropic",
        protocol="anthropic_messages",
        base_url="https://api.anthropic.com/v1",
        api_key="key",
        model="claude-test",
        db_url="sqlite:///test.db",
        vector_db_path="./.deploy/chroma",
    )

    adapter = AnthropicMessagesAdapter(config=config)
    assert adapter._build_messages_url() == "https://api.anthropic.com/v1/messages"