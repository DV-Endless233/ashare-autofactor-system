# Kanban Task 创建链

## 硬规则

**只有 `default` 能调用 `kanban_create`。** `dvcoder` 和 `evaluator` 不得创建下游 task。

正确结束方式：
- `kanban_block(reason="review-required")` — 需要人或其他 profile 检查
- `kanban_complete(summary=..., metadata=...)` — 任务完成

## 三阶段流水线任务创建链

```
                         default 创建
                             │
                    ┌────────┴────────┐
                    │ 阶段1：语义预审   │
                    │ dvcoder task    │
                    └────────┬────────┘
                             │ dvcoder 完成 → blocked
                             ▼
                    ┌────────┴────────┐
                    │ default 读取    │
                    │ 创建 evaluator  │
                    │ 语义预审 task   │
                    └────────┬────────┘
                             │ evaluator 完成
                             ▼
                    ┌────────┴────────┐
                    │ default 读取结论 │
                    │                 │
                    │ 通过 → 创建     │
                    │  阶段2 dvcoder  │
                    │  算子空间 task  │
                    │                 │
                    │ 打回 → 创建     │
                    │  新的阶段1      │
                    │  dvcoder task   │
                    └────────┬────────┘
                             │ dvcoder 完成 → blocked
                             ▼
                    ┌────────┴────────┐
                    │ default 读取    │
                    │ 创建 evaluator  │
                    │ 复审 task       │
                    └────────┬────────┘
                             │ evaluator 完成
                             ▼
                    ┌────────┴────────┐
                    │ default 读取结论 │
                    │                 │
                    │ 通过 → 归档到   │
                    │  evaluator_pass │
                    │  ed/ + 创建     │
                    │  下一轮 dvcoder │
                    │  task (永不停止) │
                    │                 │
                    │ 不通过 → 创建   │
                    │  下一轮 dvcoder │
                    │  task (按方向)  │
                    └────────┬────────┘
                             │
                             ▼
                    回到阶段1或阶段2
                    (永不停机循环)
```

## 谁不能做什么

| Profile | 禁止行为 | 正确做法 |
|---------|---------|----------|
| dvcoder | `kanban_create()` 创建 evaluator task | `kanban_block(reason="review-required")` |
| evaluator | `kanban_create()` 创建 dvcoder task | `kanban_complete()` 或 `kanban_block()` |
| 任何 profile | 在自己 task 未完成时创建另一个 task | 先完成当前 task |

## 例外

同一轮次内，dvcoder 在阶段 2 算子空间实现中如需创建 evaluator 失败审查子 task，可调用 `kanban_create`——但必须：
- 在 `kanban_complete` 的 `created_cards` 中显式声明
- evaluator 完成后仍由 `default` 创建下一轮 task
