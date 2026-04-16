# Text2SQL-0412 架构分析临时记忆

---

### arch-agent-generation 分析结论

## 一、当�?generation 层的问题

### 1.1 `generate_sql()` �?7 种职责必须拆�?
当前 `client.py::generate_sql()` 是一�?*全链路仲裁�?*，混合了�?
| # | 职责 | 当前实现位置 | 问题 |
|---|------|------------|------|
| 1 | Schema 检索编�?| `retrieve_schema_context()` | ChromaDB 硬编码，无法替换 |
| 2 | 问题分类决策 | `should_fast_fallback()` + `classify_question()` | 分类结果仅用于决定是�?fast-fallback，未传给生成�?|
| 3 | 路由决策 | 硬编�?if/else �?| fast-fallback / LLM health check / exception fallback 三路混合 |
| 4 | LLM 适配器获�?| `get_llm_adapter()` | 直接实例化，不支持运行时切换 |
| 5 | Rule-based 生成 | `generate_sql_by_rules()` | 函数形式，无接口抽象 |
| 6 | LLM 生成 | `adapter.generate_sql()` | Vanna 绑定，OpenAI 绑定 |
| 7 | 解释生成 | `build_sql_explanation()` | 后处理缠绕在一�?|

**结论�? 种职责混在同一个函数中，任何一处改动的副作用都难以追踪�?*

### 1.2 `QuestionClassification` 结果被闲�?
`classify_question()` 返回 `QuestionClassification(category, entities, time_phrases, needs_llm)`，但�?
- `category`（complex_analysis / ranked_aggregation / simple_lookup / unknown�?*从未被用于选择生成策略**
- `needs_llm` 仅在 `should_fast_fallback()` 中用到，但整�?LLM 路径**从未读取 category**
- 这意味着即使�?`simple_lookup` 问题，只要不�?`FAST_FALLBACK_KEYWORDS` 白名单里，就会走 LLM 路径�?*浪费且不稳定**

### 1.3 LLM Adapter �?Vanna 强绑�?
`OpenAICompatibleAdapter._build_vanna()` 内部�?- 继承 `ChromaDB_VectorStore + OpenAI_Chat`（Vanna 的组合类�?- 每次 `generate_sql()` 都重�?`vn.train()`（添加临�?documentation�?- 无法直接使用 LangChain �?`ChatOpenAI` / `ChatPromptTemplate` / `StrOutputParser`

---

## 二、SqlGenerator 接口设计

### 2.1 核心抽象

```python
# sql/generator.py 新增抽象
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@dataclass(frozen=True)
class GenerationResult:
    sql: str
    explanation: str
    mode: str                        # "llm" | "rule" | "template"
    backend: str                     # "openai" | "bailian" | "rule_engine"
    latency_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

@runtime_checkable
class SqlGenerator(Protocol):
    """SQL 生成器的抽象接口。两条生成路径：LLM �?Rule"""
    
    @property
    def name(self) -> str:
        """生成器名称，用于日志和路�?""
        ...
    
    def supports(self, classification: QuestionClassification) -> bool:
        """给定问题分类，此生成器是否适用"""
        ...
    
    def generate(
        self,
        question: str,
        schema_context: str,
        classification: QuestionClassification,
    ) -> GenerationResult:
        """执行 SQL 生成"""
        ...
```

### 2.2 三种实现

```python
class RuleBasedGenerator:
    """�?YAML 加载规则，支�?template 合成"""
    name = "rule_engine"
    def supports(self, c: QuestionClassification) -> bool:
        return c.category in {"simple_lookup", "ranked_aggregation"} and not c.needs_llm

class VannaGenerator:
    """保留 Vanna 路径（向后兼容）"""
    name = "vanna"

class LcelGenerator:
    """LangChain LCEL Native 生成器，新架构目�?""
    name = "lcel"
```

### 2.3 路由层独立为 `SqlRouter`

```python
class SqlRouter:
    def __init__(
        self,
        generators: list[SqlGenerator],
        classifier: QuestionClassifier,   # 接收 NLU 层注�?    ):
        self.generators = generators
    
    def route(self, question: str) -> SqlGenerator:
        """基于分类结果选择最优生成器"""
        classification = self.classifier.classify(question)
        for gen in self.generators:
            if gen.supports(classification):
                return gen
        return self.generators[-1]  # fallback to LLM
```

---

## 三、LangChain LCEL Chain 实现

### 3.1 当前痛点

Vanna 封装了太多细节，无法直接控制 prompt 模板和输出解析。LCEL Native 目标�?
- **可插�?Embeddings**：支�?OpenAI / BGE / Jina 等多 embedding 对比评测
- **可插�?VectorStore**：Chroma / FAISS / Milvus / Qdrant
- **可观测�?*：LCEL 内置 tracing support
- **可测�?*：Prompt �?OutputParser 可独立单元测�?
### 3.2 LCEL Chain 实现草案

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough

