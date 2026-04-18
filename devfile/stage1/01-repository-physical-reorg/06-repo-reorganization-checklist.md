# 仓库物理整理检查清单

> 状态：当前生效
> 更新：2026-04-18

---

## 1. 执行原则

1. 目录整理先于大规模删除。
2. 会影响 import、Docker、CI 的路径变更必须与 stage1/02-code-refactor/ 联动执行。
3. 可以先建立目标目录，再逐批迁文件，避免一次性大搬家。

---

## 2. 推荐批次

### Batch R0：冻结文档入口

- 完成 devfile 根级与 stage/reference 子目录导航
- 冻结 stage1 下的物理整理与代码重构两条执行线

### Batch R1：根目录卫生整理

- 清理根目录报告产物
- 约束 .deploy/reports/、.deploy/exports/ 的新落位

### Batch R2：数据区与运行时区整理

- 冻结 data、datasets、.deploy 三分法
- 为 future sessions、exports、reports 预留目录

### Batch R3：工具区整理

- scripts 拆为 bootstrap、verify、evaluate、ops
- tests 为 eval、scenarios 预留区位

### Batch R4：app 壳层整理

- 完成 presentation/application/domain/infrastructure 的目标路径建立
- 停止在 app/api、app/ui、app/core、app/rules、app/middleware 新增代码

### Batch R5：历史残留清退

- 清退 evolution/
- 清退 app/app/
- 清退根目录一次性文件

---

## 3. 每批执行前检查

1. 是否会影响 import 路径。
2. 是否会影响 Dockerfile 或 docker-compose 路径。
3. 是否会影响 GitHub Actions 工作流。
4. 是否已有对应兼容层或 wrapper。

只要以上任一答案为“会”，就先看 stage1/02-code-refactor/ 的对应 batch。

---

## 4. 每批执行后验证

1. 运行受影响模块的最小导入验证。
2. 运行对应测试批次。
3. 审计 README、docs、devfile 是否仍引用旧路径。
4. 确认没有新临时文件越界落到根目录。

---

## 5. 物理整理完成标准

当以下条件成立时，仓库物理整理阶段可以视为完成：

1. 根目录、app、数据区、工具区、文档区和历史区都有固定落位。
2. 新增内容不会再因为“应该放哪”而反复争论。
3. 所有后续代码迁移都可以直接参考目标目录落位，不再需要重画结构图。