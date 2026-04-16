# 第三轮架构方案分析

> 基于 LEE 的反馈：当前方案"不够清晰、不够简洁"，且需要支持：
> 1. 多 RAG embedding 思路对比（性能评测）
> 2. 增大 langchain 使用比重（凸显 langchain 技能）

---

## 一、当前代码库核心结构

```
generate_sql()  ← client.py [7 种职责混合]
    │
    ├── retrieve_schema_context()    ← retrieval/schema_loader.py [ChromaDB 硬编码]
    │       └── ChromaDB + query → documents
    │
    ├── classify_question()           ← nlu/question_classifier.py [结果未被充分利用]
    │
    ├── generate_sql_by_rules()       ← sql/generator.py [27 条硬编码 RULES]
    │
    └── adapter.generate_sql()        ← llm/adapters.py [Vanna+OpenAI 绑定]

ask_question() ← pipeline.py
    ├── generate_sql()
    └── run_query()
```

---

## 二、LEE 新需求的本质

### 需求 1：多 RAG embedding 对比

**本质是什么？**
- `retrieve_schema_context()` 是唯一的 retrieval 路径
- 未来可能换 embedding 模型（text-embedding-3 / bge / m3e）
- 未来可能换向量库（ChromaDB → FAISS → PGvector）
- 未来可能换检索策略（top-k → MMR → hybrid search）

**对比评测需要什么？**
- 相同的 retrieval interface，不同的实现
- 相同的 benchmark 问题集
- 统一的评测指标（latency / recall / accuracy）

### 需求 2：增大 langchain 比重

**LangChain 能提供什么？**
| 组件 | 当前方案 | LangChain 方案 |
|------|---------|---------------|
| Embedding | Vanna/ChromaDB 封装 | `LangChain Embeddings` 接口（OpenAI/BGE/M3E） |
| Vector Store | `chromadb.PersistentClient` | `LangChain VectorStore` 抽象 |
| LLM 调用 | `OpenAI()` / `BailianCodePlanAdapter` | `LangChain LLMs` / `ChatModels` |
| Chain | `generate_sql()` 函数 | LCEL `RunnableSequence` |
| Output Parser | 手动解析 | `StrOutputParser` / `PydanticOutputParser` |
| Prompt Template | 字符串拼接 | `ChatPromptTemplate` |

---

## 三、第三轮：统一后的简洁方案

**方案名称：LangChain Native + Retrieval Strategy**

**核心思路：**
1. retrieval 层抽象为"可插拔策略"
2. LangChain 作为底层基础设施（LLM/Embedding/VectorStore/Chain）
3. 最小化新抽象层——直接复用 LangChain LCEL

### 架构文本树

```
app/
├── core/
│   ├── retrieval/
│   │   ├── base.py              # SchemaRetriever 接口
│   │   ├── chromadb_retriever.py # ChromaDB 实现（LangChain）
│   │   ├── faiss_retriever.py   # FAISS 实现（LangChain）  [新增]
│   │   ├── pgvector_retriever.py # PGvector 实现（LangChain）[新增]
│   │   └── local_retriever.py   # 本地 fallback（无向量库）
│   │
│   ├── generation/
│   │   ├── base.py              # SqlGenerator 接口
│   │   ├── llm_generator.py     # LLM 生成（LangChain LCEL Chain）
│   │   └── rule_generator.py    # 规则生成（YAML 驱动）    [重构]
│   │
│   ├── sql/
│   │   ├── executor.py          # 执行器
│   │   ├── db_pool.py           # 连接池（统一 db_abstraction）
│   │   └── guard.py             # SQL 安全校验
│   │
│   ├── nlu/
│   │   └── classifier.py        # 问题分类（保持轻量）
│   │
│   └── pipeline/
│       ├── orchestrator.py      # 编排器
│       └── context.py           # 上下文
│
├── adapters/
│   ├── embeddings/              # Embedding 策略实现
│   │   ├── openai_embedding.py # OpenAI text-embedding-3
│   │   ├── bge_embedding.py    # BGE embedding        [新增]
│   │   └── m3e_embedding.py    # M3E embedding        [新增]
│   │
│   └── llm/                     # LLM 适配器（LangChain驱动）
│       ├── openai_llm.py
│       ├── bailian_llm.py
│       └── registry.py          # LLM Provider 注册表
│
├── rules/
│   ├── store.py                # RuleStore（YAML 加载）
│   └── default_rules.yaml       # 规则配置
│
├── api/
│   └── main.py
│
└── ui/
    └── streamlit_app.py         # HTTP 调用 API
```

---

## 四、与当前方案的对比

