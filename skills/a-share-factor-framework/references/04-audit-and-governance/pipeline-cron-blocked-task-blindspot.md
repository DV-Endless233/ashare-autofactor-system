# Pipeline Cron Blocked-Task Blindspot（R114 案例）

## 问题描述

2026-07-28 06:48，dvcoder 启动 R114 语义探索（Employee Productivity = totopinc_ttm / staff_number_total）。

dvcoder 在 4 分钟内完成了语义分析（经济学含义 ✓ 单因子合规 ✓ 因子库无重复 ✓），但因 staff feather 缓存缺失无法进入算子空间，于是调用：
```
kanban_block(reason="缺少 staff ETL 数据：请先执行 asharestaffstructure_.updatedata_()")
```

**问题**：pipeline cron（每10分钟 tick）从 06:58 起每看到这个 blocked task，都认为"管道状态正确，无需自动推进"。直到 13:27（6.5 小时后）才创建了 evaluator 语义预审 task。

## 根因

旧版 cron prompt 的状态机逻辑存在两个盲区：

### 盲区 1：模糊时间窗口

旧规则：
```
3. 如果 dvcoder 的 task **刚完成**（done/blocked），检查是否有对应的 evaluator task
```

"刚完成"是模糊条件。当一个 task 在 06:52 变成 blocked，到 06:58（下一个 tick）已经过了 6 分钟。cron agent 可能不认为这算"刚完成"，因此跳过了 evaluator 创建逻辑。

### 盲区 2：依赖 block reason 关键词

旧规则没有 explicit 说依赖于 block reason，但 cron agent 在判断时隐含依赖：当它看到 blocked reason 是"缺少 staff ETL 数据"（数据依赖，不是 "review-required"），就认为这是"等人修数据，不需 evaluator"。

但实际上 dvcoder 的语义分析已经完成（写在了 kanban comment 里），需要的只是 evaluator 做一个形式化的语义预审。

## 修复（2026-07-28）

将 cron prompt 改为无条件扫描逻辑：

```
2. **无条件扫描所有 blocked 的 dvcoder task**：
   对每个状态为 blocked 的 dvcoder task，检查该 round 是否已有对应的 evaluator task。
   如果**没有**，立即创建对应类型的 evaluator task：
   - 从 dvcoder task title 判断阶段（**不依赖 block reason 的关键词**）：
     - title 含「语义空间探索」「semantic exploration」→ 语义预审
     - title 含「算子空间实现」「operator implementation」→ 算子复审
   - 创建前必须执行**中段 evaluator 已完成检测**（SQLite 查重）
```

## 要点

- **不依赖 block reason**：无论 dvcoder 的 blocked reason 是 review-required、数据依赖、迭代预算耗尽还是其他原因，只要 dvcoder 在 blocked 状态且无对应 evaluator task，就创建
- **阶段判断用 title**：task title 是结构化的（"R114 语义空间探索—…"），比 block reason 更可靠
- **增加中段检测**：evaluator 可能在上个 tick 之间已完成审查（常见于快速评估），创建前必须用 SQLite 查重

## 配置文件位置

修复后的 cron prompt 在：
`${HERMES_HOME}/cron/jobs.json` → job `a-share-auto-pipeline` → `prompt` 字段

## 警示

任何修改 pipeline cron prompt 的 action 都必须保留这个"无条件扫描 blocked"逻辑。退化回"刚完成"模糊条件会再次导致 6+ 小时的调度延迟。
