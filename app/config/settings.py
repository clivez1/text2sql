from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env first (contains placeholders for documentation)
load_dotenv()
# Then load .impKey (contains actual sensitive values, overrides .env)
load_dotenv(dotenv_path=".impKey", override=True)


def _normalize_protocol(value: str) -> str:
    """Normalize configured LLM protocol names."""
    lower = (value or "").strip().lower()
    if lower in {"anthropic", "anthropic_messages", "claude"}:
        return "anthropic_messages"
    if lower in {"local", "local_gateway", "local-openai", "local_openai"}:
        return "local_gateway"
    return "openai_compatible"


def _detect_protocol(base_url: str) -> str:
    """Infer API protocol from base_url when protocol is not configured."""
    if not base_url:
        return "openai_compatible"

    lower = base_url.lower()
    if "anthropic" in lower or "claude" in lower:
        return "anthropic_messages"
    if any(token in lower for token in ["localhost", "127.0.0.1", "host.docker.internal", "ollama", "vllm", "lmstudio"]):
        return "local_gateway"
    return "openai_compatible"


def _provider_name_from_protocol(protocol: str) -> str:
    """Return a stable provider name used in logs, health checks, and metrics."""
    if protocol == "anthropic_messages":
        return "anthropic"
    if protocol == "local_gateway":
        return "local_gateway"
    return "openai_compatible"


def _get_env_with_index(name: str, index: int, default: str = "") -> str:
    """Read indexed env var, falling back to unsuffixed name for index=1."""
    if index == 1:
        return os.getenv(f"{name}_1") or os.getenv(name, default)
    return os.getenv(f"{name}_{index}", default)


def _parse_int_env(name: str, index: int, default: int) -> int:
    raw = _get_env_with_index(name, index, str(default))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _parse_float_env(name: str, index: int, default: float) -> float:
    raw = _get_env_with_index(name, index, str(default))
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class LLMProviderConfig:
    provider: str
    protocol: str
    base_url: str
    api_key: str
    model: str
    db_url: str
    vector_db_path: str
    purpose: str = "general"
    timeout_seconds: float = 30.0
    max_tokens: int = 1024


