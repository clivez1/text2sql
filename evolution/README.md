# Text2SQL Agent 演进工作区

> 从 Demo 到生产级系统的渐进式增强

## 目录结构

```
evolution/
├── README.md                    # 本文件
├── TECH_EVOLUTION_PLAN.md       # 技术演进方案
├── GAP_ANALYSIS.md              # 与 Data Viz 的差距分析
├── IMPLEMENTATION_LOG.md        # 实施记录
└── templates/                   # 可复用代码模板
    ├── errors.py               # 统一错误处理模板
    ├── validators.py           # 输入验证模板
    ├── resilient_llm.py        # LLM 弹性调用模板
    └── rate_limiter.py         # 限流中间件模板
```

## 工作流程

1. **分析差距** → `GAP_ANALYSIS.md`
2. **制定方案** → `TECH_EVOLUTION_PLAN.md`
3. **提取模板** → `templates/`
4. **逐步实施** → 修改原项目代码
5. **记录进度** → `IMPLEMENTATION_LOG.md`

## 实施原则

- **增量更新**：每次只改一个模块，验证通过后再继续
- **测试先行**：先修复测试，再实施增强
- **复用优先**：从 Data Viz Agent 复用已验证的代码模式
- **保持兼容**：不破坏现有 API 接口

## 当前状态

- [x] 创建演进工作区
- [ ] 差距分析完成
- [ ] 演进方案制定
- [ ] 模板提取
- [ ] Phase 1 实施
- [ ] Phase 2 实施