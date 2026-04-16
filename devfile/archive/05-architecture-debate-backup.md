### 鎻愭 C锛氭ā鍧楀寲鍗曚綋锛圡odular Monolith锛?
---

#### 涓€銆佺幇鐘堕棶棰樿瘖鏂?
| # | 闂 | 鏍瑰洜 |
|---|------|------|
| 1 | `generate_sql()` 娣峰悎 7 绉嶈亴璐?| 鎵€鏈夐€昏緫鍫嗗湪涓€涓嚱鏁帮紝鏃犳ā鍧楄竟鐣?|
| 2 | classifier 浠呯敤 `needs_llm`锛屽叾浣欏瓧娈典涪寮?| 鍒嗙被缁撴灉鏈疮绌垮叏娴佺▼ |
| 3 | 瑙勫垯纭紪鐮?27 鏉★紝鏃犳硶杩愯鏃跺鍒?| 瑙勫垯涓庝唬鐮佽€﹀悎 |
| 4 | 涓ゅ DB 鎶借薄灞傚苟琛?| 妯″潡杈圭晫瀹氫箟妯＄硦锛岀淮鎶よ€呭悇鑷疄鐜颁簡涓€濂?|
| 5 | UI 缁曡繃 API | 妯″潡闂磋皟鐢ㄦ湭瀹氫箟瑙勫垯锛孶I 鐩存帴瀵煎叆涓氬姟妯″潡 |
| 6 | `ask_question()` 缂栨帓 + 鎵ц娣峰悎 | `orchestrator` 妯″潡鏃㈠仛缂栨帓鍙堝仛鎵ц锛岃亴璐ｈ繃杞?|

**鏍稿績娲炲療锛?* 褰撳墠浠ｇ爜涓嶆槸"缂哄皯鍒嗗眰"锛岃€屾槸**缂哄皯妯″潡鍖?*鈥斺€旀瘡涓ā鍧楀唴閮ㄧ殑鑱岃矗瀹氫箟涓嶆竻鏅帮紝妯″潡闂存病鏈夐€氫俊瑙勮寖锛屽鑷磋法妯″潡鐩存帴璋冪敤妯锛圲I鈫抪ipeline鈫抔enerate_sql鈫抋dapter锛夈€?
**妯″潡鍖栧崟浣?*鐨勬牳蹇冩€濊矾锛?*鎸変笟鍔¤兘鍔涘垝鍒嗘ā鍧楋紝妯″潡鍐呴珮鍐呰仛銆佹ā鍧楅棿浣庤€﹀悎**锛岃€岄潪杩芥眰涓ユ牸鐨勫眰娆′緷璧栥€傞€傚悎 2-5 浜虹淮鎶ょ殑灏忓洟闃燂紝涓嶉渶瑕?Clean Architecture 閭ｄ箞閲嶇殑鎶借薄鎴愭湰銆?
---

#### 浜屻€佹ā鍧楃粨鏋勶紙鏂囨湰鏍戝舰鍥撅級

