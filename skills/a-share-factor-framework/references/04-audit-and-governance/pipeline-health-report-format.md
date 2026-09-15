# Pipeline Health Report Format

当用户询问"工作到哪一轮了"或"中间有卡住吗"时，默认以以下 4 项结构化报告回应。

## 标准 4 项检查

1. **当前轮次** — 最新活跃 task 的 round 编号 + 阶段 + 状态。格式：`R{num}（{方向名}）— {状态}`
2. **卡住情况** — 是否有超过 30 分钟无进展的 blocked 任务，及其根因（看门狗丢失、DB 损坏、等待人工确认等）
3. **DB 损坏** — 当前 `${HERMES_HOME}/kanban.db` 的 integrity_check 结果。如果有损坏，说明修复时间和方法
4. **协议违规** — 是否有 profile 退出时未调用 `kanban_complete()` 或 `kanban_block()` 的情况

## 报告时机

- 用户明确问"到哪了"时
- 用户消息间隔超过 1 小时，返回时默认先检查
- 每次手动修复管道问题后，附带当前状态摘要

## 看门狗(Cron)状态检查

每次检查管道健康时，额外确认看门狗是否存活：

```
cronjob(action='list') → 检查 a-share-auto-pipeline 是否 enabled=True, next_run_at 在未来
```

看门狗状态丢失的根因通常是 `repeat` 参数默认=1。修复：修改 `${HERMES_HOME}/cron/jobs.json` 中对应 job 的 `repeat.times` 为 `null`。

## 示例输出格式

```
## 1. 到 R{num}（{方向}），{状态}

{简要时间线}

## 2. 卡住情况
{无 / 有，根因，修复}

## 3. DB 损坏
{无 / 有，修复时间}

## 4. 协议违规
{无 / 有，次数，根因}
```
