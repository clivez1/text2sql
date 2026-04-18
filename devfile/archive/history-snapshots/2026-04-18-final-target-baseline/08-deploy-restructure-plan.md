# 部署目录重构方案

> 日期：2026-04-16
> 状态：规划中

---

## 1. 背景与目标

### 问题
- 测试数据全为隐私数据，不可入 git
- Schema 可能含隐私信息
- 向量库方案经常更换（ChromaDB → Milvus → PGVector）
- 需要支持 >10GB 大规模测试数据

### 目标
- Demo 数据入 git（供他人快速体验）
- 运行时数据可一键清理
- 测试数据长期存储但永不入 git
- 向量库可随时替换/重建

---

## 2. 新目录结构

```
text2sql-0412/
├── data/                   # Demo 数据（入 git）
│   ├── ddl/               # Schema 定义（脱敏）
│   │   └── sales_schema.sql
│   └── demo_db/           # Demo 数据库
│       └── sales.db
│
├── .deploy/               # 运行时（不入 git，一键清理）
│   ├── chroma/            # 向量库（含 schema 隐私）
│   ├── db/                # 运行时数据库
│   └── logs/              # 日志
│
├── datasets/              # 测试数据（隐私，长期存储，不入 git）
│   ├── sales/
│   ├── inventory/
│   └── ...
│
├── app/
├── scripts/
├── docs/
└── devfile/
```

### 目录职责

| 目录 | 内容 | 入 Git | 清理策略 |
|------|------|--------|----------|
| `data/` | Demo 数据（轻量） | ✅ | 保留 |
| `.deploy/` | 运行时数据 | ❌ | `rm -rf .deploy/` |
| `datasets/` | 隐私测试数据 | ❌ | 独立备份 |

---

## 3. 代码影响分析

### 3.1 需要修改的文件

| 文件 | 当前路径引用 | 修改内容 |
|------|-------------|----------|
| `docker-compose.yml` | `./data:/app/data`, `./logs:/app/logs` | 修改 volume 映射 |
| `Dockerfile` | `COPY data/ ./data/` | 保持（demo 数据需入镜像） |
| `scripts/init_demo_db.py` | `data/demo_db/sales.db` | 保持（demo 路径不变） |
| `scripts/ingest_schema.py` | `data/ddl/sales_schema.sql` | 保持（demo schema） |
| `app/config/settings.py` | `VECTOR_DB_PATH` 默认值 | 改为 `.deploy/chroma` |
| `app/core/retrieval/schema_loader.py` | `vector_db_path / "schema_store"` | 无需改（读配置） |
| `.env.example` | `VECTOR_DB_PATH=./data/chroma` | 改为 `./.deploy/chroma` |
| `.gitignore` | 新增 | 排除 `.deploy/`, `datasets/` |

### 3.2 路径变更对照表

| 用途 | 当前路径 | 新路径 |
|------|---------|--------|
| Demo 数据库 | `data/demo_db/sales.db` | 不变 |
| Demo Schema | `data/ddl/sales_schema.sql` | 不变 |
| 向量库 | `data/chroma/` | `.deploy/chroma/` |
| 运行时日志 | `logs/` | `.deploy/logs/` |
| 运行时数据库 | `data/demo_db/sales.db` | `.deploy/db/` (可选) |

### 3.3 环境变量变更

```bash
# 当前
VECTOR_DB_PATH=./data/chroma

# 新配置
VECTOR_DB_PATH=./.deploy/chroma
DB_URL=sqlite:///data/demo_db/sales.db  # demo 保持不变
```

---

## 4. 实施步骤

### Step 1: 创建目录结构
```bash
mkdir -p .deploy/chroma .deploy/db .deploy/logs
mkdir -p datasets
touch datasets/.gitkeep
```

### Step 2: 更新 .gitignore
```gitignore
# 运行时数据
.deploy/

# 测试数据（隐私）
datasets/

# 其他保持不变
.env
logs/
```

### Step 3: 修改 docker-compose.yml
```yaml
volumes:
  # Demo 数据（只读，入镜像）
  - ./data:/app/data:ro
  # 运行时数据
  - ./.deploy/chroma:/app/.deploy/chroma
  - ./.deploy/logs:/app/.deploy/logs
  # 测试数据（可选挂载）
  # - ./datasets:/app/datasets:ro
```

### Step 4: 修改 .env.example
```bash
VECTOR_DB_PATH=./.deploy/chroma
```

### Step 5: 修改 app/config/settings.py
```python
vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./.deploy/chroma")
```

### Step 6: 验证
```bash
# 初始化
python scripts/init_demo_db.py
python scripts/ingest_schema.py

# 启动
docker-compose up -d combined

# 验证路径
ls .deploy/chroma/  # 应有向量数据
ls data/demo_db/    # 应有 demo 数据
```

---

## 5. Docker Volume 映射方案

### 方案 A：分离映射（推荐）

```yaml
services:
  combined:
    volumes:
      # Demo 数据（只读）
      - ./data:/app/data:ro
      # 运行时
      - ./.deploy/chroma:/app/.deploy/chroma
      - ./.deploy/logs:/app/.deploy/logs
    environment:
      - VECTOR_DB_PATH=./.deploy/chroma
```

**优点**：
- Demo 数据只读，防止误改
- 运行时数据独立，可一键清理
- 测试数据可选择性挂载

### 方案 B：统一映射

```yaml
volumes:
  - ./.deploy:/app/.deploy
  - ./data:/app/data:ro
```

**优点**：配置简单

---

## 6. 测试数据管理策略

### 6.1 数据集结构

```
datasets/
├── sales/
│   ├── schema.sql          # 表结构
│   ├── products.csv        # 产品数据
│   ├── orders_1m.parquet   # 订单数据（压缩格式）
│   └── README.md           # 数据说明
├── inventory/
│   └── ...
└── .gitkeep
```

### 6.2 加载脚本

```python
# scripts/load_test_dataset.py
import sys
dataset = sys.argv[1]  # e.g., "sales"
# 从 datasets/{dataset}/ 加载到 .deploy/db/
```

### 6.3 备份策略

```bash
# 备份测试数据（独立存储）
tar -czf /backup/datasets_$(date +%Y%m%d).tar.gz datasets/

# 清理运行时
rm -rf .deploy/
```

---

## 7. 向量库迁移策略

当需要更换向量库时：

```bash
# 1. 清理旧向量库
rm -rf .deploy/chroma/

# 2. 修改配置（如切换到 Milvus）
# VECTOR_DB_TYPE=milvus
# VECTOR_DB_PATH=./.deploy/milvus

# 3. 重新初始化
python scripts/ingest_schema.py
```

---

## 8. 回滚方案

如需回滚到旧结构：

```bash
# 1. 恢复配置
git checkout docker-compose.yml .env.example app/config/settings.py

# 2. 移动数据
mv .deploy/chroma data/chroma/
mv .deploy/logs logs/

# 3. 清理
rm -rf .deploy/
```

---

## 9. 检查清单

### 实施前
- [ ] 备份当前 `data/chroma/` 数据
- [ ] 确认 `.env` 不在 git 跟踪中

### 实施后
- [ ] 验证 `python scripts/init_demo_db.py` 正常
- [ ] 验证 `python scripts/ingest_schema.py` 写入 `.deploy/chroma/`
- [ ] 验证 Docker 启动正常
- [ ] 验证 `.gitignore` 排除 `.deploy/` 和 `datasets/`
- [ ] 验证 `git status` 不显示运行时文件

---

## 10. 更新记录

| 日期 | 内容 |
|------|------|
| 2026-04-16 | 创建方案文档 |