```
text2sql-0412/
鈹?鈹溾攢鈹€ app/
鈹?  鈹?鈹?  鈹溾攢鈹€ query/                         # ====== 鏌ヨ澶勭悊妯″潡锛堟牳蹇冿級======
鈹?  鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹?  鈹溾攢鈹€ ask.py                     # 銆愬叆鍙ｃ€慳sk_question() 鈫?鏈€缁?AskResult
鈹?  鈹?  鈹溾攢鈹€ routes.py                  # FastAPI /ask 璺敱锛堣皟鐢?ask.py锛?鈹?  鈹?  鈹溾攢鈹€ classifiers/
鈹?  鈹?  鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹?  鈹?  鈹溾攢鈹€ base.py               # QuestionClassifier锛堟帴鍙ｏ級
鈹?  鈹?  鈹?  鈹斺攢鈹€ rule_based_classifier.py  # 鐜版湁 question_classifier.py 閲嶅懡鍚?灏佽
鈹?  鈹?  鈹溾攢鈹€ generators/
鈹?  鈹?  鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹?  鈹?  鈹溾攢鈹€ base.py               # SqlGenerator锛堟帴鍙ｏ級
鈹?  鈹?  鈹?  鈹溾攢鈹€ llm_generator.py       # LLM 鐢熸垚锛堣皟鐢?adapter锛?鈹?  鈹?  鈹?  鈹斺攢鈹€ rule_generator.py     # 瑙勫垯鐢熸垚锛圷AML 椹卞姩锛?鈹?  鈹?  鈹溾攢鈹€ retrieval/
鈹?  鈹?  鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹?  鈹?  鈹溾攢鈹€ schema_retriever.py   # retrieve_schema_context()
鈹?  鈹?  鈹?  鈹斺攢鈹€ local_semantics.py    # extract_metric_alias() 绛?鈹?  鈹?  鈹溾攢鈹€ executors/
鈹?  鈹?  鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹?  鈹?  鈹溾攢鈹€ query_executor.py     # run_query()锛堝畨鍏ㄦ牎楠?+ 鎵ц锛?鈹?  鈹?  鈹?  鈹斺攢鈹€ db_pool.py           # 鏁版嵁搴撹繛鎺ョ鐞嗭紙缁熶竴 database.py锛?鈹?  鈹?  鈹斺攢鈹€ charts/
鈹?  鈹?      鈹溾攢鈹€ __init__.py
鈹?  鈹?      鈹溾攢鈹€ recommender.py        # ChartRecommender锛堢幇鏈夛級
鈹?  鈹?      鈹斺攢鈹€ type_analyzer.py      # DataTypeAnalyzer锛堢幇鏈夛級
鈹?  鈹?鈹?  鈹溾攢鈹€ auth/                          # ====== 璁よ瘉鎺堟潈妯″潡 ======
鈹?  鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹?  鈹溾攢鈹€ api_key.py                # API Key 璁よ瘉
鈹?  鈹?  鈹溾攢鈹€ middleware.py             # 璁よ瘉涓棿浠?鈹?  鈹?  鈹斺攢鈹€ permission.py             # 琛ㄧ骇鏉冮檺鎺у埗
鈹?  鈹?鈹?  鈹溾攢鈹€ config/                        # ====== 閰嶇疆妯″潡 ======
鈹?  鈹?  鈹溾攢鈹€ settings.py               # Settings锛堢幇鏈夛級
鈹?  鈹?  鈹斺攢鈹€ providers.py              # LLM Provider 閰嶇疆锛堜粠 settings 鎷嗗垎锛?鈹?  鈹?鈹?  鈹溾攢鈹€ llm/                           # ====== LLM 妯″潡 ======
鈹?  鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹?  鈹溾攢鈹€ adapters.py              # 閫傞厤鍣紙鐜版湁锛岄噸鏋勪负绛栫暐娉ㄥ唽锛?鈹?  鈹?  鈹溾攢鈹€ factory.py               # 銆愭柊澧炪€慙LM 閫傞厤鍣ㄥ伐鍘傦紙绛栫暐娉ㄥ唽琛級
鈹?  鈹?  鈹溾攢鈹€ health_check.py          # LLM 鍋ュ悍妫€鏌?鈹?  鈹?  鈹斺攢鈹€ prompts.py               # Prompt 鏋勫缓
鈹?  鈹?鈹?  鈹溾攢鈹€ rules/                         # ====== 瑙勫垯妯″潡锛堢嫭绔嬶級======
鈹?  鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹?  鈹溾攢鈹€ store.py                 # RuleStore锛圷AML 鍔犺浇锛岀儹鏇存柊锛?鈹?  鈹?  鈹溾攢鈹€ matcher.py              # RuleMatcher锛堝尮閰嶉€昏緫锛?鈹?  鈹?  鈹斺攢鈹€ default_rules.yaml       # 榛樿瑙勫垯锛堟浛浠?RULES 纭紪鐮侊級
鈹?  鈹?鈹?  鈹溾攢鈹€ ui/                            # ====== UI 妯″潡 ======
鈹?  鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹?  鈹斺攢鈹€ streamlit_app.py         # 銆愰噸鏋勩€戦€氳繃 HTTP 璋冪敤 /ask
鈹?  鈹?鈹?  鈹溾攢鈹€ shared/                        # ====== 鍏变韩妯″潡 ======
鈹?  鈹?  鈹溾攢鈹€ schemas.py               # Pydantic 妯″瀷
鈹?  鈹?  鈹溾攢鈹€ errors.py               # 閿欒瀹氫箟锛坮egister_error_handlers 闇€璋冪敤锛?鈹?  鈹?  鈹斺攢鈹€ metrics.py             # 鍙娴嬫€?鈹?  鈹?鈹?  鈹斺攢鈹€ api/                          # ====== API 鍩虹妯″潡 ======
鈹?      鈹溾攢鈹€ main.py                  # FastAPI 鍏ュ彛锛堟敞鍐屼腑闂翠欢锛?鈹?      鈹斺攢鈹€ routes/                  # 璺敱鎷嗗垎
鈹?鈹溾攢鈹€ data/
鈹?  鈹斺攢鈹€ rules/
鈹?      鈹斺攢鈹€ default_rules.yaml       # 瑙勫垯閰嶇疆
鈹?鈹斺攢鈹€ devfile/
```