| 维度 | 当前方案（05-architecture-debate.md） | 第三轮方案 |
|------|-------------------------------------|-----------|
| **RAG Retrieval** | ChromaDB 硬编码 | `SchemaRetriever` 抽象 + 多实现（ChromaDB/FAISS/PGvector） |
| **Embedding** | Vanna 封装 | LangChain `Embeddings` 接口，支持多模型 |
| **LLM** | Vanna+OpenAI 绑定 | LangChain `LLM` / `ChatModels` 接口 |
| **Chain** | `generate_sql()` 函数 | LangChain LCEL `RunnableSequence` |
| **新增文件数** | ~20 | ~15 |
| **抽象层数** | 5 个 Protocol（多） | 3 个核心接口（少） |
| **langchain 比重** | 间接（Vanna 依赖 LC） | 直接（原生使用 LCEL） |

---

## 五、核心接口（仅 3 个）

```python
# core/retrieval/base.py
class SchemaRetriever(Protocol):
    """Schema 检索策略接口"""
    def retrieve(self, question: str) -> str:
        """返回 schema 上下文字符串"""
        ...

# core/generation/base.py
class SqlGenerator(Protocol):
    """SQL 生成策略接口"""
    def supports(self, question: str, classification: QuestionClassification) -> bool:
        """判断是否支持生成"""
        ...
    def generate(self, question: str, schema_context: str) -> SqlResult:
        """生成 SQL"""
        ...

# adapters/llm/registry.py
class LLMProviderRegistry:
    """LLM Provider 注册表——新增 Provider 不改已有文件"""
    @classmethod
    def register(cls, name: str):
        """@register('provider_name') 装饰器"""
        ...
```

---

## 六、多 RAG Embedding 对比：如何实现

### 评测脚本结构

```python
# scripts/eval_retrieval.py
"""
RAG Retrieval 对比评测脚本
用法: python scripts/eval_retrieval.py --retriever chromadb --embedding bge
"""
import argparse
from app.core.retrieval import get_retriever

RETRIEVERS = {
    "chroma": "app.core.retrieval.chromadb_retriever.ChromaDBRetriever",
    "faiss": "app.core.retrieval.faiss_retriever.FAISSRetriever",
    "pgvector": "app.core.retrieval.pgvector_retriever.PGVectorRetriever",
}

EMBEDDINGS = {
    "openai": "app.adapters.embeddings.openai_embedding.OpenAIEmbedding",
    "bge": "app.adapters.embeddings.bge_embedding.BGEEmbedding",
    "m3e": "app.adapters.embeddings.m3e_embedding.M3EEmbedding",
}

BENCHMARK_QUESTIONS = [
    "上个月销售额最高的前5个产品是什么？",
    "各城市的订单数量统计",
    # ... 更多 benchmark 问题
]

def evaluate(retriever_name: str, embedding_name: str):
    retriever_cls = load_class(RETRIEVERS[retriever_name])
    embedding_cls = load_class(EMBEDDINGS[embedding_name])
    
    retriever = retriever_cls(embedding=embedding_cls())
    
    for q in BENCHMARK_QUESTIONS:
        start = time.perf_counter()
        ctx = retriever.retrieve(q)
        latency = (time.perf_counter() - start) * 1000
        print(f"Q: {q} | Latency: {latency:.2f}ms | Context: {ctx[:50]}...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--retriever", choices=list(RETRIEVERS.keys()))
    parser.add_argument("--embedding", choices=list(EMBEDDINGS.keys()))
    args = parser.parse_args()
    evaluate(args.retriever, args.embedding)
```

### 对比矩阵输出示例

```bash
$ python scripts/eval_retrieval.py --retriever chromadb --embedding bge
$ python scripts/eval_retrieval.py --retriever faiss --embedding bge
$ python scripts/eval_retrieval.py --retriever pgvector --embedding m3e

| Retriever | Embedding | Avg Latency (ms) |
|-----------|-----------|-----------------|
| ChromaDB  | BGE       | 23.4            |
| FAISS     | BGE       | 12.1            |
| PGvector  | M3E       | 18.7            |
```

---

## 七、LangChain LCEL Chain 实现

```python
# core/generation/llm_generator.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from app.adapters.llm.registry import LLMProviderRegistry

@LLMProviderRegistry.register("openai")
class LLMGenerator:
    def __init__(self, config: LLMProviderConfig):
        self._config = config
    
    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个SQL生成专家。结合以下Schema上下文生成SQL。\n\n{schema_context}"),
            ("human", "{question}"),
        ])
        llm = ChatOpenAI(
            model=self._config.model,
            api_key=self._config.api_key,
            base_url=self._config.base_url,
            temperature=0.1,
        )
        return prompt | llm | StrOutputParser()
    
    def generate(self, question: str, schema_context: str) -> SqlResult:
        chain = self._build_chain()
        sql = chain.invoke({
            "question": question,
            "schema_context": schema_context,
        })
        return SqlResult(sql=sql.strip(), mode=self._config.provider)


@LLMProviderRegistry.register("bailian")
class BailianLLMGenerator(LLMGenerator):
    """通义千问 / 百炼 CodePlan"""
    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个SQL生成专家。结合以下Schema上下文生成SQL。\n\n{schema_context}"),
            ("human", "{question}"),
        ])
        llm = ChatOpenAI(
            model=self._config.model,
            api_key=self._config.api_key,
            base_url=self._config.base_url,
            temperature=0.1,
        )
        return prompt | llm | StrOutputParser()
```

