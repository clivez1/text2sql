# 部署指南

> Text2SQL Agent 部署运维完整指南

## 目录

- [本地开发环境](#本地开发环境)
- [Docker 部署](#docker-部署)
- [生产部署](#生产部署)
- [监控配置](#监控配置)
- [备份恢复](#备份恢复)
- [高可用架构](#高可用架构)
- [故障排查](#故障排查)
- [性能优化](#性能优化)
- [生产 Checklist](#生产-checklist)

---

## 本地开发环境

### 前置要求

| 依赖 | 版本 | 检查命令 |
|------|------|----------|
| Python | 3.11+ | `python3 --version` |
| pip | 最新 | `pip --version` |
| SQLite | 3.x | `sqlite3 --version` |

### 安装步骤

```bash
cd /path/to/text2sql-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/init_demo_db.py
python scripts/ingest_schema.py
streamlit run app/ui/streamlit_app.py
```

---

## Docker 部署

### 单容器部署

```bash
docker build -t text2sql-agent:latest .
docker run -d --name text2sql \
  -p 8501:8501 -p 8000:8000 \
  -e LLM_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  text2sql-agent:latest
```

### Docker Compose 部署

```bash
docker-compose up -d combined
```

### 服务访问

| 服务 | 地址 |
|------|------|
| Streamlit UI | http://localhost:8501 |
| FastAPI | http://localhost:8000/docs |

---

## 生产部署

### MySQL 连接

```bash
DB_TYPE=mysql
DB_URL=mysql+pymysql://text2sql:password@db-host:3306/sales?charset=utf8mb4
```

### Nginx 反向代理

```nginx
server {
    listen 443 ssl http2;
    server_name text2sql.example.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
    }
}
```

### Systemd 服务

```ini
[Unit]
Description=Text2SQL API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/text2sql-agent
ExecStart=/opt/text2sql-agent/.venv/bin/uvicorn app.api.main:app --host 127.0.0.1 --port 8000
Restart=always
```

---

## 监控配置

### 健康检查脚本

```bash
#!/bin/bash
# health-check.sh

HEALTH_URL="http://localhost:8000/health"
response=$(curl -s $HEALTH_URL)
status=$(echo $response | jq -r '.status')

if [ "$status" != "ok" ]; then
    echo "Service unhealthy!"
    exit 1
fi
echo "Service healthy"
```

### Cron 定时检查

```bash
# 每分钟检查
* * * * * /opt/text2sql-agent/scripts/health-check.sh
```

### 日志轮转

```ini
# /etc/logrotate.d/text2sql
/opt/text2sql-agent/logs/*.log {
    daily
    rotate 14
    compress
}
```

---

## 备份恢复

### SQLite 备份

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
sqlite3 data/demo_db/sales.db ".backup '/backup/sales_$DATE.db'"
gzip /backup/sales_$DATE.db
```

### MySQL 备份

```bash
mysqldump -h host -u user -p database | gzip > /backup/sales_$(date +%Y%m%d).sql.gz
```

### ChromaDB 备份

```bash
tar -czf /backup/chroma_$(date +%Y%m%d).tar.gz data/chroma/
```

### 恢复流程

```bash
# SQLite
gunzip -c /backup/sales_20260322.db.gz > data/demo_db/sales.db

# ChromaDB
tar -xzf /backup/chroma_20260322.tar.gz
```

---

## 高可用架构

### 架构示意

```
         Nginx (LB)
             │
     ┌───────┼───────┐
     ▼       ▼       ▼
  API-1   API-2   UI
     │       │       │
     └───────┼───────┘
             │
      ┌──────┴──────┐
      ▼             ▼
   MySQL       ChromaDB
  (Primary)    (共享存储)
```

### 关键配置

| 组件 | 方案 |
|------|------|
| API | 多实例 + Nginx 负载均衡 |
| MySQL | 主从复制 |
| ChromaDB | 共享存储或迁移 Milvus |

---

## 故障排查

### LLM 连接失败

```bash
grep LLM_API_KEY .env
```

### 数据库连接失败

```bash
sqlite3 data/demo_db/sales.db "SELECT 1"
```

### ChromaDB 错误

```bash
rm -rf data/chroma/schema_store
python scripts/ingest_schema.py
```

---

## 性能优化

### Gunicorn 多进程

```bash
gunicorn app.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 生产 Checklist

### 部署前

- [ ] 配置 `LLM_API_KEY`
- [ ] 配置生产数据库
- [ ] 设置 `READONLY_MODE=true`
- [ ] 配置 HTTPS 证书

### 部署后

- [ ] 验证 `/health`
- [ ] 验证 `/docs`
- [ ] 配置监控
- [ ] 配置备份

---

## 更新记录

| 日期 | 内容 |
|------|------|
| 2026-03-22 | 新增监控、备份、高可用 |
| 2026-03-22 | 细化部署指南 |
| 2026-03-20 | 创建初版 |