---

#### 涓夈€佹瘡妯″潡鑱岃矗瀹氫箟

| 妯″潡 | 鑱岃矗 | 杈圭晫锛堝仛浠€涔?涓嶅仛浠€涔堬級|
|------|------|---------------------|
| **query** | 澶勭悊瀹屾暣鏌ヨ閾捐矾锛氬垎绫烩啋妫€绱⑩啋鐢熸垚鈫掓墽琛屸啋鍥捐〃 | 鉁?鍋氾細瀹屾暣涓氬姟娴佺▼缂栨帓<br>鉂?涓嶅仛锛氱洿鎺ユ搷浣滄暟鎹簱杩炴帴銆佷笉鍋氳璇?|
| **query/classifiers** | 闂鍒嗙被 | 鉁?鍙仛鍒嗙被鍒ゆ柇<br>鉂?涓嶅仛 SQL 鐢熸垚銆佷笉鍋?LLM 璋冪敤 |
| **query/generators** | SQL 鐢熸垚锛圠LM 鎴栬鍒欙級 | 鉁?鍙牴鎹?question + schema 鐢熸垚 SQL<br>鉂?涓嶅仛鎵ц銆佷笉鍋氭牎楠?|
| **query/retrieval** | Schema 妫€绱?| 鉁?鍙繑鍥?schema context<br>鉂?涓嶅仛 SQL 鐢熸垚銆佷笉鍋氬垎绫?|
| **query/executors** | SQL 鎵ц + 瀹夊叏鏍￠獙 | 鉁?鍙墽琛?SELECT銆佹牎楠屽畨鍏ㄦ€?br>鉂?涓嶅仛 SQL 鐢熸垚銆佷笉鍋氬垎绫?|
| **query/charts** | 鍥捐〃鎺ㄨ崘 | 鉁?鍙帹鑽愬浘琛ㄧ被鍨?br>鉂?涓嶅仛 SQL 鐢熸垚銆佷笉鍋氭墽琛?|
| **auth** | 璁よ瘉 + 琛ㄧ骇鏉冮檺 | 鉁?鍙仛韬唤鏍￠獙鍜屾潈闄愬垽鏂?br>鉂?涓嶅仛涓氬姟閫昏緫 |
| **llm** | LLM 璋冪敤灏佽 | 鉁?鍙仛 LLM API 璋冪敤<br>鉂?涓嶅仛 SQL 鎵ц銆佷笉鍋氳鍒欏尮閰?|
| **rules** | 瑙勫垯瀛樺偍 + 鍖归厤 | 鉁?鍙尮閰嶈鍒欒繑鍥?SQL 妯℃澘<br>鉂?涓嶅仛 LLM 璋冪敤銆佷笉鍋氭墽琛?|
| **config** | 閰嶇疆璇诲彇 | 鉁?鍙彁渚涢厤缃€?br>鉂?涓嶅仛涓氬姟閫昏緫 |
| **shared** | 鍏变韩绫诲瀷 + 宸ュ叿 | 鉁?璺ㄦā鍧楀叡浜殑鏁版嵁妯″瀷鍜屽伐鍏?br>鉂?涓嶅仛鍏蜂綋涓氬姟 |
| **ui** | 鐢ㄦ埛鐣岄潰 | 鉁?鍙仛灞曠ず鍜岀敤鎴蜂氦浜?br>鉂?涓嶇洿鎺ヨ皟鐢ㄤ笟鍔℃ā鍧楋紙璧?HTTP锛?|

