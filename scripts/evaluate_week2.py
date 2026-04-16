from __future__ import annotations

import json
from pathlib import Path

from app.core.llm.prompts import build_sql_explanation
from app.core.sql.generator import DEFAULT_EXPLANATION, generate_sql_by_rules
from app.core.sql.guard import validate_readonly_sql

BASE_DIR = Path(__file__).resolve().parents[1]
FIXTURE_PATH = BASE_DIR / "tests" / "fixtures" / "qa_test_set.json"


def main() -> None:
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    total = 0
    passed = 0
    single_total = 0
    single_passed = 0
    rows = []

    for item in fixtures:
        sql, rule_explanation = generate_sql_by_rules(item["question"])
        safe_sql = validate_readonly_sql(sql)
        ok = all(token.lower() in safe_sql.lower() for token in item["expected_sql_contains"])
        total += 1
        passed += int(ok)
        if item["category"] == "single_table":
            single_total += 1
            single_passed += int(ok)
        explanation = rule_explanation if rule_explanation != DEFAULT_EXPLANATION else build_sql_explanation(safe_sql, rule_hint=rule_explanation)
        rows.append(
            {
                "question": item["question"],
                "ok": ok,
                "mode": "rules_eval",
                "sql": safe_sql,
                "blocked_reason": None,
                "explanation": explanation,
            }
        )

    result = {
        "total": total,
        "passed": passed,
        "accuracy": round(passed / total * 100, 2),
        "single_table_total": single_total,
        "single_table_passed": single_passed,
        "single_table_accuracy": round(single_passed / single_total * 100, 2) if single_total else 0,
        "details": rows,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
