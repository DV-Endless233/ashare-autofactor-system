# dvcoder Profile 成本优化决策记录

> 适用范围：当需要调整 `${HERMES_HOME}/profiles/dvcoder/config.yaml` 中的模型、推理、上下文等设置时。
> 本文件记录每个配置项的节约效果与风险边界，避免凭直觉改动导致因子质量下降或任务失败。

## 核心原则

**省 token 不能以牺牲语义质量为代价。** dvcoder 的主要价值产出在语义空间探索阶段（因子构思、经济学含义推理、第一性原理推导），这一阶段需要 deep reasoning。算子空间实现阶段（写 codex 代码、跑回测、格式化文档）只需要中低度推理，但不支持按阶段区分。

因此：全局性改动必须保守，只在确定性安全的局部做优化。

---

## 配置项逐一分析

### 1. `agent.reasoning_effort: high` → 不可动

**当前值：** high
**风险：** 高

**理由：** dvcoder 的语义空间探索阶段依靠 deep reasoning 从第一性原理出发做经济学含义推理、变量映射和因子设计。这是整个系统的价值起点。降到 medium 会导致它倾向于从 skill 文本中套现成公式而不是做独立因果推理，因子新颖性下降。算子空间阶段虽然不需要 high，但 setting 是全 profile 统一的，无法按阶段拆分。

**之前的降级（gpt-5.5 → gpt-5.4）已经保留了 reasoning_effort: high，说明当时有意识地保留了推理深度。**

### 2. `delegation.reasoning_effort: high` → 安全可降

**当前值：** 已从 high 改为 low（本 session）
**风险：** 低

**理由：** dvcoder 通过 `delegate_task` 分配给子 agent 的任务全是机械性操作：
- 跑回测脚本（跑完取 stdout）
- 读 CSV 输出做数值检查
- 查数据库字段是否可用
- 格式化 handoff 文档
- 计算重复性检查的 formula_hash

这些不需要深层因果推理。deepseek-v4-flash 做 low 模式完全够用。之前设为 high 是遗漏。

### 3. `agent.max_turns: 90` → 保守可降

**当前值：** 已从 90 改为 70（本 session）
**风险：** 中等

**理由（基于历史数据）：**
- 典型 dvcoder kanban task 使用 20-35 turns
- 遇到需要 debug（DB 查错、回测异常、代码修 bug）时额外 +5-10 turns
- handoff 文档生成 +3-5 turns
- 50 对复杂轮次太紧（容易超 turns 掉线 → 重跑更费 token）
- 65-70 留 2x 余量，安全且省 ~22%

**降前检查：** 先确认已无 running task 再改，否则当前任务会因配置热加载中断。

### 4. `model.context_length: 272000` → 绝对不可降

**当前值：** 272000（OpenAI Codex 上限）
**风险：** 极高

**理由：** `a-share-factor-framework` skill 文件本身已经 ~250K+ chars（含所有 references 的导航、三层结构口径、执行闭环）。加上 HERMES.md、task body、memory、历史 turn——窗口已经压得很紧。用户已反馈 "经常报错 272000 不够"。

降到 96K 的结果：skill 都塞不下 → 每次请求 context 超长被拒 → task 失败 → dispatcher 重试 → 重试又失败。**比现在更费 token。**

### 5. `compression.target_ratio: 0.25` → 边际收益忽略

**当前值：** 0.25（threshold 0.5，protect_last_n: 12）
**建议：** 不动

**理由：** compression 只在 context 使用超过 50% 时触发（~136K+ tokens）。当前 `protect_last_n: 12` 保护最近消息（关键的 handoff/便利贴）。从 0.25 降到 0.15 意味着更激进的压缩 → 丢失更多历史细节（上一轮的 field_availability.md 等参考信息）。而问题是**绝对体积**（skill + prompt 本身就大），不是压缩率。边际收益极小。

---

## 开销热力图

| 配置项 | 省钱效果 | 风险等级 | 结论 |
|--------|---------|---------|------|
| `agent.reasoning_effort` | 🔥🔥🔥 最大头 | 🔴 影响语义质量 | **不动** |
| `delegation.reasoning_effort` | 🔥🔥 子任务省推理 | 🟢 安全 | **已改为 low** |
| `max_turns` | 🔥 少跑 22% 轮次 | 🟡 适中 | **已改为 70** |
| `model.context_length` | — | 🔴 272000 已吃紧 | **不动** |
| `compression.target_ratio` | 边际 | 🟡 损失历史细节 | **不动** |

---

## 改动流程

1. **改前必须确认当前无 running task** — 通过 `kanban_list(status="running")` 检查
2. **仅修改 `config.yaml` 中对应字段**，不改其他 profile
3. **改后触发管道推进器**：`cronjob(action="run", job_id="7700f19354a6")` 或者等 10 分钟自动 tick
