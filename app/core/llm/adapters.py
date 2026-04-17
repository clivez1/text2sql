from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI

from app.config.settings import LLMProviderConfig
from app.core.llm.prompts import TEXT2SQL_SYSTEM_PROMPT, build_prompt_bundle


class LLMAdapter(Protocol):
    provider_name: str

    def generate_sql(self, question: str, schema_context: str | None = None) -> str: ...

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
            api_key=self.config.api_key, base_url=self.config.base_url or None
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
        )
        return response.choices[0].message.content or ""
