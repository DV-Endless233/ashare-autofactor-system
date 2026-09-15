# Cross-Round Pipeline Consolidation Audit

当需要对全部已探索轮次（R1-RN）做全面整合报告时，使用本模式。

## 触发条件

- 用户要求"把 R1-RN 的结果整合一下"
- 用户决定暂停自动 pipeline 并评估整体进展
- 需要盘点已通过的候选、失败的方向、重复撤回的方向

## 并行盘点方法

使用 `delegate_task` 启动 3 个并行子 agent，分别检查不同的数据源：

### 任务 A：盘点 `evaluator_passed/`
路径：`${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/`
- 每个子目录读取 `result/summary.md`（若有）
- 提取：方向名称、ICmean、IR、lsret、pass_count
- 标记：3/3 全达标 vs 2/3 条件性通过 vs 用户判定归档

### 任务 B：盘点 `review_queue/`
路径：`${PROJECT_ROOT}/factor_replicate_outputs/review_queue/`
- 列出所有子目录
- 读取 `result/summary.md`（若有）
- 提取方向、round 编号、指标、结论

### 任务 C：从 kanban 历史反查
- `kanban_list(limit=200)` 获取全部任务
- 对 evaluator 审查任务的 comments 提取结论
- 特别关注：3/3 通过轮次、2/3 接近轮次、0/3 关闭轮次、撤回轮次

### 执行参数
```
delegate_task(
  tasks=[
    {goal: "...", context: "...", toolsets: ["file"]},
    {goal: "...", context: "...", toolsets: ["file"]},
    {goal: "...", context: "kanban_list...", toolsets: ["file", "kanban"]},
  ]
)
```

## 整合报告结构

最终报告应包含：

1. **总体统计**：总轮次、3/3 通过数、2/3 接近数、0/3 失败数、重复撤回数
2. **已通过候选中**（3/3）：轮次、方向、公式、指标、存放路径
3. **接近达标候选**（2/3）：轮次、方向、最佳指标、差距分析
4. **已正式关闭方向**：按维度分组列出（经营杠杆、capex 效率、税负、SG&A 等）
5. **当前 pipeline 状态**：最新轮次、正在跑的阶段、暂停原因

## 手动编排步骤

当自动看门狗已暂停，需要手动推进剩余轮次时：

1. 确认两个看门狗已暂停：`cronjob(action='list')` → 检查 `state=paused`
2. 按需推进：
   - evaluator 预审 PASS → `kanban_create(title="R{N} 算子空间实现...", assignee="dvcoder", ..., skills=["a-share-factor-framework"])`
   - **必须传 skills 参数**，否则 dispatcher 可能不调度
3. 等 task 跑完（`kanban_show` 检查 status）
4. 若 dvcoder blocked → 创建 evaluator 审查 task
5. 等待 evaluator 完成
6. 评估结论是否需要继续

## 常见问题

### 重复任务
手动创建 task 时，可能会和 auto-decompose 或旧 watchdog 创建的 task 重复。
- 使用 `idempotency_key` 参数防重复
- 发现重复时：保留新版本（更新模型/配置），关闭旧版本

### 模型切换后验证
dvcoder 模型变更后：
1. 编辑 `${HERMES_HOME}/profiles/dvcoder/config.yaml` 中 `model.default`
2. 创建连通性测试 kanban task（小任务，仅验证连接）
3. 确认 agent 日志显示新模型名后再继续
