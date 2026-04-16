#!/usr/bin/env sh
set -e
cd "$(dirname "$0")/.."
. .venv/bin/activate
python scripts/init_demo_db.py
python -m app.core.orchestrator.pipeline "上个月销售额最高的前5个产品是什么？"
python - <<'PY'
from app.api.main import health, schema
print(health())
print(schema())
PY
printf '\nStart UI manually if needed:\nstreamlit run app/ui/streamlit_app.py --server.headless true --server.port 18501\n'
