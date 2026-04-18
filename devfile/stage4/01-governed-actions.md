# stage4-01. 受治理动作目录

> 状态：未开始
> 更新：2026-04-18

---

## 1. 目标

1. 用 action type 替代自由写 SQL。
2. 明确允许动作、禁止动作和高风险动作边界。
3. 让数据写入从“生成 SQL”变成“执行受支持动作”。

---

## 2. 首批动作建议

1. insert_record
2. update_record
3. bulk_update_by_filter
4. soft_delete_record
5. restore_record
6. import_records
7. recompute_field

---

## 3. 默认禁止项

1. DDL
2. 无条件全表更新
3. 无条件全表删除
4. 跨租户写入
5. 无审批批量操作

---

## 4. 参考

1. references/themes/02-copilot-visualization-and-actions.md