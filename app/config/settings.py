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


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "dev")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    # Primary LLM config
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_model: str = os.getenv("LLM_MODEL", "")

    # Fallback LLM config (optional, used when primary fails)
    llm_api_key_2: str = os.getenv("LLM_API_KEY_2", "")
    llm_base_url_2: str = os.getenv("LLM_BASE_URL_2", "")
    llm_model_2: str = os.getenv("LLM_MODEL_2", "")

    # Database
    db_type: str = os.getenv("DB_TYPE", "sqlite")
    db_url: str = os.getenv("DB_URL", "sqlite:///data/demo_db/sales.db")
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "")

    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./data/chroma")
    sql_max_rows: int = int(os.getenv("SQL_MAX_ROWS", "200"))
    sql_query_timeout: int = int(os.getenv("SQL_QUERY_TIMEOUT", "15"))
    readonly_mode: bool = os.getenv("READONLY_MODE", "true").lower() == "true"
    allowed_tables: str = os.getenv(
        "ALLOWED_TABLES", "orders,products,order_items,customers"
    )

    def get_provider_config(self, index: int = 1) -> LLMProviderConfig:
        if index == 1:
            api_key = self.llm_api_key
            base_url = self.llm_base_url
            model = self.llm_model
        elif index == 2:
            api_key = self.llm_api_key_2
            base_url = self.llm_base_url_2
            model = self.llm_model_2
        else:
            raise ValueError(f"Invalid provider index: {index}")

        provider = _detect_provider(base_url)

        if not model:
            defaults = {
                "anthropic": "claude-sonnet-4-20250514",
                "openai_compatible": "gpt-4o-mini",
            }
            model = defaults.get(provider, "gpt-4o-mini")

        return LLMProviderConfig(
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            model=model,
            db_url=self.db_url,
            vector_db_path=self.vector_db_path,
        )

    def has_fallback(self) -> bool:
        return bool(self.llm_api_key_2 and self.llm_base_url_2)


def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "dev"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_base_url=os.getenv("LLM_BASE_URL", ""),
        llm_model=os.getenv("LLM_MODEL", ""),
        llm_api_key_2=os.getenv("LLM_API_KEY_2", ""),
        llm_base_url_2=os.getenv("LLM_BASE_URL_2", ""),
        llm_model_2=os.getenv("LLM_MODEL_2", ""),
        db_type=os.getenv("DB_TYPE", "sqlite"),
        db_url=os.getenv("DB_URL", "sqlite:///data/demo_db/sales.db"),
        mysql_host=os.getenv("MYSQL_HOST", "localhost"),
        mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
        mysql_user=os.getenv("MYSQL_USER", ""),
        mysql_password=os.getenv("MYSQL_PASSWORD", ""),
        mysql_database=os.getenv("MYSQL_DATABASE", ""),
        vector_db_path=os.getenv("VECTOR_DB_PATH", "./data/chroma"),
        sql_max_rows=int(os.getenv("SQL_MAX_ROWS", "200")),
        sql_query_timeout=int(os.getenv("SQL_QUERY_TIMEOUT", "15")),
        readonly_mode=os.getenv("READONLY_MODE", "true").lower() == "true",
        allowed_tables=os.getenv(
            "ALLOWED_TABLES", "orders,products,order_items,customers"
        ),
    )
