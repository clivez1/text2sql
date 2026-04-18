# 20-04. presentation 层与入口迁移方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 迁移范围

presentation 层负责：

- FastAPI API
- Streamlit UI
- HTTP middleware
- presenter 与响应组装
- 面向外部的错误映射与输入校验

---

## 2. 当前模块清单

- app/api/main.py
- app/api/routes/
- app/ui/streamlit_app.py
- app/ui/chart_renderer.py
- app/ui/exporter.py
- app/middleware/rate_limiter.py
- app/core/errors.py

---

## 3. 目标结构

```text
app/presentation/
├── api/
│   ├── main.py
│   ├── routes/
│   ├── middleware/
│   ├── error_handlers.py
│   ├── validators.py
│   ├── schemas.py
│   └── presenters.py
└── ui/
    ├── streamlit_app.py
    ├── chart_renderer.py
    ├── exporter.py
    └── components/
```

---

## 4. 文件映射

| 当前文件 | 目标位置 | 说明 |
|---|---|---|
| app/api/main.py | app/presentation/api/main.py | 第一落点直接迁移 |
| app/api/routes/ | app/presentation/api/routes/ | 直接迁移 |
| app/ui/streamlit_app.py | app/presentation/ui/streamlit_app.py | 第一落点直接迁移 |
| app/ui/chart_renderer.py | app/presentation/ui/chart_renderer.py | 直接迁移 |
| app/ui/exporter.py | app/presentation/ui/exporter.py | 直接迁移 |
| app/middleware/rate_limiter.py | app/presentation/api/middleware/rate_limiter.py | HTTP 中间件归 presentation |
| app/core/errors.py | app/presentation/api/error_handlers.py | FastAPI 绑定逻辑属于 API 层 |

---

## 5. 关键调整

### 5.1 API schema 与 presenter

当前 app/shared/schemas.py 同时承载：

1. API 请求模型
2. API 响应模型
3. 内部 AskResult dataclass

迁移后：

- API 请求/响应模型进入 presentation/api/schemas.py
- domain object 留在 domain/
- presenters.py 负责 domain -> API response 的转换

### 5.2 API 入口依赖方向

迁移后 API 只允许依赖：

- application/
- domain/
- presentation/api 自己的 schemas、middleware、presenters

不再直接依赖旧 app/core/ 模块。

### 5.3 UI 依赖方向

迁移后 Streamlit UI 只允许调用：

- application/orchestration/
- application/analytics/
- application/actions/

不再直接调用 core/data_import、core/chart、core/orchestrator。

---

## 6. 推荐批次

### Batch P1：平移 API 与 UI 文件

- 先把 main.py、routes/、streamlit_app.py、chart_renderer.py、exporter.py 平移到 presentation/
- 旧路径保留兼容 wrapper

### Batch P2：迁移 middleware 与错误处理

- rate_limiter.py
- error_handlers.py
- validators.py

### Batch P3：引入 presenters

- API 不再直接依赖内部 dataclass
- presenter 负责组装 AskResponse

### Batch P4：切断对旧 core 的直接 import

- UI 和 API 统一只调 application 层

---

## 7. 验收标准

1. app/api 和 app/ui 不再承接新增代码。
2. API 与 UI 都通过 application 层进入主链路。
3. 错误处理、验证器、限流和响应组装都在 presentation 层收口。