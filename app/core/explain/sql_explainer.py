def explain(sql: str) -> str:
    return f"SQL will execute in readonly mode: {sql[:120]}..."
