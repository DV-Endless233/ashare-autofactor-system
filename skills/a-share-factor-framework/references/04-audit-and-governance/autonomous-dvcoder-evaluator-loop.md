# 自治 dvcoder→evaluator 多轮迭代循环模式

## 概览

此模式实现了 dvcoder（实现）与 evaluator（审查）之间的自治迭代循环，无需人工在每轮之间干预。default 作为编排者，通过 kanban 任务链自动推进。

## 循环结构

```
default 创建 dvcoder 任务
    → dvcoder 运行 N 轮 + 整理留档
    → 根据指标是否达标走两条路径：

    路径 A — 指标未达初步条件（失败报告）
    → dvcoder 向 evaluator 提交失败分析（做了什么尝试、当前最佳值、卡住原因）
    → evaluator 审查失败报告，给出下一轮方向
    → default 读取 evaluator 输出，创建下一轮 dvcoder 任务
    → 循环...

    路径 B — 指标已达初步条件（全面审查）
    → dvcoder 提交 evaluator 做全面独立审查
    → evaluator 通过 → 提交人工终审，循环结束
    → evaluator 不通过 → 给出修改方向，dvcoder 继续下一轮
    → 循环...

最终由 default 汇总结果给人
```

## 各角色职责

### default（编排者）

1. **创建初始 dvcoder 任务** — 在 task body 中写清楚：
   - N 轮的工作范围（如 R1-R3）
   - 每轮的具体目标
   - 硬规则（单因子、门控、第一性原理、门槛）
   - 回测口径
   - 验收标准
   - 产物输出目录

2. **将任务转换为 evaluator 任务** — 当 dvcoder 任务 blocked(review-required) 时：
   - 读取 dvcoder 的评论/交接信息，了解候选因子详情
   - 完成 dvcoder 任务（kanban_complete），用 metadata 记录关键指标
   - 创建 evaluator 任务，body 包含：
     - 审查入口路径（review_queue/<facname>/）
     - 必须执行的审查步骤（经济学含义、单因子、门控审查等）
     - **必须要求 evaluator 在结论末尾输出 `## 下一轮方向建议` 章节**

3. **读取 evaluator 输出，创建下一轮 dvcoder 任务** — 当 evaluator 任务完成时：
   - 读取 evaluator 的评论/handoff，提取下一轮方向建议
   - 将 evaluator 的输出作为下一轮 dvcoder 任务的上下文
   - 创建新的 dvcoder 任务，引用 evaluator 的审查结论

4. **循环出口条件** — 当满足以下任一条件时停止 loop：
   - evaluator 认为候选可提交人工终审（审查结论为通过）
   - evaluator 和 dvcoder 均确认某方向已 plateau，无继续迭代价值
   - 用户人工介入要求停止

5. **报告** — 循环结束时，default 汇总各轮结果给人的通道（Telegram）

### dvcoder（实现者）

1. **第一性原理启动** — 每轮开始时先说"从第一性原理出发"
2. **语义空间 → 算子空间** — 先定义经济学含义，再写代码
3. **N 轮连续运行** — 按 task body 中的轮次规划连续执行
4. **各轮独立交付** — 每轮产生独立代码/因子值/回测/留档
5. **整理完整留档** — summary.md + formula.md + hypothesis.md + dvcoder_handoff.md + run_manifest.json
6. **根据结果走对应路径**：
   - **路径 A（指标未达标）**：向 evaluator 提交失败分析（做了什么尝试、最佳值、卡住原因），在 kanban 评论中输出结构化 handoff（JSON 格式），然后 kanban_block(reason="review-required: failure-report ...")
   - **路径 B（指标已达标）**：选出通过门槛的候选放入 review_queue，在 kanban 评论中输出结构化 handoff（JSON 格式），然后 kanban_block(reason="review-required: full-review ...")

### evaluator（审查者）

1. **读规则** — 先读 HERMES.md + a-share-factor-framework + a-share-factor-review
2. **审查三步**（每步强制执行）：
   - 因子是否有明确的经济学含义？
   - 因子是单因子还是多因子组合？
   - 因子是否基于历史数据调整的比率/门控/奖励？
3. **根据接收的路径类型给出结论**：
   - **路径 A（失败报告）**：审查失败分析，给出下一轮方向（继续/换方向/放弃），不需要走完整审查流程
   - **路径 B（全面审查）**：执行完整审查流程，给出通过/不通过/有条件通过
4. **提供下一轮方向** — 在结论末尾的 `## 下一轮方向建议` 章节中给出：
   - 本候选是否可进入人工终审
   - 如需继续迭代，建议的改进方向
   - 如已足够，下一个探索的单因子主题

## 关键约束

### 路径判断门槛

dvcoder 根据以下指标判断走路径 A 还是路径 B：
- 路径 B（全面审查）要求三项同时满足：RankICmean > 0.015（1.5%）、RankICIR > 1.5、lsret > 4%
- 任意一项不达标则走路径 A（失败报告）

### 产物目录
- dvcoder 的输出放在 `new_single_factor_rounds/<task_id>/` 
- evaluator 的审查入口在 `review_queue/<facname>/`
- 审查通过后转入 `evaluator_passed/<facname>/`
- 所有路径必须写 handoff 文件到 `docs/session_handoffs/`

### 禁止行为
- dvcoder 不能自行决定"不送 evaluator" — 无论指标是否达标，都必须向 evaluator 报告。未达标走失败报告路径，达标走全面审查路径
- evaluator 不能自行决定下一轮方向而不留下书面建议 — 必须写在 kanban 评论中
- default 不能跳过 evaluator 直接让 dvcoder 继续下一轮
- 不能把多个不相关的单因子拼在一起当复合因子提交