def _parse_providers(db_url: str, vector_db_path: str) -> tuple[LLMProviderConfig, ...]:
    """Parse LLM providers from environment variables.

    Detection order:
    - Index 1: LLM_API_KEY_1 (preferred) or LLM_API_KEY (backward compatible)
    - Index 2+: LLM_API_KEY_2, LLM_API_KEY_3, ... until first gap
    """
    providers: list[LLMProviderConfig] = []

    # Index 1: prefer LLM_API_KEY_1, fall back to LLM_API_KEY (no suffix)
    api_key_1 = _get_env_with_index("LLM_API_KEY", 1)
    if api_key_1:
        base_url_1 = _get_env_with_index("LLM_BASE_URL", 1)
        model_1 = _get_env_with_index("LLM_MODEL", 1)
        protocol_1 = _normalize_protocol(
            _get_env_with_index("LLM_PROTOCOL", 1, _detect_protocol(base_url_1))
        )
        provider_1 = _provider_name_from_protocol(protocol_1)
        purpose_1 = _get_env_with_index("LLM_PURPOSE", 1, "general")
        timeout_1 = _parse_float_env("LLM_TIMEOUT", 1, 30.0)
        max_tokens_1 = _parse_int_env("LLM_MAX_TOKENS", 1, 1024)

        if not model_1:
            defaults = {
                "anthropic_messages": "claude-sonnet-4-20250514",
                "local_gateway": "local-model",
                "openai_compatible": "gpt-4o-mini",
            }
            model_1 = defaults.get(protocol_1, "gpt-4o-mini")

        providers.append(
            LLMProviderConfig(
                provider=provider_1,
                protocol=protocol_1,
                base_url=base_url_1,
                api_key=api_key_1,
                model=model_1,
                db_url=db_url,
                vector_db_path=vector_db_path,
                purpose=purpose_1,
                timeout_seconds=timeout_1,
                max_tokens=max_tokens_1,
            )
        )

    # Index 2+: scan LLM_API_KEY_2, _3, _4, ... until first gap
    idx = 2
    while True:
        api_key = _get_env_with_index("LLM_API_KEY", idx)
        if not api_key:
            break
        base_url = _get_env_with_index("LLM_BASE_URL", idx)
        model = _get_env_with_index("LLM_MODEL", idx)
        protocol = _normalize_protocol(
            _get_env_with_index("LLM_PROTOCOL", idx, _detect_protocol(base_url))
        )
        provider = _provider_name_from_protocol(protocol)
        purpose = _get_env_with_index("LLM_PURPOSE", idx, "general")
        timeout_seconds = _parse_float_env("LLM_TIMEOUT", idx, 30.0)
        max_tokens = _parse_int_env("LLM_MAX_TOKENS", idx, 1024)

        if not model:
            defaults = {
                "anthropic_messages": "claude-sonnet-4-20250514",
                "local_gateway": "local-model",
                "openai_compatible": "gpt-4o-mini",
            }
            model = defaults.get(protocol, "gpt-4o-mini")

        providers.append(
            LLMProviderConfig(
                provider=provider,
                protocol=protocol,
                base_url=base_url,
                api_key=api_key,
                model=model,
                db_url=db_url,
                vector_db_path=vector_db_path,
                purpose=purpose,
                timeout_seconds=timeout_seconds,
                max_tokens=max_tokens,
            )
        )
        idx += 1

    return tuple(providers)


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "dev")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    # Database
    db_type: str = os.getenv("DB_TYPE", "sqlite")
    db_url: str = os.getenv("DB_URL", "sqlite:///data/demo_db/sales.db")
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "")

    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./.deploy/chroma")
    sql_max_rows: int = int(os.getenv("SQL_MAX_ROWS", "200"))
    sql_query_timeout: int = int(os.getenv("SQL_QUERY_TIMEOUT", "15"))
    readonly_mode: bool = os.getenv("READONLY_MODE", "true").lower() == "true"
    allowed_tables: str = os.getenv(
        "ALLOWED_TABLES", "orders,products,order_items,customers"
    )

    # LLM providers stored as a tuple, parsed at construction time
    _llm_providers: tuple[LLMProviderConfig, ...] = ()

    @property
    def provider_count(self) -> int:
        """Return total number of configured LLM providers."""
        return len(self._llm_providers)

    def get_provider_config(self, index: int = 1) -> LLMProviderConfig:
        """Get provider config. index is 1-based."""
        if index < 1 or index > len(self._llm_providers):
            raise ValueError(
                f"Provider index {index} out of range (1-{len(self._llm_providers)})"
            )
        return self._llm_providers[index - 1]

    def has_fallback(self) -> bool:
        """Return True if more than one provider is configured."""
        return len(self._llm_providers) > 1


def get_settings() -> Settings:
    """Create Settings instance with dynamically parsed LLM providers."""
    db_url = os.getenv("DB_URL", "sqlite:///data/demo_db/sales.db")
    vector_db_path = os.getenv("VECTOR_DB_PATH", "./.deploy/chroma")

    providers = _parse_providers(db_url, vector_db_path)

    return Settings(
        app_env=os.getenv("APP_ENV", "dev"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        db_type=os.getenv("DB_TYPE", "sqlite"),
        db_url=db_url,
        mysql_host=os.getenv("MYSQL_HOST", "localhost"),
        mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
        mysql_user=os.getenv("MYSQL_USER", ""),
        mysql_password=os.getenv("MYSQL_PASSWORD", ""),
        mysql_database=os.getenv("MYSQL_DATABASE", ""),
        vector_db_path=vector_db_path,
        sql_max_rows=int(os.getenv("SQL_MAX_ROWS", "200")),
        sql_query_timeout=int(os.getenv("SQL_QUERY_TIMEOUT", "15")),
        readonly_mode=os.getenv("READONLY_MODE", "true").lower() == "true",
        allowed_tables=os.getenv(
            "ALLOWED_TABLES", "orders,products,order_items,customers"
        ),
        _llm_providers=providers,
    )
