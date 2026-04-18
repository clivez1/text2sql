# 12. LLM 优先迁移方案

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 当前问题

当前系统的主路由仍然是：

- 先分类
- 先判断 `needs_llm`
- 简单问题走规则 / 模板 / fast fallback
- 复杂问题才进入 LLM

这个架构的问题不是“规则不好”，而是：

1. 主链路被演示库规则绑定
2. 复杂度判断过早，导致泛化能力受限
3. LLM 不能统一承担意图规划、检索规划和 SQL 草拟
4. 本地规则长期成为系统行为中心，最终无法成为通用平台

---

## 2. 迁移目标

迁移后应改为：

1. LLM 负责意图规划
2. 检索层负责 schema grounding
3. SQL 生成器负责方言化输出
4. policy gate 和 validator 负责约束与修复
5. 本地规则只作为辅助资产和兜底资产存在

---

## 3. 目标链路

### 3.1 读路径

`question -> plan intent -> retrieve grounding -> draft sql -> validate -> repair -> execute -> explain`

### 3.2 写路径

`action request -> plan action -> validate params -> dry-run -> approve -> execute -> audit -> rollback token`

---

## 4. Provider 协议层要求

### 4.1 必须支持的协议

- OpenAI compatible
- Anthropic messages
- local gateway

### 4.2 必须支持的能力

- 统一健康检查
- 统一文本补全 / 对话接口
- 统一结构化输出能力
- 统一错误分类
- 统一超时和重试策略
- 主模型 + fallback 模型序列

### 4.3 配置要求

配置不能再只表达“第几个 provider”，还要表达：

- 协议类型
- 用途类型
- 模型等级
- timeout
- retry
- max tokens
- 预算上限
- fallback 顺序

---

## 5. 规则资产的重新定位

本地规则不删除，但角色必须变化：

### 5.1 变成 few-shot 资产

- 高价值问法对应优质 SQL 示例
- 作为 prompt 里的示例，不再直接短路主流程

### 5.2 变成修复资产

- 对常见错误 SQL 进行规则化修复
- 例如 LIMIT、危险关键字、特定方言替换、字段别名回补

### 5.3 变成兜底资产

- 在检索失败或模型失败时保底
- 明确标记为 fallback 输出

### 5.4 变成回归资产

- 用作评测集和回归验证素材
- 防止主链路演进后退化

---

## 6. 迁移步骤

### Step 1：抽象 provider 接口

- 拆分当前 adapter 层
- 补齐 Anthropic 协议实现
- 增加 local gateway 适配层

### Step 2：建立 Router

- 把当前 `generate_sql()` 改造成显式 Router
- 输出中间结果：intent、retrieval query、grounding、draft、repair history

### Step 3：建立 validation + repair loop

- AST 校验
- 表列合法性校验
- budget 校验
- 失败时自动修复

### Step 4：下放规则角色

- 保留 YAML 规则库
- 从主路由中移除“先规则后 LLM”的控制权

### Step 5：补 eval

- 比较迁移前后成功率、延迟、成本和 fallback 率

---

## 7. 验收标准

- 简单问题不再依赖 `needs_llm=False` 才进入主链路
- LLM 可以统一承担 planning 和 drafting
- 本地规则不再决定主路由是否调用 LLM
- OpenAI / Anthropic / local gateway 三类协议都可完成健康检查和主链路调用
- 主模型失败后能按配置切换 fallback
