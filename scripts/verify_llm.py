from __future__ import annotations

import json
import sys

from app.core.llm.client import check_llm_connectivity, generate_sql


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "上个月销售额最高的前5个产品是什么？"
    provider, connectivity = check_llm_connectivity()
    sql, explanation, mode, blocked_reason = generate_sql(question)
    print(json.dumps({
        "provider": provider,
        "connectivity": connectivity,
        "question": question,
        "generated_sql": sql,
        "explanation": explanation,
        "mode": mode,
        "blocked_reason": blocked_reason,
    }, ensure_ascii=False, indent=2))