**妯″潡闂撮€氫俊瑙勫垯锛?*
- 妯″潡闂磋皟鐢ㄥ繀椤婚€氳繃**妯″潡 public 鎺ュ彛**锛坄__init__.py` 瀵煎嚭锛夛紝涓嶅厑璁哥洿鎺?import 鍐呴儴鏂囦欢
- `query` 妯″潡鏄牳蹇冿紝鍏朵粬妯″潡锛坅uth/llm/rules锛変綔涓轰緷璧栬 query 璋冪敤
- UI 鍙兘閫氳繃 HTTP 璋冪敤 `query/routes.py`锛岀姝㈢洿鎺?import `query/ask.py`

---

#### 鍥涖€佸叧閿枃浠堕噸鏋勬柟妗?
##### 4.1 `generate_sql()` 鈫?`query/generators/`

**鐜扮姸锛?*
```python
# client.py:generate_sql() 涓€涓嚱鏁?7 绉嶈亴璐?```

**鐩爣锛氭媶鍒嗕负 query/generators/ 涓嬬殑涓や釜鐢熸垚鍣?*
```python
# query/generators/base.py
class SqlGenerator(Protocol):
    def generate(self, question: str, ctx: "GenerationContext") -> "SqlResult": ...

# query/generators/llm_generator.py
class LlmSqlGenerator(SqlGenerator):
    def __init__(self, adapter_factory: LLMFactory):
        self._factory = adapter_factory
    
    def generate(self, question: str, ctx: "GenerationContext") -> "SqlResult":
        adapter = self._factory.get_adapter()
        sql = adapter.generate_sql(question, ctx.schema_context)
        return SqlResult(sql=sql, mode=adapter.provider_name)

# query/generators/rule_generator.py
class RuleSqlGenerator(SqlGenerator):
    def __init__(self, rule_store: RuleStore):
        self._store = rule_store
    
    def generate(self, question: str, ctx: "GenerationContext") -> "SqlResult":
        rule = self._store.find_match(question)
        return SqlResult(sql=rule.sql, mode="fallback", explanation=rule.explanation)
```

##### 4.2 `ask_question()` 鈫?`query/ask.py`

**鐜扮姸锛?*
```python
# pipeline.py:ask_question() = generate_sql + run_query + 鍩嬬偣
```

**鐩爣锛?*
```python
# query/ask.py
class QueryService:
    def __init__(
        self,
        classifier: QuestionClassifier,
        generators: list[SqlGenerator],  # [llm_generator, rule_generator]
        retriever: SchemaRetriever,
        executor: QueryExecutor,
        chart_recommender: ChartRecommender,
    ):
        self._classifier = classifier
        self._generators = generators
        self._retriever = retriever
        self._executor = executor
        self._chart = chart_recommender
    
    def ask(self, question: str) -> AskResult:
        # 1. 鍒嗙被
        classification = self._classifier.classify(question)
        ctx = GenerationContext(question=question, classification=classification)
        
        # 2. 妫€绱?        if classification.needs_llm:
            ctx.schema_context = self._retriever.retrieve(question)
        
        # 3. 鐢熸垚锛堢瓥鐣ユā寮忥紝浼樺厛瑙勫垯锛屽啀 LLM锛?        for gen in self._generators:
            if gen.supports(classification):
                result = gen.generate(question, ctx)
                if result.sql:
                    break
        
        # 4. 鎵ц
        df = self._executor.execute(result.sql)
        
        # 5. 鍥捐〃
        chart = self._chart.recommend(df, question)
        
        return AskResult(result.sql, result.mode, df, chart)
```

##### 4.3 瑙勫垯纭紪鐮?鈫?`rules/store.py` + YAML

**鐜扮姸锛?* `RULES = [Rule(...), ...]` 纭紪鐮佸湪 generator.py

**鐩爣锛?*
```python
# rules/store.py
class RuleStore:
    def __init__(self, yaml_path: str):
        self._yaml_path = yaml_path
        self._rules: list[Rule] = []
        self._load()
    
    def _load(self):
        with open(self._yaml_path) as f:
            data = yaml.safe_load(f)
        self._rules = [Rule(**r) for r in data["rules"]]
    
    def find_match(self, question: str) -> Rule | None:
        normalized = question.replace('锛?, '').strip()
        for rule in self._rules:
            if all(kw in normalized for kw in rule.keywords):
                return rule
        return None
    
    def reload(self):
        """鐑洿鏂?""
        self._load()
```

```yaml
# data/rules/default_rules.yaml
rules:
  - keywords: ["涓婁釜鏈?, "鍓?", "浜у搧", "閿€鍞"]
    sql: "SELECT p.product_name, ..."
    explanation: "缁熻涓婁釜鏈堝悇浜у搧閿€鍞骞跺彇 Top5銆?
  - keywords: ["鍚勫煄甯?, "璁㈠崟鏁伴噺"]
    sql: "SELECT city, COUNT(*) AS order_count FROM orders GROUP BY city ORDER BY order_count DESC LIMIT 10;"
    explanation: "鎸夊煄甯傜粺璁¤鍗曢噺骞舵帓搴忋€?
```

