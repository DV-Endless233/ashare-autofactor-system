# Pipeline Cron Blocked Task 盲区修复记录（2026-07-28）

## 问题

R114 dvcoder 在 06:48 进入 kanban_block 状态（数据依赖阻塞），但 pipeline cron 直到 13:27（6.5 小时后）才创建对应的 evaluator 语义预审任务。

## 根因

旧 cron prompt 的状态机逻辑：

```
3. 如果 dvcoder 的 task **刚完成**（done/blocked），检查是否有 evaluator task
```

两个缺陷：
1. **"刚完成"时间窗口模糊** — cron 可能认为 R114 在 06:52 blocked、到 08:00 已不算"刚完成"，跳过检查
2. **依赖 block reason 关键词** — cron 看到 "缺少 staff ETL 数据" 认为"等人工，不需要 evaluator"，没有意识到语义分析已完成（只是无法进算子空间）

## 修复内容

cron prompt 的"状态机"部分重写为：

```
2. **无条件扫描所有 blocked 的 dvcoder task**：
   对每个 blocked dvcoder task，检查该 round 是否已有对应 evaluator task。
   如果没有 → 立即创建
   - 从 title 判断阶段（语义/算子），**不依赖 block reason**
   - 创建前做中段 evaluator 已完成检测（SQLite 查重）
```

## 规范变更

- pipeline cron 不再依赖"刚完成"或 block reason 关键词
- 所有 blocked 状态的 dvcoder task 都会被检查
- 阶段判断从 task title 提取（稳健），不从 block reason 字符串猜测（脆弱）

文件位置：`${HERMES_HOME}/cron/jobs.json` 中 `a-share-auto-pipeline` 的 `prompt` 字段。
