from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env first (contains placeholders for documentation)
load_dotenv()
# Then load .impKey (contains actual sensitive values, overrides .env)
load_dotenv(dotenv_path=".impKey", override=True)


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
    llm_provider: str = os.getenv("LLM_PROVIDER", "bailian_code_plan")

    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    bailian_api_key: str = os.getenv("BAILIAN_API_KEY") or os.getenv(
        "OPENCLAW_BAILIAN_API_KEY", ""
    )
    bailian_base_url: str = os.getenv(
        "BAILIAN_BASE_URL", "https://coding.dashscope.aliyuncs.com/v1"
    )
    bailian_model: str = os.getenv("BAILIAN_MODEL", "glm-5")

    # Astron (xfyun-maas) 配置
    astron_api_key: str = os.getenv("ASTRON_API_KEY") or os.getenv(
        "OPENCLAW_ASTRON_API_KEY", ""
    )
    astron_base_url: str = os.getenv("ASTRON_BASE_URL", "https://maas-api.xfyun.cn/v1")
    astron_model: str = os.getenv("ASTRON_MODEL", "astron-code-latest")

    # 数据库配置 - 支持多数据库
    db_type: str = os.getenv("DB_TYPE", "sqlite")  # sqlite, mysql, postgresql
    db_url: str = os.getenv("DB_URL", "sqlite:///data/demo_db/sales.db")

    # MySQL 专用配置
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "")

    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./data/chroma")
    sql_max_rows: int = int(os.getenv("SQL_MAX_ROWS", "200"))
    sql_query_timeout: int = int(os.getenv("SQL_QUERY_TIMEOUT", "15"))
    readonly_mode: bool = os.getenv("READONLY_MODE", "true").lower() == "true"

    # 允许的表名白名单（逗号分隔）
    allowed_tables: str = os.getenv(
        "ALLOWED_TABLES", "orders,products,order_items,customers"
    )

    def get_provider_config(self) -> LLMProviderConfig:
        provider = self.llm_provider
        if provider == "bailian_code_plan":
            return LLMProviderConfig(
                provider=provider,
                base_url=self.llm_base_url or self.bailian_base_url,
                api_key=self.llm_api_key or self.bailian_api_key,
                model=self.llm_model or self.bailian_model,
                db_url=self.db_url,
                vector_db_path=self.vector_db_path,
            )
        if provider == "openai_compatible":
            return LLMProviderConfig(
                provider=provider,
                base_url=self.llm_base_url or self.openai_base_url,
                api_key=self.llm_api_key or self.openai_api_key,
                model=self.llm_model or self.openai_model,
                db_url=self.db_url,
                vector_db_path=self.vector_db_path,
            )
        if provider == "astron":
            return LLMProviderConfig(
                provider=provider,
                base_url=self.llm_base_url or self.astron_base_url,
                api_key=self.llm_api_key or self.astron_api_key,
                model=self.llm_model or self.astron_model,
                db_url=self.db_url,
                vector_db_path=self.vector_db_path,
            )
        raise RuntimeError(f"Unsupported LLM provider: {provider}")


def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "dev"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        llm_provider=os.getenv("LLM_PROVIDER", "bailian_code_plan"),
        llm_base_url=os.getenv("LLM_BASE_URL", ""),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        bailian_api_key=os.getenv("BAILIAN_API_KEY")
        or os.getenv("OPENCLAW_BAILIAN_API_KEY", ""),
        bailian_base_url=os.getenv(
            "BAILIAN_BASE_URL", "https://coding.dashscope.aliyuncs.com/v1"
        ),
        bailian_model=os.getenv("BAILIAN_MODEL", "glm-5"),
        astron_api_key=os.getenv("ASTRON_API_KEY")
        or os.getenv("OPENCLAW_ASTRON_API_KEY", ""),
        astron_base_url=os.getenv("ASTRON_BASE_URL", "https://maas-api.xfyun.cn/v1"),
        astron_model=os.getenv("ASTRON_MODEL", "astron-code-latest"),
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