##### 4.4 涓ゅ DB 鎶借薄灞?鈫?缁熶竴鍒?`query/executors/db_pool.py`

**鐜扮姸锛?* `db_abstraction.py`锛堥噸锛夊拰 `database.py`锛堣交锛夊苟琛?
**鐩爣锛?* 缁熶竴 `DatabaseManager`锛堟潵鑷?db_abstraction.py锛? `QueryExecutor`锛堟潵鑷?executor.py锛夛紝鍚堝苟涓?`query/executors/db_pool.py`

```
query/executors/
鈹溾攢鈹€ db_pool.py       # DatabaseManager 鍗曚緥 + 杩炴帴姹犵鐞嗭紙鏉ヨ嚜 db_abstraction.py锛?鈹溾攢鈹€ query_executor.py  # run_query() + 瀹夊叏鏍￠獙锛堟潵鑷?executor.py锛?鈹斺攢鈹€ connectors/      # SQLite/MySQL/PostgreSQL 杩炴帴鍣?    鈹溾攢鈹€ sqlite.py
    鈹溾攢鈹€ mysql.py
    鈹斺攢鈹€ postgresql.py
```

##### 4.5 UI 缁曡繃 API 鈫?HTTP 璋冪敤

**鐜扮姸锛?* `streamlit_app.py` 鐩存帴 import `ask_question`

**鐩爣锛?*
```python
# ui/streamlit_app.py
import requests, os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

def ask(question: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/ask",
        json={"question": question},
        headers={"X-API-Key": os.getenv("API_KEY", "")},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
```

---

#### 浜斻€佹柊妯″潡娓呭崟

| 鏂囦欢璺緞 | 鑱岃矗 |
|----------|------|
| `query/ask.py` | QueryService锛氱紪鎺掑畬鏁存煡璇㈤摼璺?|
| `query/generators/base.py` | `SqlGenerator` 鎺ュ彛 |
| `query/generators/llm_generator.py` | LLM SQL 鐢熸垚鍣?|
| `query/generators/rule_generator.py` | 瑙勫垯 SQL 鐢熸垚鍣?|
| `query/classifiers/rule_based_classifier.py` | 闂鍒嗙被鍣?|
| `query/retrieval/schema_retriever.py` | Schema 妫€绱㈠櫒 |
| `query/executors/db_pool.py` | 鏁版嵁搴撹繛鎺ユ睜绠＄悊 |
| `query/executors/query_executor.py` | 鏌ヨ鎵ц鍣?|
| `query/executors/connectors/*.py` | 澶氭暟鎹簱杩炴帴鍣?|
| `rules/store.py` | RuleStore锛歒AML 瑙勫垯鍔犺浇鍣?|
| `rules/matcher.py` | RuleMatcher锛氳鍒欏尮閰?|
| `rules/default_rules.yaml` | 瑙勫垯閰嶇疆 |
| `llm/factory.py` | LLM 閫傞厤鍣ㄥ伐鍘傦紙娉ㄥ唽琛ㄦā寮忥級 |
| `data/rules/default_rules.yaml` | 榛樿瑙勫垯 |

---

#### 鍏€佽В鍐充簡鍝簺褰撳墠闂

| 闂 | 瑙ｅ喅鏂规 |
|------|---------|
| #1 generate_sql() 7 绉嶈亴璐ｆ贩鍚?| 鎷嗗垎涓?generators/ 涓嬬嫭绔嬬敓鎴愬櫒锛屾瘡涓敓鎴愬櫒鍗曚竴鑱岃矗 |
| #2 classifier 缁撴灉鏈疮绌?| QueryService 绗竴姝ユ墽琛?classifier锛岀粨鏋滃瓨鍏?ctx 渚涘悗缁娇鐢?|
| #3 瑙勫垯纭紪鐮?| rules/store.py + YAML锛岃繍琛屾椂鍙姞杞?澧炲垹瑙勫垯 |
| #4 涓ゅ DB 鎶借薄灞傚苟琛?| 缁熶竴鍒?query/executors/锛屾秷闄ら噸澶嶆娊璞?|
| #5 UI 缁曡繃 API | UI 鏀逛负 HTTP 璋冪敤 /ask锛岀粡杩囪璇?涓棿浠?鍩嬬偣 |
| #6 ask_question() 缂栨帓+鎵ц娣峰悎 | QueryService 缁熶竴缂栨帓锛宔xecutor 鐙珛锛屽悇鐜妭鍙崟鐙祴璇?|
| Provider 鎵╁睍 OCP 杩濆弽 | llm/factory.py 寮曞叆绛栫暐娉ㄥ唽琛紝鏂板 Provider 鍙渶娉ㄥ唽 |

