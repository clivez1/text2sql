from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env first (contains placeholders for documentation)
load_dotenv()
# Then load .impKey (contains actual sensitive values, overrides .env)
load_dotenv(dotenv_path=".impKey", override=True)


def _detect_provider(base_url: str) -> str:
    """Auto-detect API protocol from base_url pattern."""
    if not base_url:
        return "openai_compatible"
    lower = base_url.lower()
    if "anthropic" in lower or "claude" in lower:
        return "anthropic"
    return "openai_compatible"


@dataclass(frozen=True)
class LLMProviderConfig:
    provider: str
    base_url: str
    api_key: str
    model: str
    db_url: str
    vector_db_path: str


def _parse_providers(db_url: str, vector_db_path: str) -> tuple[LLMProviderConfig, ...]:
    """Parse LLM providers from environment variables.

    Detection order:
    - Index 1: LLM_API_KEY_1 (preferred) or LLM_API_KEY (backward compatible)
    - Index 2+: LLM_API_KEY_2, LLM_API_KEY_3, ... until first gap
    """
    providers: list[LLMProviderConfig] = []

    # Index 1: prefer LLM_API_KEY_1, fall back to LLM_API_KEY (no suffix)
    api_key_1 = os.getenv("LLM_API_KEY_1") or os.getenv("LLM_API_KEY", "")
    if api_key_1:
        base_url_1 = os.getenv("LLM_BASE_URL_1") or os.getenv("LLM_BASE_URL", "")
        model_1 = os.getenv("LLM_MODEL_1") or os.getenv("LLM_MODEL", "")
        provider_1 = _detect_provider(base_url_1)

        if not model_1:
            defaults = {
                "anthropic": "claude-sonnet-4-20250514",
                "openai_compatible": "gpt-4o-mini",
            }
            model_1 = defaults.get(provider_1, "gpt-4o-mini")

        providers.append(
            LLMProviderConfig(
                provider=provider_1,
                base_url=base_url_1,
                api_key=api_key_1,
                model=model_1,
                db_url=db_url,
                vector_db_path=vector_db_path,
            )
        )

    # Index 2+: scan LLM_API_KEY_2, _3, _4, ... until first gap
    idx = 2
    while True:
        api_key = os.getenv(f"LLM_API_KEY_{idx}", "")
        if not api_key:
            break
        base_url = os.getenv(f"LLM_BASE_URL_{idx}", "")
        model = os.getenv(f"LLM_MODEL_{idx}", "")
        provider = _detect_provider(base_url)

        if not model:
            defaults = {
                "anthropic": "claude-sonnet-4-20250514",
                "openai_compatible": "gpt-4o-mini",
            }
            model = defaults.get(provider, "gpt-4o-mini")

        providers.append(
            LLMProviderConfig(
                provider=provider,
                base_url=base_url,
                api_key=api_key,
                model=model,
                db_url=db_url,
                vector_db_path=vector_db_path,
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
