from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Protocol
from urllib import error, request

from openai import OpenAI

from app.config.settings import LLMProviderConfig
from app.core.llm.prompts import TEXT2SQL_SYSTEM_PROMPT, build_prompt_bundle


class LLMAdapter(Protocol):
    provider_name: str

    def generate_sql(self, question: str, schema_context: str | None = None) -> str: ...

    def chat(self, prompt: str) -> str: ...

    def connectivity_check(self) -> str: ...


def _strip_markdown_code_fences(text: str) -> str:
    """Strip markdown code fences from LLM output.

    LLMs sometimes wrap SQL in ```sql or ``` code blocks.
    This helper removes those fences while preserving the content.
    """
    text = text.strip()
    if not text.startswith("```"):
        return text

    lines = text.split("\n")
    # Remove the opening fence line (e.g., ```sql or ```)
    content_lines = lines[1:]

    # Check if the last line is a closing fence
    if content_lines and content_lines[-1].strip() == "```":
        content_lines = content_lines[:-1]

    return "\n".join(content_lines).strip()


@dataclass(frozen=True)
class OpenAICompatibleAdapter:
    config: LLMProviderConfig

    @property
    def provider_name(self) -> str:
        return self.config.provider

    def _build_client(self) -> OpenAI:
        if not self.config.api_key:
            raise RuntimeError(f"{self.provider_name} API key missing")
        return OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url or None,
            timeout=self.config.timeout_seconds,
        )

    def generate_sql(self, question: str, schema_context: str | None = None) -> str:
        """Generate SQL from a natural language question using OpenAI chat completion.

        Args:
            question: The natural language question to convert to SQL.
            schema_context: Optional pre-retrieved schema context. If not provided,
                           it will be retrieved based on the question.

        Returns:
            The generated SQL query string, stripped of any markdown formatting.
        """
        client = self._build_client()
        if schema_context is not None:
            context = schema_context
        else:
            from app.core.retrieval.schema_loader import retrieve_schema_context

            context = retrieve_schema_context(question)
        prompt = build_prompt_bundle(question, context)

        response = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
            temperature=0.1,
            max_tokens=self.config.max_tokens,
        )

        raw_output = response.choices[0].message.content or ""
        return _strip_markdown_code_fences(raw_output)

    def connectivity_check(self) -> str:
        client = self._build_client()
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": TEXT2SQL_SYSTEM_PROMPT},
                {"role": "user", "content": "Reply with OK"},
            ],
            temperature=0,
            max_tokens=min(self.config.max_tokens, 32),
        )
        return response.choices[0].message.content or ""

    def chat(self, prompt: str) -> str:
        """通用聊天接口，用于自然语言摘要等场景"""
        client = self._build_client()
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": "你是一个数据分析助手。请用简洁的中文回答问题。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content or ""


@dataclass(frozen=True)
class LocalGatewayAdapter(OpenAICompatibleAdapter):
    """Local model gateways usually expose an OpenAI-compatible HTTP interface."""


@dataclass(frozen=True)
class AnthropicMessagesAdapter:
    config: LLMProviderConfig

    @property
    def provider_name(self) -> str:
        return self.config.provider

    def _build_messages_url(self) -> str:
        base_url = (self.config.base_url or "https://api.anthropic.com").rstrip("/")
        if base_url.endswith("/v1/messages"):
            return base_url
        if base_url.endswith("/v1"):
            return f"{base_url}/messages"
        return f"{base_url}/v1/messages"

    def _post_messages(self, *, system: str, user_prompt: str, temperature: float, max_tokens: int) -> str:
        if not self.config.api_key:
            raise RuntimeError(f"{self.provider_name} API key missing")

        payload = {
            "model": self.config.model,
            "system": system,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        req = request.Request(
            self._build_messages_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Anthropic request failed: {exc.code} {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Anthropic request failed: {exc.reason}") from exc

        parsed = json.loads(body)
        chunks = [
            item.get("text", "")
            for item in parsed.get("content", [])
            if item.get("type") == "text"
        ]
        return "\n".join(chunk for chunk in chunks if chunk).strip()

    def generate_sql(self, question: str, schema_context: str | None = None) -> str:
        if schema_context is not None:
            context = schema_context
        else:
            from app.core.retrieval.schema_loader import retrieve_schema_context

            context = retrieve_schema_context(question)
        prompt = build_prompt_bundle(question, context)
        raw_output = self._post_messages(
            system=prompt.system_prompt,
            user_prompt=prompt.user_prompt,
            temperature=0.1,
            max_tokens=self.config.max_tokens,
        )
        return _strip_markdown_code_fences(raw_output)

    def connectivity_check(self) -> str:
        return self._post_messages(
            system=TEXT2SQL_SYSTEM_PROMPT,
            user_prompt="Reply with OK",
            temperature=0.0,
            max_tokens=min(self.config.max_tokens, 32),
        )

    def chat(self, prompt: str) -> str:
        return self._post_messages(
            system="你是一个数据分析助手。请用简洁的中文回答问题。",
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=self.config.max_tokens,
        )


def create_llm_adapter(config: LLMProviderConfig) -> LLMAdapter:
    """Create a protocol-specific adapter from provider configuration."""
    if config.protocol == "anthropic_messages":
        return AnthropicMessagesAdapter(config=config)
    if config.protocol == "local_gateway":
        return LocalGatewayAdapter(config=config)
    return OpenAICompatibleAdapter(config=config)