---

#### 涓冦€佹綔鍦ㄦ柊闂

1. **妯″潡闂村惊鐜緷璧栭闄?*锛氬鏋?query 渚濊禆 auth锛堝仛鏉冮檺鏍￠獙锛夛紝auth 鍙堥渶瑕?query 鐨勬煇浜涚粨鏋滃仛鍒ゆ柇锛屽彲鑳藉舰鎴愬惊鐜€傜紦瑙ｏ細auth 鍙仛鍚屾鐨勫竷灏斿垽鏂紝涓嶈皟鐢?query 鐨勪笟鍔￠€昏緫銆?
2. **"妯″潡鍖栧崟浣?鍙兘閫€鍖栦负"澶ф偿鐞?**锛氬鏋滄ā鍧楀唴鍙堝嚭鐜颁氦鍙夊紩鐢紙query/generators 鐩存帴 import query/executors 鐨勫唴閮ㄥ嚱鏁帮級锛屾灦鏋勭害鏉熶細澶辨晥銆傜紦瑙ｏ細妯″潡鍐呴€氳繃 `__init__.py` 瀹氫箟 public 鎺ュ彛锛岀姝?import 鍐呴儴鏂囦欢銆?
3. **UI HTTP 璋冪敤澧炲姞鏃跺欢**锛氭湰鍦板紑鍙戞椂 FastAPI + Streamlit 鍒嗗紑鍚姩锛屽涓€娆＄綉缁滆烦杞€傜紦瑙ｏ細寮€鍙戞ā寮忓彲浠ョ敤鐜鍙橀噺 `DEV_MODE=true` 缁曡繃 HTTP锛岀洿鎺ヨ皟鐢?QueryService銆?
4. **瑙勫垯 YAML 鐑洿鏂伴渶瑕佹枃浠剁洃鎺?*锛歚watchdog` 搴撶洃鍚枃浠跺彉鍖栵紝涓嶉€傚悎绠€鍗曡疆璇€傜敓浜ч儴缃叉椂瑕佹敞鎰忋€?
---

#### 鍏€佸姣斿叾浠栨彁妗?
| 缁村害 | 鎻愭 A锛堝垎灞傦級 | 鎻愭 B锛圕lean锛?| 鎻愭 C锛堟ā鍧楀寲锛?| 鎻愭 D锛圥ipeline锛?|
|------|-------------|----------------|-----------------|-------------------|
| **澶嶆潅搴?* | 涓?| 楂?| 浣?涓?| 涓?|
| **鏂板鏂囦欢鏁?* | ~20 涓?| ~25 涓?| ~15 涓?| ~18 涓?|
| **杩佺Щ鎴愭湰** | 涓?| 楂?| 浣?| 涓?|
| **閫傚悎鍥㈤槦瑙勬ā** | 3-10 浜?| 5浜? | 2-5 浜?| 浠绘剰 |
| **閫傚悎鍙樻洿绫诲瀷** | 绋冲畾灞傞棿鍏崇郴 | 澶氶€傞厤鍣ㄥ垏鎹?| 鎸変笟鍔¤兘鍔涙墿灞?| 娴佺▼鍙彉/澶氳矾寰?|
| **瀵圭幇鏈変唬鐮佹敼鍔?* | 閲嶆瀯灞傜粨鏋?| 閲嶆瀯鎵€鏈夋枃浠?| 鎸夎兘鍔涜縼绉?| 鎷嗗垎涓?Stage |

**鎻愭 C 鐨勬牳蹇冧紭鍔匡細** 瀵圭幇鏈変唬鐮佹敼鍔ㄦ渶灏忥紝鎸変笟鍔¤兘鍔涜縼绉昏€岄潪鎸夊眰娆￠噸鏋勶紝閫傚悎涓皬鍥㈤槦蹇€熻惤鍦般€?
---

**鎻愭 C 瀹屾垚銆?*

