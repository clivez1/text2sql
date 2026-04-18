# Text2SQL Agent - Agent Instructions

## Quick Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html

# Initialize demo database (REQUIRED before first run)
python scripts/init_demo_db.py

# Ingest schema to ChromaDB (REQUIRED for RAG retrieval)
python scripts/ingest_schema.py

# Start Streamlit UI
streamlit run app/ui/streamlit_app.py

# Start FastAPI server
uvicorn app.api.main:app --reload

# Docker combined mode (UI + API)
docker-compose up -d combined
```

## Startup Order

1. `python scripts/init_demo_db.py` — creates `data/demo_db/sales.db`
2. `python scripts/ingest_schema.py` — populates ChromaDB (required for schema retrieval)
3. Then start UI or API

## Architecture

### Entry Points
- **FastAPI**: `app/api/main.py` — `/ask`, `/health`, `/schemas`, `/metrics`
- **Streamlit**: `app/ui/streamlit_app.py`
- **Pipeline**: `app/core/orchestrator/pipeline.py` — `ask_question()` is the main orchestration entry

### Core Flow
```
User Question → QuestionClassifier → SchemaRetriever → SQLGenerator → SQLExecutor → ChartRecommender
```

### Key Modules
| Module | Purpose |
|--------|---------|
| `app/core/llm/client.py` | LLM adapter selection, `generate_sql()` entry |
| `app/core/sql/generator.py` | Rule-based SQL generation |
| `app/core/retrieval/` | Schema retrieval (ChromaDB) |
| `app/core/nlu/question_classifier.py` | Local question classification |
| `app/rules/` | YAML-based SQL rules (Round 4) |

## LLM Providers

Configured via `LLM_PROVIDER` env var:
- `bailian_code_plan` — Alibaba Bailian
- `openai_compatible` — OpenAI or compatible APIs
- `astron` — Xfyun Astron

Provider routing in `app/core/llm/client.py:get_llm_adapter()` uses if-elif chain.

## Feature Flags

- `READONLY_MODE=true` — Only allow SELECT statements
- `API_KEY_ENABLED=true` — Enable API key authentication

## SQL Rules

Rules are defined in `app/rules/default_rules.yaml`:
- `keywords`: Match against user question
- `sql`: Template SQL to execute
- `priority`: Higher number = higher priority
- `tags`: Categorization labels

`RuleStore` in `app/rules/__init__.py` handles matching.

## Database Support

- SQLite (default): `DB_URL=sqlite:///data/demo_db/sales.db`
- MySQL: Set `DB_TYPE=mysql` + MySQL env vars
- PostgreSQL: Set `DB_TYPE=postgresql`

Connectors in `app/core/sql/connectors/`.

## Testing

- 265 tests, 80% coverage
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- CI: `.github/workflows/test.yml` runs on push to main/develop

## Recent Architecture Changes (Round 4, 2026-04-15)

- Rules migrated from hardcoded Python to YAML
- `SchemaRetriever` Protocol added for retrieval abstraction
- `AskResult.chart_config` field added (chart logic moved to pipeline)
- `database.py` deprecated, use `db_abstraction.py`
- `generate_sql_v2()` with feature flag for gradual rollout

## Common Pitfalls

1. **ChromaDB errors**: Run `python scripts/ingest_schema.py` first
2. **Missing demo DB**: Run `python scripts/init_demo_db.py` before testing
3. **LLM calls failing**: Check `LLM_API_KEY` and provider config in `.env`
4. **SQL blocked**: Check `READONLY_MODE` and `ALLOWED_TABLES` whitelist

## Development Status

See `devfile/` for detailed progress:
- `00-master-plan.md` — Architecture optimization plan
- `01-current-state.md` — Current repository state and boundaries
- `02-target-architecture.md` — Target repository and code architecture
- `03-execution-roadmap.md` — Current roadmap and execution window