---

## 八、关键改动文件清单

| 文件 | 动作 | 说明 |
|------|------|------|
| `core/retrieval/base.py` | 新增 | `SchemaRetriever` 接口 |
| `core/retrieval/chromadb_retriever.py` | 新增 | ChromaDB 实现（LangChain） |
| `core/retrieval/faiss_retriever.py` | 新增 | FAISS 实现（LangChain） |
| `core/retrieval/pgvector_retriever.py` | 新增 | PGvector 实现（LangChain） |
| `core/retrieval/local_retriever.py` | 新增 | 本地 fallback |
| `adapters/embeddings/openai_embedding.py` | 新增 | OpenAI Embedding |
| `adapters/embeddings/bge_embedding.py` | 新增 | BGE Embedding |
| `adapters/embeddings/m3e_embedding.py` | 新增 | M3E Embedding |
| `core/generation/base.py` | 新增 | `SqlGenerator` 接口 |
| `core/generation/llm_generator.py` | 新增 | LLM 生成（LangChain LCEL） |
| `core/generation/rule_generator.py` | 新增 | 规则生成（YAML） |
| `adapters/llm/registry.py` | 新增 | LLM Provider 注册表 |
| `rules/store.py` | 新增 | RuleStore（YAML 加载） |
| `rules/default_rules.yaml` | 新增 | 规则配置 |
| `core/retrieval/schema_loader.py` | 废弃 | 合并入 retrieval/ |
| `core/sql/generator.py` | 重构 | 规则部分移入 rule_generator.py |
| `core/llm/adapters.py` | 重构 | 适配 LangChain |
| `core/pipeline/orchestrator.py` | 新增/重构 | 编排器 |

---

## 九、执行步骤（精简版）

| Step | 内容 | 优先级 |
|------|------|--------|
| **R1** | 定义 `SchemaRetriever` 接口 + ChromaDB 实现 | P0 |
| **R2** | 实现 `BGEEmbedding` / `M3EEmbedding` 适配器 | P0 |
| **R3** | 实现 `FAISSRetriever` / `PGVectorRetriever` | P1 |
| **R4** | 写 `scripts/eval_retrieval.py` 对比脚本 | P1 |
| **G1** | 定义 `SqlGenerator` 接口 | P0 |
| **G2** | `LLMGenerator` 重写为 LangChain LCEL | P0 |
| **G3** | 规则 YAML 化（`rule_generator.py`） | P1 |
| **G4** | `LLMProviderRegistry` + `@register` | P0 |
| **P1** | 重构 `pipeline.py` → `orchestrator.py` | P1 |
| **P2** | UI 改为 HTTP 调用 | P1 |

---

## 十、第三轮 vs 第二轮方案对比

| 维度 | 第二轮（提案 E） | 第三轮（本方案） |
|------|----------------|----------------|
| **RAG 抽象** | `ISchemaRetrievalStrategy` | `SchemaRetriever`（更简洁） |
| **多 Embedding** | ❌ 未考虑 | ✅ LangChain `Embeddings` 接口 |
| **LangChain 比重** | 间接（Vanna 依赖） | ✅ 原生 LCEL |
| **对比评测** | ❌ | ✅ `scripts/eval_retrieval.py` |
| **核心接口数** | 5 个 | 3 个 |
| **新增文件数** | ~20 | ~15 |
| **迁移思路** | 渐进 | 渐进 |

---

## 十一、方案成熟度评估

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 模块结构清晰 | ✅ | 3 个核心接口，职责分明 |
| 改动范围可控 | ✅ | 新增为主，重构为辅 |
| 多 RAG 对比支持 | ✅ | `SchemaRetriever` 抽象 + 对比脚本 |
| LangChain 比重提升 | ✅ | 原生使用 LCEL / Embeddings / VectorStore |
| 迁移路径明确 | ✅ | 每个 Step 可独立测试/回滚 |
| 简洁性 | ✅ | 比提案 A-E 更简洁，抽象层更少 |

**结论：第三轮方案已达到"成熟可执行"状态。**

---

*文档更新时间：2026-04-14*
