# 2026-07-28 Pipeline cron 盲区修复记录

## 场景
R114 dvcoder 在 06:48 完成语义分析后执行 `kanban_block(reason="缺少 staff ETL 数据...")`，但 pipeline cron 直到 13:21 才创建 evaluator 语义预审 task，间隔 6.5 小时。

## 根因
旧版 cron prompt 规则：
```
3. 如果 dvcoder 的 task **刚完成**（done/blocked），检查是否有 evaluator task
```
两个漏洞：
1. **"刚完成"** — 模糊时间窗口，cron 可能认为 R114 在 06:52 blocked 后到 08:00 已不算"刚完成"
2. **依赖 block reason** — cron 看到"缺少 staff ETL 数据"就认为"在等人，不送 evaluator"

## 修复内容
在 `${HERMES_HOME}/cron/jobs.json` 的 `a-share-auto-pipeline` prompt 中：
- 将"刚完成（done/blocked）"改为 **"无条件扫描所有 blocked 的 dvcoder task"**
- 从 **title** 判断阶段（语义/算子），**不依赖 block reason 关键词**
- 加入中段 evaluator 已完成检测（SQLite 查重防重复创建）

## 修复后效果
任何 blocked 的 dvcoder task，只要该 round 无对应 evaluator task，下一个 10 分钟 tick 就会创建 evaluator task，不再等待。

## 位置
`${HERMES_HOME}/cron/jobs.json` → job `a-share-auto-pipeline` → `prompt` 字段。
