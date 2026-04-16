from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from openai import OpenAI
from vanna.chromadb import ChromaDB_VectorStore
from vanna.openai import OpenAI_Chat

from app.config.settings import LLMProviderConfig
from app.core.llm.prompts import TEXT2SQL_SYSTEM_PROMPT, build_prompt_bundle
from app.core.retrieval.schema_loader import retrieve_schema_context
from app.core.sql.generator import RULES


class LocalVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, client: OpenAI, config: dict):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, client=client, config=config)


class LLMAdapter(Protocol):
    provider_name: str

    def generate_sql(self, question: str) -> str:
        ...

    def connectivity_check(self) -> str:
        ...


@dataclass(frozen=True)
class OpenAICompatibleAdapter:
    config: LLMProviderConfig
    provider_name: str = "openai_compatible"

    def _build_client(self) -> OpenAI:
        if not self.config.api_key:
            raise RuntimeError(f"{self.provider_name} API key missing")
        return OpenAI(api_key=self.config.api_key, base_url=self.config.base_url or None)

    def _build_vanna(self) -> LocalVanna:
        client = self._build_client()
        vn = LocalVanna(
            client=client,
            config={
                "model": self.config.model,
                "path": self.config.vector_db_path,
                "temperature": 0.1,
            },
        )

        db_path = self.config.db_url.replace("sqlite:///", "")
        vn.connect_to_sqlite(db_path)

        ddl_path = Path("data/ddl/sales_schema.sql")
        if ddl_path.exists():
            vn.train(ddl=ddl_path.read_text(encoding="utf-8"))

        vn.train(documentation=TEXT2SQL_SYSTEM_PROMPT)
        vn.train(documentation=(
            "业务说明：orders 是订单主表，order_items 是订单明细，products 是商品表。"
            "销售额优先按 order_items.quantity * order_items.unit_price 汇总；"
            "城市在 orders.city，区域在 orders.region，商品名在 products.product_name。"
            "中文问题优先单表求解，只有明确涉及销量/销售额拆分时再联表。"
        ))

        for rule in RULES:
            question = "，".join(rule.keywords)
            vn.train(question=question, sql=rule.sql)
            vn.train(documentation=f"示例说明：{rule.explanation}")

        return vn

    def generate_sql(self, question: str) -> str:
        vn = self._build_vanna()
        prompt = build_prompt_bundle(question, retrieve_schema_context(question))
        vn.train(documentation=prompt.system_prompt)
        vn.train(documentation=prompt.user_prompt)
        return vn.generate_sql(question)

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


@dataclass(frozen=True)
class BailianCodePlanAdapter(OpenAICompatibleAdapter):
    provider_name: str = "bailian_code_plan"
