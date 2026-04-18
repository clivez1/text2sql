# Round 6: 全面重构方案

> 生成时间：2026-04-17
> 状态：**执行中**

---

## 一、背景

Round 5 完成了数据分离。本轮解决剩余 5 个核心问题：
1. Vanna 依赖阻塞（`vanna.chromadb`/`vanna.openai` 在 2.0 中不存在）
2. LLM 配置仅支持 2 个 provider，需求要求 N 个
3. 代码中有重复文件和死引用
4. 4 个测试文件被 Vanna 导入阻塞
5. 文档未反映架构变更

## 二、策略决定

### Vanna 迁移：选择 **方案 C — 完全移除 Vanna**

**理由：**
- Vanna 仓库已于 2026-03-29 归档（read-only），不会再有更新
- Vanna 2.0 是完全重写（Agent 架构），`generate_sql()` API 不再存在
- 项目实际只用 Vanna 做 OpenAI 封装 + ChromaDB 向量存储
- 我们已直接依赖 `openai` SDK 和 `chromadb`，Vanna 是多余的中间层
- `requirements.txt` 声明 `vanna>=0.7,<1` 但安装的是 `2.0.2`，版本冲突

**替代方案：** 直接使用 `openai` SDK 的 `chat.completions.create()` + `chromadb` 的 `Collection.query()`

### N-Provider Fallback：`.impKey` 动态解析

**模式：** 在 `.impKey` 中定义 `LLM_PROVIDERS` JSON 数组或按序号定义 `LLM_API_KEY_1/2/3...`
按序号解析所有 provider，index=1 为主模型，其余为 fallback 链。

---

## 三、执行计划

### Phase 1: 移除 Vanna，重写 adapters.py（P0 阻塞解除）

**改动文件：**
- `app/core/llm/adapters.py` — 删除 Vanna 导入和 `LocalVanna` 类，`OpenAICompatibleAdapter.generate_sql()` 改用 `openai.chat.completions.create()` 直接调用
- `requirements.txt` — 删除 `vanna>=0.7,<1` 行
- `app/core/llm/resilient_client.py` — 删除（Vanna 专用包装器，功能已被 client.py fallback 覆盖）
- `app/core/llm/resilient_llm.py` — 删除（与 resilient_client.py 完全重复）

**保留不变：**
- `LLMAdapter` Protocol（接口定义，无 Vanna 依赖）
- `prompts.py`（纯净模块）
- `client.py` 路由逻辑（仅修改 adapter 层接口）
- `health_check.py`（通过 adapter 间接调用，无 Vanna 依赖）

### Phase 2: N-Provider Fallback 系统

**改动文件：**
- `app/config/settings.py` — 重构为动态解析 N 个 provider
  - 解析规则：扫描 `LLM_API_KEY_1`, `LLM_BASE_URL_1`, `LLM_MODEL_1` ... `LLM_API_KEY_N`
  - 向后兼容：`LLM_API_KEY`（无后缀）等价于 `_1`
  - `get_provider_config(index)` 支持任意 index
  - `provider_count` 属性返回可用 provider 数量
- `app/core/llm/client.py` — `_try_llm_with_fallback` 改为循环遍历所有 fallback provider
- `app/core/llm/health_check.py` — 健康检查支持 N 个 provider
- `.env.example` — 添加 N-provider 配置示例

### Phase 3: 代码清理

- 删除 `resilient_client.py` 和 `resilient_llm.py`（Vanna 专用，已无引用）
- 删除 `_vanna_cache` 全局状态
- 清理 `__init__.py` re-exports（如有变化）
- 简化 `client.py` 中的 v1/v2 双版本（合并为一个版本）

### Phase 4: 测试修复

- 修复 4 个被阻塞的测试文件：
  - `test_llm_client.py`
  - `test_fast_fallback_strategy.py`
  - `test_resilient_client.py` — 删除（对应源文件已删除）
  - `test_resilient_llm.py` — 删除（对应源文件已删除）
- 运行全量测试 `pytest tests/ -v`

### Phase 5: 文档更新

- `docs/CONFIGURATION.md` — N-provider 配置说明
- `docs/architecture.md` — LLM 模块架构更新（移除 Vanna）
- `docs/QUICKSTART.md` — 更新配置步骤
- `README.md` — 技术栈更新（移除 Vanna 引用）
- `devfile/01-completed.md` — 记录 Round 6 完成
- `devfile/02-pending.md` — 更新待办
- `devfile/00-master-plan.md` — 更新主方案

---

## 四、风险与缓解

| 风险 | 缓解 |
|------|------|
| 移除 Vanna 后 generate_sql 行为变化 | 新 adapter 使用相同 prompt 模板，输出格式不变 |
| N-provider 配置向后不兼容 | 保留 `LLM_API_KEY`（无后缀）作为 `_1` 的别名 |
| 测试覆盖率下降 | 删除 Vanna 专用测试的同时添加新 adapter 测试 |

---

_最后更新：2026-04-17_
