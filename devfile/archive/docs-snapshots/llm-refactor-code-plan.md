# LLM Adapter Refactor for Bailian Code Plan

## 最小重构方案
- 保留 `app/core/orchestrator/pipeline.py` 与 SQL fallback 逻辑不变。
- 将原先 `app/core/llm/client.py` 中“provider 选择 + Vanna 初始化 + endpoint 写死”拆成统一适配层。
- 新增 `LLMAdapter` 协议与两类 provider：`bailian_code_plan`、`openai_compatible`。
- 配置层统一暴露：`provider / base_url / api_key / model`；同时保留 Bailian/OpenAI 兼容字段作为回退来源。

## 关键兼容点
- `bailian_code_plan` 默认端点：`https://coding.dashscope.aliyuncs.com/v1`
- API Key 优先来源：`LLM_API_KEY`，否则回退 `BAILIAN_API_KEY` / `OPENCLAW_BAILIAN_API_KEY`
- `openai_compatible` 可直接对接标准 OpenAI 样式服务，也可复用 Code Plan 端点做兼容验证
- LLM 异常时继续走 Week1 本地规则 fallback，不伪造成功

## 验证命令
```bash
cd /home/clawz/.openclaw/workspace-cos/projects/text2sql-agent
. .venv/bin/activate
python scripts/init_demo_db.py
PYTHONPATH=. LLM_PROVIDER=bailian_code_plan python scripts/verify_llm.py
PYTHONPATH=. LLM_PROVIDER=openai_compatible LLM_BASE_URL=https://coding.dashscope.aliyuncs.com/v1 LLM_API_KEY="$OPENCLAW_BAILIAN_API_KEY" LLM_MODEL=glm-5 python scripts/verify_llm.py
python -m app.core.orchestrator.pipeline "华东销售额是多少？"
```