# Prompt 模板（来�?prompts.py 重构�?SQL_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", TEXT2SQL_SYSTEM_PROMPT),
    ("user", """用户问题：{question}\n\nSchema 上下文：\n{schema_context}\n\n示例 SQL：\n{examples_context}\n\n请输出最�?SQL，只返回 SQL 语句，不�?Markdown 格式�?")),
])

SQL_EXPLANATION_PROMPT = ChatPromptTemplate.from_messages([
    ("user", SQL_EXPLANATION_TEMPLATE),
])

# LCEL Chain
def build_sql_generation_chain(
    llm: ChatOpenAI,
    schema_context: str,
    examples_context: str = "",
):
    return (
        {
            "question": RunnablePassthrough(),
            "schema_context": lambda _: schema_context,
            "examples_context": lambda _: examples_context,
        }
        | SQL_GENERATION_PROMPT
        | llm
        | StrOutputParser()
    )

def build_explanation_chain(llm: ChatOpenAI):
    return SQL_EXPLANATION_PROMPT | llm | StrOutputParser()

# LcelGenerator 实现
class LcelGenerator:
    def __init__(
        self,
        llm: ChatOpenAI,
        embeddings,  # LangChain Embeddings 接口
        vectorstore, # LangChain VectorStore 接口
    ):
        self.llm = llm
        self.embeddings = embeddings
        self.vectorstore = vectorstore
    
    def _retrieve_examples(self, question: str, limit: int = 4) -> str:
        docs = self.vectorstore.similarity_search(question, k=limit)
        return "\n\n".join(d.page_content for d in docs)
    
    def generate(
        self,
        question: str,
        schema_context: str,
        classification: QuestionClassification,
    ) -> GenerationResult:
        start = time.perf_counter()
        examples = self._retrieve_examples(question)
        chain = build_sql_generation_chain(self.llm, schema_context, examples)
        sql = chain.invoke(question)
        latency_ms = (time.perf_counter() - start) * 1000
        return GenerationResult(
            sql=sql,
            explanation=build_sql_explanation(sql),
            mode="llm",
            backend="lcel",
            latency_ms=latency_ms,
        )
```

### 3.3 Embeddings / VectorStore 可插拔示�?
```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import BgeEmbeddings  # 国产 embedding

# 通过配置切换
def build_embeddings(provider: str, config: dict):
    if provider == "openai":
        return OpenAIEmbeddings(model=config["model"])
    elif provider == "bge":
        return BgeEmbeddings(model=config["model"], ...)
    raise ValueError(f"Unknown embedding provider: {provider}")

def build_vectorstore(embeddings, provider: str, config: dict):
    if provider == "chroma":
        return Chroma(embedding_function=embeddings, ...)
    # 支持 qdrant / faiss / milvus
```

---

## 四、Rule 生成�?YAML �?
### 4.1 当前问题

`generator.py` �?27 �?`Rule` 对象�?*硬编�?Python tuple**�?- 新增规则需要改代码
- 无法热更�?- 无法做版本化管理
- 无法�?UI 中可视化配置

### 4.2 YAML 化设�?
```yaml
# config/rules/**/*.yaml
rules:
  - id: rule_001
    keywords: ["上个�?, "�?", "产品", "销售额"]
    sql: |
      SELECT p.product_name, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
      FROM order_items oi
      JOIN orders o ON oi.order_id = o.order_id
      JOIN products p ON oi.product_id = p.product_id
      WHERE strftime('%Y-%m', o.order_date) = (
        SELECT strftime('%Y-%m', date(MAX(order_date), 'start of month', '-1 month'))
        FROM orders
      )
      GROUP BY p.product_name ORDER BY revenue DESC LIMIT 5;
    explanation: "统计上个月各产品销售额并取 Top5�?
    category: ranked_aggregation
    priority: 10

  - id: rule_002
    keywords: ["各城�?, "订单数量"]
    sql: |
      SELECT city, COUNT(*) AS order_count FROM orders
      GROUP BY city ORDER BY order_count DESC LIMIT 10;
    explanation: "按城市统计订单量并排序�?
    category: simple_lookup
    priority: 20
```

### 4.3 `RuleGenerator` 重构

```python
# sql/rule_generator.py
import yaml
from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class Rule:
    id: str
    keywords: tuple[str, ...]
    sql: str
    explanation: str
    category: str
    priority: int = 0

class RuleRegistry:
    def __init__(self, rules_dir: Path):
        self.rules: list[Rule] = []
        self._load_all(rules_dir)
    
    def _load_all(self, rules_dir: Path):
        for yaml_file in rules_dir.glob("**/*.yaml"):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            for r in data.get("rules", []):
                self.rules.append(Rule(
                    id=r["id"],
                    keywords=tuple(r["keywords"]),
                    sql=r["sql"],
                    explanation=r["explanation"],
                    category=r.get("category", "unknown"),
                    priority=r.get("priority", 0),
                ))
        # �?priority 降序排列，高优先级先匹配
        self.rules.sort(key=lambda r: -r.priority)
    
    def match(self, question: str) -> Rule | None:
        normalized = question.replace('�?, '?').strip()
        for rule in self.rules:
            if all(kw in normalized for kw in rule.keywords):
                return rule
        return None

    def match_by_classification(
        self,
        question: str,
        classification: QuestionClassification,
    ) -> Rule | None:
        """结合分类结果的增强匹�?""
        # 只在分类认为不需�?LLM 时才匹配 rule
        if classification.needs_llm:
            return None
        # 优先匹配同类别的规则
        candidates = [r for r in self.rules if r.category == classification.category]
        # fallback 到全量匹�?        candidates = candidates or self.rules
        normalized = question.replace('�?, '?').strip()
        for rule in candidates:
            if all(kw in normalized for kw in rule.keywords):
                return rule
        return None

class TemplateSqlSynthesizer:
    """从语义片段合�?SQL（本地语义映射，保留 try_template_sql 能力�?""
    
    SEMANTIC_MAPPINGS = {
        ("COUNT(*)", "城市"): ("SELECT city, COUNT(*) FROM orders GROUP BY city", "按城市统计数�?),
        ("SUM(revenue)", "产品", "�?"): ("...TOP 5...", "按产品销�?Top5"),
        # ... 其他映射
    }
    
    def try_synthesize(self, question: str) -> tuple[str, str] | None:
        ...
```

---

## 五、与 retrieval �?flow 的边�?
### 5.1 Generation 层输入输出接�?
**输入（来�?retrieval 层）�?*
```python
@dataclass(frozen=True)
class GenerationInput:
    question: str                                    # 原始用户问题
    schema_context: str                              # 来自 retrieval/schema_loader
    examples_context: str                             # 来自 retrieval（示�?SQL�?    classification: QuestionClassification           # 来自 NLU/nlu/classifier
    config: GenerationConfig                         # 超时、temperature �?```

**输出（交�?flow 层）�?*
```python
@dataclass(frozen=True)
class GenerationOutput:
    sql: str
    explanation: str
    mode: str              # "llm" | "rule" | "template"
    backend: str            # "lcel" | "vanna" | "rule_engine"
    latency_ms: float
    classification: QuestionClassification  # 回传�?flow 用于后续处理
    metadata: dict
```

### 5.2 retrieval 层接口（Generation 的视角）

当前问题：`retrieve_schema_context()` 直接返回 `str`，Generation 层无法知道检索质量（是否有召回文档、相似度分数）�?
**建议新增接口�?*
```python
@dataclass(frozen=True)
class RetrievalResult:
    documents: list[str]           # 检索到的文档内�?    scores: list[float]           # 相似度分数（用于判断检索质量）
    schema_text: str              # 最终拼接到 prompt �?schema 上下�?    source: str                   # "chroma" | "local" | "ddl"

class SchemaRetriever(Protocol):
    def retrieve(self, question: str, limit: int = 4) -> RetrievalResult:
        ...
```

Generation 层收�?`RetrievalResult` 后，可以�?- 如果 `scores` 普遍�?�?降低�?LLM 的置信度，提示使�?rule fallback
- 如果 `documents` 为空 �?使用 DDL fallback
- �?`source` 写入 metadata 用于可观测�?
---

## 六、对其他 subagent 提案的质�?
### 6.1 质疑 retrieval 层的 ChromaDB 硬编码问�?
当前 `retrieve_schema_context()` 使用 `chromadb.PersistentClient` 直接实例化。如�?retrieval agent 提案�?VectorStore 抽象出来，Generation �?*强烈要求**�?
- 不要仅抽�?`retrieve(question) -> str`，而要返回 `RetrievalResult`（含 scores�?- 因为 Generation 层需要根据检索质量决定是否降级到 rule path
- 如果 retrieval 层仅返回拼装好的字符串，Generation 层失去自适应能力

### 6.2 质疑 flow 层的单一日志输出

如果 flow orchestrator �?generation 输出统一包装为单一日志字符串（�?`"sql=..., explanation=..."`），将失去：
- `classification` 对象的流动价值（flow 后面的节点可能需�?category�?- `metadata` 的可观测性（latency breakdown、retrieval scores�?- �?generation 路径的对比评测能�?
**建议**：flow 层保�?`GenerationOutput` dataclass 形式传递，不要序列化为字符串�?
### 6.3 质疑 classification 作为独立节点

如果�?`classify_question` 设计�?flow 中独立的一�?step（与 retrieval 并行或顺序执行），则�?
- **必须缓存**：同一�?question 不应在同一请求中重复分�?- **必须传�?*：分类结果必须作�?`GenerationInput` 的一部分传给 Generation，而不是让 Generation 重新调用 `classify_question()`
- **建议**：classification 作为 `GenerationInput` 的一部分，由 flow 在路由阶段注入，不在 Generation 内部重复调用

---

## 七、迁移路径建�?
### Phase 1（最小侵入）：接口抽�?+ Rule YAML �?1. 定义 `SqlGenerator` Protocol
2. 新增 `RuleRegistry` �?YAML 加载规则
3. `RuleBasedGenerator` 实现 `SqlGenerator`
4. `SqlRouter` 作为 facade，对外仍暴露 `generate_sql()` 签名
5. 不改�?LLM path，向后兼�?
### Phase 2（LangChain Native）：
1. 新增 `LcelGenerator` 实现 `SqlGenerator`
2. 配置驱动选择 `LcelGenerator` �?`VannaGenerator`
3. Vanna path 标记�?deprecated

### Phase 3（清理）�?1. 移除 `generate_sql()` 中的 if/else 路由�?2. `client.py` 简化为 `SqlRouter().route().generate()`
3. ChromaDB VectorStore 替换�?LangChain VectorStore interface
---

### arch-agent-retrieval 分析结论

## 1. 当前 retrieval 的核心问�?
### 1.1 ChromaDB 硬编码的痛点

`schema_loader.py` 中有两处直接实例�?ChromaDB�?
```python
# load_schema_documents()
client = chromadb.PersistentClient(path=str(Path(settings.vector_db_path) / "schema_store"))
collection = client.get_collection("schema_docs")

# retrieve_schema_context()
client = chromadb.PersistentClient(path=str(Path(settings.vector_db_path) / "schema_store"))
result = collection.query(query_texts=[question], n_results=limit)
```

**痛点清单�?*| 痛点 | 描述 |
|------|------|
| **向量库强耦合** | 无法切换 FAISS/PGvector，每次换向量库要改代�?|
| **Embedding 模型不可�?* | ChromaDB 用的�?Vanna 内部封装�?embedding，无可控�?|
| **重复客户端实�?* | `load_schema_documents` �?`retrieve_schema_context` 各自创建 client，无连接复用 |
| **Vanna 二次索引** | `adapters.py` �?`LocalVanna` 继承�?`ChromaDB_VectorStore`，又单独建了一套索引，`train()` 调用频繁，且 train 数据没有 schema 边界（把 RULES/DDL/PROMPT 全塞进去）|
| **无法评测对比** | 没有抽象层就没有统一的评测基准，6 号需求（�?embedding 对比）无法落�?|

### 1.2 如何支持�?embedding 对比

�?embedding 对比需要两个维度正交化�?
1. **Embedding 模型**：bge、m3e、text-embedding-3-small �?2. **向量�?*：ChromaDB、FAISS、PGvector

每个组合都应能独立运行和评测。当前架构的问题在于 embedding 和向量库都在 ChromaDB 内部绑定，无法解耦�?
---

## 2. SchemaRetriever 接口设计

### 2.1 核心接口

```python
from typing import Protocol
from dataclasses import dataclass

@dataclass
class RetrievedChunk:
    content: str          # 文档文本
    score: float          # 相似度分�?    metadata: dict        # 原始 metadata（表名、字段名、来源等�?
class SchemaRetriever(Protocol):
    """Schema 检索的统一接口"""
    
    def retrieve(self, question: str, limit: int = 4) -> list[RetrievedChunk]:
        """同步检�?""        ...    
    def ingest(self, documents: list[dict]) -> None:
        """批量写入向量库（建索引）"""
        ...    
    def clear(self) -> None:
        """清空索引（测试用�?""        ...
```

### 2.2 多实现支�?
| 实现�?| 底层向量�?| Embedding 封装 |
|--------|-----------|---------------|
| `ChromaSchemaRetriever` | ChromaDB | LangChain `Embeddings` |
| `FAISSSchemaRetriever` | FAISS | LangChain `Embeddings` |
| `PGvectorSchemaRetriever` | PGvector (asyncpg) | LangChain `Embeddings` |
| `InMemorySchemaRetriever` | LangChain InMemoryVectorStore | LangChain `Embeddings`（测试用）|

所有实现都通过 **LangChain �?`Embeddings` 接口**注入 embedding 模型，而非自己调用 embedding API�?
```python
class ChromaSchemaRetriever:
    def __init__(self, embedding: Embeddings, persist_dir: str, collection: str):
        self._embedding = embedding
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection_name = collection
    
    def retrieve(self, question: str, limit: int = 4) -> list[RetrievedChunk]:
        # �?self._embedding.embed_query(question) 得到向量
        # 再用 ChromaDB similarity_search_with_score_by_vector
        ...
```

### 2.3 SchemaRetriever �?Vanna 的边�?
**关键问题：Vanna 自身维护了一�?ChromaDB 索引用于 few-shot RAG**

当前架构中，Vanna �?`train()` 实质上是�?DDL/rules/prompts 都往 ChromaDB 里塞。重构后应该�?
- **SchemaRetriever 只负�?schema context 检�?*（表结构、字段说明、DDL�?- **Vanna �?few-shot examples** 走另一套存储（可以是同一向量库，但通过 `namespace` �?`filter` 隔离�?- Vanna 不继�?`ChromaDB_VectorStore`，而是组合使用 `SchemaRetriever` + 自定�?example store

这样 embedding 模型可以统一，评测也公平�?
---

## 3. LangChain �?retrieval 的使用点

### 3.1 LangChain Embeddings 接口

LangChain �?`Embeddings` 接口是跨向量库统一的关键：

```python
from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceEmbeddings

# bge embedding（本地推理）
bge_embedding = HuggingFaceBgeEmbeddings(
    model_name="BAAI/bge-small-zh-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

# m3e embedding
m3e_embedding = HuggingFaceEmbeddings(
    model_name="moka-ai/m3e-base",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)
```

所�?`SchemaRetriever` 实现都接�?`Embeddings` 对象，实现真正的**嵌入模型可插�?*�?
### 3.2 LangChain VectorStore 封装

| LangChain 封装 | 用�?|
|---------------|------|
| `langchain_community.vectorstores.Chroma` | 替代直接�?chromadb，封装了 `add_texts`/`similarity_search` |
| `langchain_community.vectorstores.FAISS` | 内存向量库，适合本地评测 |
| `langchain_community.vectorstores.PGvector` | PGvector 异步封装 |
| `langchain_core.vectorstores.VectorStore` | 基类，`as_retriever()` 直接生成 `VectorStoreRetriever` |

**推荐方案�?*```python
from langchain_community.vectorstores import Chroma as LCChroma

class ChromaSchemaRetriever:
    def __init__(self, embedding: Embeddings, persist_dir: str):
        self._store = LCChroma(
            embedding_function=embedding,  # LangChain 统一 embedding
            persist_directory=persist_dir,
            collection_name="schema_docs"
        )    
    def retrieve(self, question: str, limit: int = 4) -> list[RetrievedChunk]:
        results = self._store.similarity_search_with_score(question, k=limit)
        return [RetrievedChunk(content=doc.page_content, score=score, metadata=doc.metadata) for doc, score in results]
```

这样 LangChain 作为中间层，VectorStore �?Embeddings 的兼容性由 LangChain 维护�?
### 3.3 �?Generation �?LCEL Chain 的关�?
Generation agent �?LCEL chain 中的 `VectorStoreRetriever` 应该**直接�?`SchemaRetriever`** 而不是自己创�?store�?
```python
# Generation 层的 LCEL chain
retriever = schema_retriever.as_retriever()  # SchemaRetriever implements VectorStore
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | SQL_GENERATION_PROMPT
    | llm
    | StrOutputParser()
)
```

前提�?`SchemaRetriever` 实现 `langchain_core.vectorstores.VectorStore` 接口（通过委托实现）�?
---

## 4. 评测脚本设计

### 4.1 核心数据结构

```python
@dataclass
class RetrievalResult:
    question: str
    retrieved_chunks: list[RetrievedChunk]
    ground_truth_chunks: list[str]  # 人工标注或规则生成的 golden chunks

@dataclass
class EvalMetrics:
    recall_at_k: float      # top-k 召回�?    mrr: float              # 平均倒数排名
    precision_at_k: float   # top-k 精确�?    ndcg_at_k: float        # normalized DCG

@dataclass
class RetrieverConfig:
    retriever_type: str           # "chromadb" | "faiss" | "pgvector"
    embedding_type: str           # "bge" | "m3e" | "openai" | "text-embedding-3-small"
    embedding_model_path: str     # HuggingFace 模型路径�?API 配置
    top_k: int = 4
```

### 4.2 核心接口

```python
class RetrievalEvaluator:
    def __init__(self, dataset: list[RetrievalResult]):
        self.dataset = dataset
    
    def evaluate(self, retriever: SchemaRetriever) -> EvalMetrics:
        """对单一 retriever 配置跑评�?""        ...    
    def evaluate_cross_config(
        self, 
        configs: list[RetrieverConfig]
    ) -> dict[RetrieverConfig, EvalMetrics]:
        """多配置横向对比评测，返回 {config: metrics}"""
        ...
```

### 4.3 评测数据集格�?
```yaml
# data/eval/retrieval_benchmark.yaml
- question: "上个月销售额最高的�?个产品是什�?
  ground_truth_tables: ["products", "order_items", "orders"]
  ground_truth_fields: ["product_name", "quantity", "unit_price"]
  
- question: "华东区域的订单总量"
  ground_truth_tables: ["orders"]
  ground_truth_fields: ["region", "total_amount"]
```

### 4.4 评测指标选择理由

- **Recall@K**：Text2SQL 重点�?�?字段有没有被召回"，召回率比精确率更重�?- **MRR**：排名质量，�?SQL 生成正确性有直接影响
- **NDCG@K**：综合考虑相关性和排名位置

---

## 5. 对其�?subagent 提案的质疑（�?retrieval 视角�?
### 5.1 �?Generation/LangChain agent 的质�?
**质疑点：Vanna �?SQL generation �?RAG 边界是否清晰�?*当前 `adapters.py` �?`generate_sql()` 做了两件事：
1. �?`retrieve_schema_context()` 获取 schema context
2. �?context 塞进 Vanna �?prompt 让它生成 SQL

如果 generation agent 想用 LCEL 链式生成，retrieval 的输出应该已经是结构化的 `list[RetrievedChunk]`，而不是字符串拼接后的 prompt。如�?generation agent �?retrieval 集成到自�?LCEL chain 里，是否会绕�?`retrieve_schema_context()` 导致两套 retrieval 并存�?
**建议**：明�?retrieval 只负�?�?，generation 只负�?生成"，中间用 `list[RetrievedChunk]` �?`SchemaContext` 对象传递，不要用字符串拼接�?
### 5.2 �?Rules/Extensibility agent 的质�?
**质疑点：Rule �?Schema 的索引是否需要分离？**`generator.py` 中的 RULES 是一个扁平的 list，`train(question=question, sql=rule.sql)` �?question �?sql 作为 pair 存入 Vanna �?ChromaDB。Rules 的索引和 Schema 的索引是否应该合并？

**建议**：rules 作为"意图→SQL"的映射，推荐走独立的 `RuleStore`（可以是 dict/YAML，也可以是单独的向量索引），�?`SchemaRetriever` 完全隔离。这�?retrieval 评测时不会受 rules 污染，也避免 Vanna 内部同时操作两套索引导致的语义混乱�?
### 5.3 �?Flow/Orchestration agent 的质�?
**质疑点：`classify_question()` 结果应该�?retrieval 之前还是之后使用�?*Generation agent 的提案提�?`QuestionClassification` 应该作为 `GenerationInput` 的一部分。但 retrieval 层也可以利用 `category` 来调整检索策略（例如 `simple_lookup` 类问题可能不需要召回太多示例）�?
**建议**：retrieval 层接�?`question` 和可选的 `classification` 两个参数。当 `classification` 存在�?`category == 'simple_lookup'` 时，可以跳过向量检索直接走 DDL fallback，减少不必要的向量查询开销�?
---

## 6. 架构建议总结

```
retrieval/
├── __init__.py              # 导出 SchemaRetriever, RetrievedChunk
├── base.py                  # SchemaRetriever Protocol + RetrievedChunk dataclass
├── chroma_retriever.py      # ChromaDB 实现（LangChain 封装�?├── faiss_retriever.py       # FAISS 实现
├── pgvector_retriever.py    # PGvector 实现（async�?├── factory.py               # RetrieverFactory.from_config(config)
└── evaluator.py             # RetrievalEvaluator, EvalMetrics

scripts/
└── eval_retrieval.py        # 评测入口
```

**LangChain 定位**：Embeddings �?VectorStore 封装�?LangChain 提供，项目代码只依赖 LangChain 接口，不直接依赖 ChromaDB/FAISS 客户�?API�?

---

## 六、Extensibility & Rules 分析结论（arch-agent-extensibility�?
### 1. Provider 扩展 OCP 问题

**当前 if-elif 链位置：**

| 文件 | 函数 | 当前数量 | 新增 Provider 需�?|
|------|------|---------|-------------------|
| client.py | get_llm_adapter() | 2 个（bailian_code_plan, openai_compatible�?| 改此文件 |
| settings.py | get_provider_config() | 3 个（bailian_code_plan, openai_compatible, astron�?| 改此文件 |
| dapters.py | import + 类定�?| 2 �?adapter �?| 改此文件 |

**结论：当前需要改 3 个文件才能新�?1 �?Provider，违�?OCP�?*

**额外发现�?* settings.py �?get_provider_config() 已经写了 stron 分支，但 client.py �?get_llm_adapter() 完全没有处理 stron——这是个隐藏 bug，astron 配置存在但不可用�?
---

### 2. ProviderRegistry 设计

**推荐方案：@register 装饰�?*`python
# app/core/llm/registry.py
class LLMProviderRegistry:
    _providers: dict[str, type["LLMAdapter"]] = {}
    
    @classmethod
    def register(cls, name: str):
        def decorator(adapter_cls):
            cls._providers[name] = adapter_cls
            return adapter_cls
        return decorator
    
    @classmethod
    def create(cls, name: str, config) -> "LLMAdapter":
        if name not in cls._providers:
            raise ValueError(f"Unknown provider: {name}. Available: {list(cls._providers.keys())}")
        return cls._providers[name](config=config)
` `python
# adapters.py - 每个 adapter �?@register 装饰�?@LLMProviderRegistry.register("bailian_code_plan")
class BailianCodePlanAdapter(OpenAICompatibleAdapter):
    ...

@LLMProviderRegistry.register("astron")
class AstronAdapter(OpenAICompatibleAdapter):  # 新增一行即�?    ...
` `python
# client.py - 改造后（零 if-elif�?def get_llm_adapter() -> LLMAdapter:
    settings = get_settings()
    return LLMProviderRegistry.create(settings.get_provider_config().provider, settings.get_provider_config())
`

**效果：新�?Provider 只需�?adapters.py �?1 个类 + @register，client.py/settings.py 零改动�?*

---

### 3. 规则 YAML �?
**RuleStore 结构�?*`python
@dataclass(frozen=True)
class Rule:
    keywords: tuple[str, ...]
    sql: str
    explanation: str
    priority: int = 0    # 数值越大优先级越高
    tags: tuple[str, ...] = ()

class RuleStore:
    def match(self, question: str) -> Optional[Rule]: ...
    def match_with_classification(self, question: str, classification) -> Optional[Rule]: ...
```

---

## 第二轮收敛结论

### 分歧 1：Retrieval 返回类型
**结论：`list[RetrievedChunk]`（与 Retrieval agent 定义一致），Generation LCEL chain 通过 `SchemaRetriever.as_retriever()` 接入。**

**详细：**
- 返回类型采用 Retrieval agent 定义的 `list[RetrievedChunk]`（含 content/score/metadata），而非 Generation agent 提出的 `RetrievalResult`/`SchemaContext`——两者语义等价，但 `RetrievedChunk` 更简洁，与 LangChain VectorStore 接口一致。
- Generation 层 LCEL chain **必须通过** `SchemaRetriever.as_retriever()` 获得 `VectorStoreRetriever`，不允许在 Generation 内部自己实例化 VectorStore/Embedding 来做 retrieval。这样保证：`(1)` 复用同一套 retrieval pipeline，`(2)` 评测口径统一，`(3)` 避免 ChromaDB 被实例化两次。
- 如果 `scores` 普遍低（如平均 < 0.6），Generation 层可根据配置降级到 rule fallback，这是 Generation 层的责任而非 retrieval 层的责任。

### 分歧 2：Vanna 策略
**结论：标记 deprecated（暂不删除），与 SchemaRetriever 边界明确：无自己专属索引，走同一套 SchemaRetriever + 独立 ExampleStore。**

**详细：**
- Vanna 生成路径标记 `@deprecated`，目标架构是 LCEL Native。
- Vanna **不再维护自己的 ChromaDB 索引**。`train()` 方法在 deprecated 路径下仅用于追加 few-shot examples，这些 examples 走独立的 ExampleStore（可用同一 ChromaDB 实例，但通过 `namespace` 或 `collection` 隔离）。
- SchemaRetriever 负责 schema context（RULES/DDL 的结构化说明），ExampleStore 负责 few-shot (question, sql) pairs。两者正交。
- 等 LCEL Native 路径稳定后，完全移除 Vanna。

### 分歧 3：LCEL Chain 集成
**结论：Generation 层 LCEL chain 的 retrieval step 必须调用 `SchemaRetriever.as_retriever()`，不允许自己集成 VectorStoreRetriever。**

**详细：**
- Generation LCEL chain 应为：
  ```python
  retriever = schema_retriever.as_retriever()  # SchemaRetriever → VectorStoreRetriever
  rag_chain = (
      {"context": retriever, "question": RunnablePassthrough()}
      | SQL_GENERATION_PROMPT
      | llm
      | StrOutputParser()
  )
  ```
- Generation 层**不直接依赖** ChromaDB/FAISS/PGvector 客户端 API，只依赖 `SchemaRetriever` 接口。
- 这意味着 `SchemaRetriever` 必须实现 `langchain_core.vectorstores.VectorStore` 接口（或至少提供 `.as_retriever()` 方法返回 `VectorStoreRetriever`）。

### 分歧 4：PipelineOrchestrator Phase1
**结论：Phase1 = `PipelineState` dataclass 提取 + FlowFacade 简化，对象引用传递（不序列化）。**

**Phase1 具体内容：**
1. **提取 `PipelineState` dataclass**（所有中间数据打包）：
   ```python
   @dataclass(frozen=True)
   class PipelineState:
       question: str
       classification: Optional[QuestionClassification]
       retrieval_result: Optional[list[RetrievedChunk]]  # 新增，Phase2 前为 None
       schema_context: Optional[str]
       generation_output: Optional[GenerationOutput]
       config: PipelineConfig
       timestamps: dict[str, float]  # 各项操作的 wall time
   ```
2. **FlowFacade 改造**：`client.py` 的 `generate_sql()` 拆为一个 orchestrator 函数，接收 `PipelineState`，逐步填充各字段，`PipelineState` 在节点间以引用形式传递（不 JSON 序列化）。
3. **`SqlRouter` 引入**：Phase1 末引入 `SqlRouter`，替换硬编码 if/else 链，作为 Phase2 Orchestrator 类的雏形。

**不采用 Generation agent 方案的理由：** Generation agent 主张 `GenerationOutput` 直接传递不需要 `PipelineState`，但这只在单节点场景下成立。当 flow 有多个处理节点（classification → retrieval → generation → explanation）时，需要一个承载中间状态的结构。Phase1 提取 `PipelineState` 是最小侵入的过渡方案，后续可以演进为 Phase2 的正式 Orchestrator 类。

### 分歧 5：DB 层
**结论：确认废弃 `database.py`，统一走 `db_abstraction.py`。不需要额外 `IDatabaseStrategy` 抽象层。**

**详细：**
- `db_abstraction.py` 已有 `DatabaseConnector(ABC)` 作为 interface，是足够的抽象。
- `DatabaseManager` 已是工厂+单例，connectors/ 子类是良好的策略模式实现。
- `database.py` 废弃，迁入工作：`(1)` grep 确认所有 `database.py` 的调用点，`(2)` 迁移至 `db_abstraction.py` 的等效接口，`(3)` 删除 `database.py`。
- **无需** 引入 `IDatabaseStrategy`——这是过度设计，已有的 ABC 接口已够用。

---
_第二论收敛完成：2026-04-14 23:49_

---

## 第二轮收敛结论（Extensibility 视角）

### 1. DB 层最终结论
**结论：确认废弃 `database.py`，统一走 `db_abstraction.py`。无需额外 `IDatabaseStrategy` 抽象层。**

**理由：**
- `db_abstraction.py` 已有 `DatabaseConnector(ABC)` 作为 interface，足够覆盖所有场景。connectors/ 子类（sqlite.py、mysql.py、postgresql.py）已实现良好的策略模式。
- `database.py` 的 `DatabaseConfig` 是简化版（无 enum、无 `from_url`、无 `DatabaseType`），与 `db_abstraction.py` 的 `DatabaseConfig` 功能重叠。两套并存是历史遗留，不值得维护两份。
- `IDatabaseStrategy` 是过度设计：已有 ABC interface + DatabaseManager 工厂，不需要第三层抽象。
- **迁移步骤**：`grep -r "from app.core.sql.database"` 确认调用点 → 替换为 `db_abstraction` 接口 → 删除 database.py。

---

### 2. ProviderRegistry 与 Generation 接口契约
**结论：`SqlGenerator` 作为 `@runtime_checkable Protocol`，`generate()` 必须接收 `QuestionClassification` 参数。契约通过 Protocol + 工厂模式共同保证。**

**详细设计：**

```python
@runtime_checkable
class SqlGenerator(Protocol):
    @property
    def name(self) -> str: ...

    def supports(self, classification: QuestionClassification) -> bool:
        """供 SqlRouter 路由决策调用"""

    def generate(
        self,
        question: str,
        schema_context: str,          # 来自 retrieval 层
        classification: QuestionClassification,  # 必须接收，用于路由决策
    ) -> GenerationResult: ...
```

**契约保证机制（两层）：**
1. **Protocol `@runtime_checkable`**：运行时 `isinstance(gen, SqlGenerator)` 会检查 `generate` 方法签名，类型检查器（mypy/pyright）也能在开发期捕获签名不匹配。
2. **`ProviderRegistry` 工厂**：新增 Generator 实现必须用 `@LLMProviderRegistry.register(name)` 装饰注册，工厂在创建时做接口兼容性检查。**不通过 Registry 创建的实现，视为非标准实现，不保证兼容性。**

**SqlRouter 路由逻辑：**
```python
class SqlRouter:
    def route(self, question: str, classification: QuestionClassification) -> SqlGenerator:
        for gen in self.generators:
            if gen.supports(classification):
                return gen
        return self.generators[-1]  # fallback to default LLM generator
```

**禁止事项：**
- `SqlGenerator.generate()` **禁止**忽略 `classification` 参数——这会使路由决策和生成策略脱节。
- Generation 层**禁止**在内部重复调用 `classify_question()`——分类由 flow 层注入，Generation 只负责生成。

---

### 3. Rules 与 Retrieval 隔离策略
**结论：RuleStore 的 examples（question-sql pairs）和 SchemaRetriever 的向量库共用 ChromaDB 实例，但通过 `collection` 隔离。禁止共用同一 collection。**

**架构设计：**

```
ChromaDB (同一 PersistentClient)
├── collection="schema_docs"   → SchemaRetriever 专用
└── collection="rule_examples" → RuleStore (Vanna/trian) 专用
```

**RuleStore 职责：**
- 存储 `(question_keywords, sql)` pairs，用于 rule-based fallback 和 few-shot提示。
- **不参与** retrieval 评测：评测时只查询 `schema_docs` collection，rule_examples 的数据不会污染 recall/mrr 指标。
- 实现方式：`RuleStore` 可选择是否使用向量索引（`namespace="rule_examples"`），也可以用纯 dict/YAML 存储（关键字匹配 + priority 排序）。

**与 Vanna 的边界（分歧 2 相关）：**
- Vanna deprecated 路径下，`vn.train(question, sql)` 数据存入 `rule_examples` collection。
- LCEL Native 路径下，RuleStore 直接提供 `match_with_classification()`，不经过 Vanna。

**评测隔离保证：**
- `RetrievalEvaluator` 只对 `schema_docs` collection 打分。
- `RuleStore` 的 examples 不出现在 retrieval 评测的 ground truth 中。

---

### 4. Vanna Provider 注册策略
**结论：Vanna **必须** 在 `ProviderRegistry` 中注册（用于 backward compatibility），但注册名为 `"vanna_deprecated"`，标注废弃语义。**

**具体方案：**

```python
@LLMProviderRegistry.register("vanna_deprecated")
class VannaGenerator:
    """Deprecated: 保留用于向后兼容，最终将被 LcelGenerator 替代"""
    name = "vanna_deprecated"

    def supports(self, c: QuestionClassification) -> bool:
        # Vanna 只在 classification.needs_llm == True 时被路由到
        # 且无更特定的 LLM generator 时作为 fallback
        return c.needs_llm and not self._has_better_option(c)

    def generate(self, question, schema_context, classification) -> GenerationResult:
        warnings.warn("VannaGenerator is deprecated, use LcelGenerator", DeprecationWarning, stacklevel=2)
        ...
```

**与 LCEL Generator 的优先级：**
```
SqlRouter.route(classification) 遍历 generators:
  1. RuleBasedGenerator   (category=simple_lookup/ranked_aggregation, needs_llm=False)
  2. LcelGenerator        (needs_llm=True, 有更优 prompt 控制能力)
  3. VannaGenerator      (needs_llm=True, 兜底，标注 deprecated)
```

**为何必须注册：**
- 当前 production 环境依赖 Vanna path，直接删除会导致链路断裂。
- 通过 Registry 注册 + deprecation warning，可以在切换到 LCEL Native 后逐步灰度下线。
- 注册名用 `"vanna_deprecated"` 而非 `"vanna"`，强制所有调用方意识到废弃状态。

---
_Extensibility 视角收敛完成：2026-04-14 23:49_