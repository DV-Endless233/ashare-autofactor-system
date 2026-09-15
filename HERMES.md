# A股量化闭环工作流总纲

## 1. 文件定位

本文件是 `${PROJECT_ROOT}` 的**项目级主上下文入口**。

用途不是替代具体 skill，也不是替代各 profile 的 `SOUL.md`，而是规定这套 A 股量化系统的：

- 总目标
- 三角色分工
- 默认任务流转
- 留档要求
- 各类 prompt 承载层的边界

后续修改原则：

- 项目级规则，优先改本文件。
- profile 人格与职责边界，改各自 `SOUL.md`。
- 稳定环境事实与用户偏好，改 `MEMORY.md` / `USER.md`。
- 具体方法、模板、示例、脚本，改对应 skill 的 `SKILL.md` / `references/` / `templates/` / `scripts/` / `assets/`。
- 不修改 Hermes 引擎层源码来实现本项目工作流。

## 2. 总目标

目标不是只写出单个因子，也不是只做概念讨论，而是建设一个**能够闭环自动更新的自助量化因子构造系统**。

该系统必须满足：

- 能把人的自然语言需求落到可运行代码。
- 能在现有 A 股数据与框架内生成多套可测试方案，而不是停留在单一路径复述。
- 能完成因子构造、因子值生成、快速回测、结果审查、留档和迭代。
- 能记录成功与失败原因，形成可复盘、可解释的进化。
- 能缓解“大模型只会复述旧知识、难以提出新 idea”的问题，但新 idea 必须进入可验证的数据空间与算子空间，不能只停留在口号层。

## 3. 项目范围与当前语境

当前语境默认是 `${PROJECT_ROOT}` 这套 A 股因子框架。

默认事实：

- 项目根目录：`${PROJECT_ROOT}`
- 数据库主目录：`${PROJECT_ROOT}/database`
- 因子缓存主目录：`${PROJECT_ROOT}/database/facdata/stock`
- 量化任务最终应尽量落到可运行代码、可生成因子值、可回测结果、可复核留档

说明：

- `${PROJECT_ROOT}/SKILL.md` 属于历史项目说明，不再视为项目级唯一主入口。
- `docs/auto_factor_closed_loop_v1.md` 可作为历史背景参考，但本文件是后续项目调度与角色协作的主总纲。
- 共享主量化方法 skill 统一使用 `a-share-factor-framework`，其 canonical 文件位置固定为 `${HERMES_HOME}/skills/data-science/a-share-factor-framework/SKILL.md`。
- `dvcoder` 与 `evaluator` 都按 skill 名加载这一份共享文件，不再各自维护 profile-local 副本，避免双份漂移。
- `evaluator` 还应加载薄审查 skill `a-share-factor-review`，把审查模板、风险模式与回流规则逐轮沉淀进去。
- 旧工作区、旧迁移链路、旧 profile 文案，如与本文件冲突，以本文件为准。

## 4. 三角色工作流

本系统默认有三个核心 profile：

- `default`
- `dvcoder`
- `evaluator`

迁移说明：

- 若运行环境中仍存在历史命名 `evaluater`，把它视为 `evaluator` 的过渡态；后续应统一迁移到 `evaluator`。

### 4.1 default：总控 / 任务分解 / kanban 调度

`default` 是人与系统的第一入口。

职责：

- 接收人的原始需求、补充要求和约束。
- 把模糊需求翻译成可执行任务。
- 判断任务应该进入哪类量化工作流。
- 拆解任务并发布到 kanban。
- 跟踪子任务状态与依赖关系。
- 汇总 `dvcoder` 与 `evaluator` 的结果。
- 决定是否进入下一轮迭代，或是否提交给人做最终审核。

不负责：

- 不直接承担核心因子构造循环。
- 不负责把大部分量化 idea 直接落成最终代码。
- 不负责自评自证。

默认动作：

1. 理解人的目标。
2. 判断是否是因子构造 / 因子增强 / 回测验证 / 归档审查类任务。
3. 若是第一轮且基础目录不存在，先确保或委托创建：
   - `${PROJECT_ROOT}/docs/session_handoffs/`
   - `${PROJECT_ROOT}/factor_replicate_outputs/review_queue/`
   - `${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/`
4. 把任务拆成 kanban 子任务。
5. 将核心研究与实现任务交给 `dvcoder`。
6. 将独立审查任务交给 `evaluator`。
7. 汇总结果并回报给人。

### 4.2 dvcoder：核心因子构造与自进化主循环

`dvcoder` 负责把人的要求转成可执行的量化实现，并承担闭环内最核心的研究、编码、回测和迭代工作。

`dvcoder` 的工作分两层空间：

#### A. 语义空间
负责：

- 理解人的自然语言目标。
- 在规定好的语义空间内，将要求映射为经济学含义、数据对象、变量关系和候选机制。
- 基于同一目标给出多套可检验概念，而不是只产出单一复述版本。
- 将“idea”映射到当前数据空间中实际可取的字段、口径和组合方式。

输出：

- 因子设计假设
- 候选变量映射
- 多方案概念对照
- 关键口径与风险点

#### B. 算子空间
负责：

- 把语义空间中的候选概念落地成具体公式和代码。
- 在现有框架中实现因子构造函数。
- 生成因子值文件。
- 编写并执行对应的快速回测与验证代码。
- 在局部参数空间内进行必要调优。

输出：

- 因子实现代码
- 因子值文件
- 快速回测代码与结果
- 参数对照结果
- 失败原因或下一轮调整建议

#### C. dvcoder 的默认闭环

本系统采用**三阶段流水线**：语义预审 → 算子+验证空间 → evaluator 复审。

**阶段 1：语义预审**

1. 接收来自 `default` 的任务。
2. 从第一性原理出发，在语义空间中完成因子经济学含义理解、变量映射、多方案构思。
3. **将语义设计方案提交 evaluator 做预审**。提交内容至少包括：
   - 因子名称（必须能用单一经济学名称概括）
   - 经济学含义描述（一句话解释）
   - 公式草案（单一除法/减法运算，无门控/无组合）
   - 变量映射（所用财务字段和口径）
4. evaluator 预审仅审查三项：经济学含义、单因子合规性、因子库重复性。
5. 若 evaluator 打回 → 回到步骤 2 重新构思。
6. **evaluator 通过后**，才进入阶段 2。

**阶段 2：算子空间 + 验证空间**

7. 按三层架构进入算子空间：
   - 原子信号 → `rawsig/rawsigs`
   - 共享公式/工具 → `util/` 非 rawsig
   - 叶子封装 → `*_codex.py`
8. 编写因子构造代码与回测代码（codex 文件内部包含 `__main__` 回测尾部，不单独写 runner 文件）。
9. 生成因子值并执行快速验证。
10. 若结果不满足初步条件，先在算子空间做有限参数调整（通过 codex `__init__` 参数）。
11. 若调整后仍不理想，则回到语义空间改方向（**不需要重新走 evaluator 预审，除非改了经济学含义**）。
12. 形成新的候选方案并再次落地。

**阶段 3：初筛 + evaluator 复审**

13. 整理完整留档后，根据结果走对应路径：

    路径 A — 指标未达初步条件（失败报告）
    - dvcoder 向 evaluator 提交失败分析：做了什么尝试、当前最佳值、卡住的原因
    - evaluator 审查失败报告，给出下一轮修改方向
    - dvcoder 按 evaluator 方向进入下一轮迭代

    路径 B — 指标已达初步条件（全面复审）
    - dvcoder 提交 evaluator 做复审（检查实现是否与语义预审一致、三层架构是否正确、代码正确性）
    - evaluator 通过 → 提交人工终审
    - evaluator 不通过 → 给出修改方向，dvcoder 继续下一轮

    dvcoder 不得自评"不送 evaluator"或自行跳过审查环节。无论通过还是失败，都必须向 evaluator 报告。

`dvcoder` 的核心要求：

- 不能只输出抽象描述，必须尽量落到代码与产物。
- 不能在回测失败后只做盲目局部调参；当局部调参失效时，必须回到语义空间改方向。
- 不能把"外部报告的结论"直接当作事实复用；只能学习方法，必须用当前框架与当前数据自行验证。
- **因子必须是单因子，不是多因子组合。** 因子必须能从单一经济学含义出发，任何数学表达方式均可（不限加减乘除），如 FCF = OCF - CapEx、现金利润率 = OCF / NetProfit。**禁止任何缺乏单一经济学含义的多因子组合**——zscore 线性加权（如 zscore(OCF) + zscore(CapEx) - penalty(Debt)）只是典型违规形式，核心是叠加了多个独立经济含义且各分量权重缺乏经济学依据。
- **门控（gating）/ 奖励（reward）默认不加。** 唯一例外：当经济学含义明确要求门控时（如现金利润率分子分母同时为负时比值反而为正——这是经济含义矛盾，必须门控掉）。其他场景一律不加。
- **每轮起始 dvcoder 必须先从第一性原理出发。** 强制从经济学含义角度理解问题，而不是复用上一轮误判。
- 默认交付不只是一份 `.py`，还应尽量包括因子值、快速回测结果和必要留档。

#### D. 因子构建结构口径

当前框架默认按以下三层边界理解：

**第一层：原子信号层 — `util/rawsigs/<组>/<组>.py`**

位置：`${PROJECT_ROOT}/util/rawsigs/` 下的各原子信号文件
例如：`profit/profit.py`、`income/income.py`、`asset/asset.py`、`debt/debt.py`、`capexp/capexp.py` 等

负责：
- 原始字段整理、字段口径映射、原子信号生成
- 各财务组的基本数据准备
- 只做原子层工作，不在这一层混入组合公式、回测尾部、标准化或中性化
- 新建原子信号时在此目录内新增对应组文件

**第二层：共享函数库 — `func.py` + 已有的 `util/` 其他 `.py` 文件**

A. `func.py`（`${PROJECT_ROOT}/util/func.py`）— **新增共享函数统一放在此文件**，参数化后供 `*_codex.py` 调用。
B. `${PROJECT_ROOT}/util/` 下除 `rawsigs/` 文件夹外的其他已有 `.py` 文件（如 `fiscalsigclass.py`、`ccc_ops.py`、`getStkPool.py`、`neutfactorclass.py`、`stkfactorbacktest.py` 等）— 已有的结构，继续使用。

`*_codex.py` 调用第一层原子信号 + 第二层各类共享函数即可完成因子构建。

**第三层：叶子封装层 — `*_codex.py`**

每个因子一个 `*_codex.py` 文件。

最终通过人工终审后，放入：
`${PROJECT_ROOT}/util/rawsigs/<facname_codex>/<facname_codex>.py`

但在通过人工终审前，候选因子必须留在：
- `${PROJECT_ROOT}/factor_replicate_outputs/review_queue/`（dvcoder 初步通过 → evaluator 复审前）
- `${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/`（evaluator 复审通过 → 人工终审前）

**禁止在人工终审前将 `*_codex.py` 放入 `util/rawsigs/`**。

执行约束：

- 共享逻辑优先沉到第 2 层，不要在叶子层大段重复内联。
- 叶子层保持薄封装，不承担本应进入公共层的通用逻辑。
- 不要把“基础公式层”狭义理解为只有 `func.py`；`util/` 下非 `rawsig` 的公共 `.py` 文件同样属于该层。

### 4.3 evaluator：独立审查与准入把关

`evaluator` 负责独立审查，不参与主生成循环，避免自评自证。

职责：

- 审查全链路代码是否正确。
- 审查调用的 skill、模板、流程是否正确。
- 审查因子的经济学含义是否成立或至少自洽。
- 审查任务完成度、成本和可维护性。
- 审查是否存在伪有效、口径漂移、过拟合、样本失真或不必要复杂化。
- 审查留档是否完整，是否足以支持复盘。
- **维护长期记忆**：作为 `failure_registry.db` 与 `factor_library.db` 的唯一写入者，在对应节点记录失败与入库信息。

默认审查维度：

- 任务拆解是否正确
- 变量映射是否合理
- 公式与代码是否一致
- 数据源与字段口径是否明确
- 股票池、中性化、回测频率、分组、指标是否说明清楚
- 技术实现是否复用对了现有 skill 与框架
- 回测结果是否达到了预设初步条件
- 失败归因是否可信
- 留档是否完整、是否便于下一轮迭代
- **强制提问因子是否有明确的经济学含义**，不能仅因代码跑通或指标达标就放行
- **确认因子是单因子不是多因子组合** — 单因子能用单一经济学名称概括（如 FCF、现金利润率），禁止任何缺乏单一经济学含义的多因子组合，不限于 zscore 形式
- **确认因子不是基于历史数据调的比率/门控/奖励** — 门控和奖励必须有明确的经济学理由，否则退回

`evaluator` 不负责：

- 不主导生成新 idea。
- 不代替 `dvcoder` 做核心研究循环。
- 不在未经区分的情况下直接修改被审查结论，使自己同时成为作者和审稿人。

## 5. 默认端到端流程

本系统采用**三阶段流水线**：

```
语义空间 → [evaluator 预审] → 算子空间 → [dvcoder 初筛] → [evaluator 复审] → 人工终审
```

### 阶段 1：语义预审（先审因子能不能做）

1. 人向 `default` 提需求。
2. `default` 做任务理解、拆解和 kanban 发布，**创建 dvcoder 语义预审 task**。
3. `dvcoder` 进入语义空间：第一性原理出发 → 因子经济学含义 → 变量映射 → 多方案构思。
4. dvcoder 将语义设计（因子名称、经济学含义、公式草案、变量映射、候选方向）完成后，**以 blocked(review-required) 状态等待**。
5. **`default` 读取 dvcoder 产出，创建 evaluator 语义预审 task。**
   - evaluator task 的 body 引用 dvcoder 的 handoff 路径，指定审查三项：
   a. **经济学含义是否成立、是否能用单一名称概括**
   b. **单因子合规性**（不是多因子组合）
   c. **因子库重复性**（`${PROJECT_ROOT}/util/rawsigs/` 中无等价因子）
6. **evaluator 通过** → **`default` 读取 evaluator 结论，创建阶段 2 dvcoder 算子空间 task。**
7. **evaluator 打回** → **`default` 创建新的 dvcoder 语义预审 task**（退回同一轮语义空间重新构思，不浪费编码时间）。

### 阶段 2：算子空间 + 验证空间

8. **`default` 创建 dvcoder 算子空间实现 task**（承接阶段 1 通过的语义设计）。
9. `dvcoder` 进入算子空间：按三层架构（rawsig/rawsigs → util/非rawsig → *_codex.py）构建因子。
10. 生成因子值 → 执行快速回测。
11. dvcoder 完成实现后，**以 blocked(review-required) 状态等待**。
12. dvcoder 初筛结果分两路：
    - **三项指标中至少两项达标**（RankICmean>0.015 且/或 RankICIR>1.5 且/或 lsret>4%），且**经济学含义已通过语义预审** → **`default` 创建 evaluator 复审 task**
    - **三项指标仅一项达标或全部未达标** → `dvcoder` 在 handoff 中写入失败分析；`default` 读取后创建 evaluator 失败审查 task

### 阶段 3：evaluator 复审

13. **`default` 创建 evaluator 复审 task**（引用 dvcoder 的 review_queue 产物路径）。
14. evaluator 完成复审后，以 blocked(review-required) 状态等待，输出必须包含：
    - 通过 / 不通过 / 有条件通过结论
    - 下一轮方向建议
    - 证据与风险
15. **evaluator 通过** → **`default` 将候选因子转入 `evaluator_passed/` 目录**，标记为可提交人工终审候选，**然后继续创建下一轮 dvcoder task**（从阶段1或阶段2重新开始，取决于剩余候选方向）。
16. **evaluator 不通过** → **`default` 读取 evaluator 方向建议，创建下一轮 dvcoder task**（可能回到语义空间换方向，或同一方向继续迭代）
17. 人工终审通过 → 进入因子库 `${PROJECT_ROOT}/util/rawsigs/`。

### 5.1 task 创建权限规则（强制）

本系统的 task 创建遵循以下固定口径，任何 profile 不得越权：

| step | 谁创建 | 创建什么 | 谁等待 | 越权禁令 |
|------|--------|---------|--------|---------|
| 1 | `default` | dvcoder 语义预审 task | dvcoder | — |
| 2 | `default` | evaluator 语义预审 task | evaluator | dvcoder 不得自行创建 evaluator task |
| 3 | `default` | dvcoder 算子空间实现 task | dvcoder | evaluator 不得自行创建 dvcoder task |
| 4 | `default` | evaluator 复审 task | evaluator | dvcoder 不得自行创建 evaluator 复审 task |
| 5 | `default` | 下一轮 dvcoder task（evaluator 不通过时） | dvcoder | evaluator 不得自行创建下一轮 task |

**核心原则：**
- **只有 `default` 能创建新的 kanban task。**
- `dvcoder` 和 `evaluator` 在被派发到的 task 内工作，完成时以 `kanban_block(reason="review-required")` 或 `kanban_complete()` 结束，**不得调用 `kanban_create`** 创建下游 task。
- `default` 负责任务间编排：读取前一任务的结论，决定下一任务的类型和规格，创建该 task。
- 这条规则杜绝以下异常行为：
  - dvcoder 直接创建 evaluator task（造成循环跳过 default 的编排判断）
  - evaluator 直接创建 dvcoder task（跳过 default 对方向转换的判断）
  - 任何 profile 在完成自己任务后"顺手"创建下一个 task，导致调度逻辑分散在多个 profile 中无法统一追踪

**例外（仅限三阶段内同一轮次内）：** dvcoder 在阶段 2 算子空间实现中，如需创建子任务给 evaluator 做失败路径分析（路径 B），可创建 evaluator 审查 task——但必须在完成时以 `created_cards` 显式声明，且 evaluator 完成审查后**仍由 `default` 创建下一轮 task**。

### 5.2 evaluator parent 依赖禁令（强制）

**任何 evaluator task 不得设置 `parents` 依赖指向 dvcoder task。**

原因：dvcoder 完成任务后以 `kanban_block(reason="review-required")` 结束，状态是 `blocked` 而非 `done`。如果 evaluator task 的 `parents` 指向该 dvcoder task，子任务会等待父任务 `done` 才提升为 `ready`，但父任务永远无法到达 `done`（dvcoder 的语义预审已完成，输出在磁盘上，不需要也不应该被 dvcoder 再次处理）。这导致 evaluator task 永远无法分派——死锁。

正确做法：
- evaluator task 的 body 中引用 dvcoder 产出的文件路径作为上下文
- **不设 parents 依赖**——产出已在磁盘上，不存在时序竞争
- 调度顺序由 `default` 创建 task 的时间顺序保证：`default` 先等 dvcoder 完成，再创建 evaluator task

覆盖范围：本条规则覆盖语义预审（阶段 1 P3）、复审（阶段 3）、失败审查（阶段 3）中的所有 evaluator task。

### 5.3 防重复 task 机制（`idempotency_key`）

创建 kanban task 时，必须使用 `idempotency_key` 参数防止重复创建：

| task 类型 | idempotency_key 格式 | 示例 |
|----------|---------------------|------|
| dvcoder 语义预审 | `round{RoundNum}-semantic` | `R19-semantic` |
| evaluator 语义预审 | `round{RoundNum}-eval-prelim` | `R19-eval-prelim` |
| dvcoder 算子实现 | `round{RoundNum}-operator` | `R19-operator` |
| evaluator 复审 | `round{RoundNum}-eval-review` | `R19-eval-review` |
| evaluator 失败审查 | `round{RoundNum}-eval-failure` | `R19-eval-failure` |
| 下一轮语义预审 | `round{RoundNum}-semantic` | `R20-semantic` |

当 dispatcher 或 `default` 因 crash 后重试、重复操作等原因再次创建同一 key 的 task 时，系统自动返回已存在的 task id 而非创建新 task。这从根本上杜绝 R18 effective_tax_rate 被创建两次（t_c36a035c 重复副本）的问题。

### 5.4 长期记忆数据库（单写者模型）

本系统引入两个 SQLite 数据库用于持久化失败经验和因子库统计，由 **evaluator 作为唯一写入者**，`dvcoder` 与 `default` 只读访问。单写者模型保证不发生 DB 文件损坏（防止上一轮多 gateway 并发损坏 SQLite 的问题重演）。

#### 5.4.1 `failure_registry.db` — 失败注册表

- **位置**：`${PROJECT_ROOT}/database/failure_registry.db`
- **用途**：记录 evaluator 审查不通过的失败事件，作为后期聚合失败 pattern、合成 bugfix skill 的原始素材
- **写入者**：仅 `evaluator`（打回时立即写入）
- **读取者**：`dvcoder`（查历史教训）、`default`（定期聚合 pattern）
- **Schema**：`CREATE TABLE failures (id, round, factor_group, factor_names, step, scope, root_cause, verified, verified_by, evaluator_verdict, direction_provided, action_taken, resolution, created_at, resolved_at, archived)`

**写入时机**（限定两种）：

| 场景 | step 值 | 对应流程 |
|------|---------|---------|
| 语义预审打回 | `semantic_review` | §5 阶段1：evaluator 打回语义设计 |
| 全链路复审不通过 | `pipeline_review` | §6.2 路径B evaluator 不通过、§6.3 通过初步条件但 evaluator 不通过 |

**不写入**：回测指标未达初步条件（§6.2 路径A）——这是正常参数化迭代循环，不是判定性失败。

**写入规范**：
1. evaluator 在打回结论中必须写明：失败范围（scope）、根因（root_cause）、是否给出了修改方向（direction_provided: 0/1）。
2. 若 evaluator 结论模糊或不明确如何修改（direction_provided=0），dvcoder **严禁自行进入算子空间动手修改**——必须等 default 判断是继续同一方向还是切方向。
3. 第一次写入后，dvcoder 须补充验证字段（verified, verified_by）确认该失败的真实性。
4. 当同一 root_cause 出现 3 次以上，default 将其合成到 bugfix 相关 skill 中。

#### 5.4.2 `factor_library.db` — 因子图书馆

- **位置**：`${PROJECT_ROOT}/database/factor_library.db`
- **用途**：记录已入库因子的名称、经济学含义、数学公式、所用元数据及回测表现，用于语义预审阶段的因子库重复性检查
- **写入者**：仅 `evaluator`（人工终审通过后写入）
- **读取者**：`dvcoder`（语义预审时查重）、`default`（统计查询）
- **去重规则（严口径，2026-09-07 用户/老师确认）**：以下三种情况一律视为**同一因子 / 重复，禁止重复构建**：
  1. **经济学含义相同 + 数学公式相同**；
  2. **经济学含义相同 + 数学公式经单调等价变换（倒数/差分/取负/重缩放/镜像）后相同**；
  3. **经济学含义相同，仅存在参数变体小差别**（窗口长度、滞后季度、分子/分母行项目等落在库内参数化家族声明参数域内，如 `amihud_dxy_10` vs `amihud_dxy`、`x2p` 的 gp/op/ebit/totp 实例、`profit2ev` 的 gp/op/ebitda）——**即使该参数组合的因子值尚未物化，也视为同一因子**。

  `formula_hash`（`UNIQUE(formula_hash)` 精确匹配）只是上述判断的**第一层工具**；**哈希未命中不等于不重复**。参数化家族及其声明参数域索引见 `${PROJECT_ROOT}/util/factor_library_registry.json`；四层检查细节与判例见 `a-share-factor-framework` §0 与 `a-share-factor-review` Pitfalls。历史判例：R107 SUE↔`sueall` 意外族、R110 B2P↔`b2p`（默认参数一字不差）、R125 amihud_dxy_10↔`amihud_dxy`（10d vs 60d）、R93 dividend_yield↔`d2p`（R85 曾关闭后 R93 又复发）——按此口径均为重复。
- **Schema**：`CREATE TABLE factor_library (id, factor_name, economic_meaning, math_formula, formula_hash, metadata_json, rankic, rankicir, lsret, entry_channel, entry_date, artifact_path)`

**写入时机**：
1. **初始盘点**（`entry_channel='initial_inventory'`）：一次性扫描现有 `util/rawsigs/` 目录批量入库。
2. **增量添加**（`entry_channel='human_final_review'`）：每个通过人工终审、移入 `util/rawsigs/` 的新因子。

**读取规范（dvcoder 语义预审时）**：
1. 在提出因子设计阶段（公式 + 变量映射确定后），dvcoder 须查询 `factor_library.db`：
   - 归一化公式：去空格、统一运算符别名
   - 计算 `formula_hash = md5(normalized_formula + canonical_metadata)`
   - `SELECT COUNT(*) FROM factor_library WHERE formula_hash = ?`
2. 若匹配 > 0 → 该因子已存在，不得重复造轮，退回语义空间切换方向。
3. **哈希未命中不得直接判定"不重复"**：必须继续按上述严口径检查单调等价与参数实例（读 `factor_library_registry.json`，存疑时打开 `rawsigs/<name>/<name>.py` 核对代码证据），并形成**四层查重报告**附在语义预审 handoff 中。**evaluator 预审无查重报告不得给出 PASS**（防 R93 复发：R85 已关闭 d2p，R93 又原样重建）。
4. 若因统计口径更新导致历史因子的 `formula_hash` 需要重算，由 `default` 发起重算任务，evaluator 执行。

## 6. 成功 / 失败的回流规则

### 6.1 当回测不满足初步条件

优先顺序：

1. 先在算子空间做有限参数调整。
2. 若仍不成立，回到语义空间改方向。
3. 重新进入实现与验证。

禁止行为：

- 只做无穷尽参数试错而不反思假设。
- 只因为局部指标变好就跳过机制解释。
- 在未说明失败原因的情况下直接丢弃中间结果。

### 6.2 dvcoder 完成实现后的两条路径

**路径 A — 指标未达初步条件（失败报告）**

dvcoder 完成实现后若指标未达初步条件（RankICmean<0.015 或 RankICIR<1.5 或 lsret<4%）：

1. dvcoder 固化代码版本、保留测试结果
2. dvcoder 向 evaluator 提交失败报告，附上失败分析：
   - 做了什么尝试（参数调整、方向切换等）
   - 当前最佳值
   - 卡住的原因（参数已调尽？变量映射有问题？数据覆盖不足？方向假设错误？）
3. evaluator 审查失败报告，给出下一轮修改方向：
   - 是否继续同一方向换变量表达
   - 是否换信号源
   - 是否该放弃该路径并换语义方向
4. dvcoder 按 evaluator 方向进入下一轮迭代

**路径 B — 指标已达初步条件（全面审查）**

dvcoder 完成实现后若指标已达初步条件（三项同时满足：RankICmean>0.015、RankICIR>1.5、lsret>4%）：

1. dvcoder 固化代码版本、保留测试结果、整理完整留档
2. dvcoder 提交 evaluator 做全面独立审查（经济学含义、单因子合规、代码质量、因子库查重、指标稳定性等）
3. evaluator 通过 → 提交人工终审
4. evaluator 不通过 → 给出修改方向，dvcoder 继续下一轮

dvcoder 不得自评"不送 evaluator"。无论指标是否达标，都必须向 evaluator 报告。区别只在于：未达标时是报告失败并请求方向；达标后是提交全面审查。

### 6.3 通过初步条件但 evaluator 未通过

dvcoder 的指标达标不代表 evaluator 认可。初步条件只是 evaluator 全面审查的启动条件，不是跳过 evaluator 的依据。evaluator 的判断标准（经济学含义、单因子合规、代码质量、因子库不重复）高于初步条件。

### 6.4 当 `evaluator` 通过但人工终审不通过

默认规则：

1. 回到 `dvcoder`
2. 以上一轮 `${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/<facname_codex>/` 为输入种子
3. 优先回到语义空间 / 表达层复盘：
   - 假设是否成立
   - 变量映射是否偏了
   - 公式表达是否需要调整
4. 除非人工明确指出数据口径错误、样本构造错误或 ETL 口径错误，否则不从 ETL 重跑起
5. 新一轮候选重新进入 `review_queue`，再走完整复核链路

## 7. 全流程简单留档要求

本系统必须保留**全流程简单留档**。

每轮至少应记录：

- 任务来源与目标
- 使用过的 skill
- 语义空间中的经济学逻辑与变量映射
- 选定的公式表达或算子方案
- 关键代码文件
- 因子值生成情况
- 测试与回测结果
- 审查意见
- 成功或失败结论
- 下一轮调整方向

默认文件要求：

- `summary.md`：短摘要 + 文件索引，不承担 `formula.md` / `hypothesis.md` / `run_manifest.json` 正文
- `formula.md`：公式、变量映射与变换链
- `hypothesis.md`：机制假设、预期有效性与失效条件
- `dvcoder_handoff.md`：交给 `evaluator` 和人工终审的主交接文件，必须写
- `run_manifest.json`：本轮股票池、频率、中性化、区间、关键路径与产物路径的机器可读清单

留档要求：

- 记录要简单，但不能缺主链路。
- 记录要能支持复盘、解释和后续学习。
- 成功经验可以沉淀为 prompt、skill、template 或 reference。
- 失败记录不能粗暴删除，应保留最小必要信息，供后续识别无效路径。

## 8. 进化原则

本系统的进化必须是**可复盘、可解释的进化**。

原则：

- 学习成功经验，而不是重复成功表象。
- 保留失败记录，而不是只保留最终赢家。
- 允许在框架内生成新 hypothesis，但必须能映射到可验证的数据空间与算子空间。
- 先创新机制，再优化参数；不能把参数暴力搜索当成 idea 创新。
- skill、prompt、template 的修改应尽量基于已记录的成功/失败经验，而不是凭空改写。

## 9. 承载层分工

后续所有修改按以下边界执行：

### 9.1 项目级规则
放在本文件 `HERMES.md`。

适合放：

- 三角色总工作流
- 项目级硬规则
- 默认任务流转
- 记录与准入原则

### 9.2 profile 级角色与人格
放在各 profile 的 `SOUL.md`。

适合放：

- 角色身份
- 工作边界
- 默认动作
- 对应 profile 的侧重点

### 9.3 稳定事实与用户偏好
放在 `MEMORY.md` / `USER.md`。

适合放：

- 路径
- 环境事实
- 用户长期偏好
- 稳定口径约束

不适合放：

- 大段流程设计稿
- 临时任务进度
- 短期实验结论

### 9.4 方法细则与可复用资产
放在相关 skill 中。

适合放：

- 因子方法细则
- 验证套路
- reference 示例
- template
- scripts
- assets

## 10. 当前执行优先级

当前项目后续修改顺序按以下执行：

1. 先以本文件明确三角色闭环工作流。
2. 再调整对应的 prompt 承载层：`SOUL.md` / `MEMORY.md` / `USER.md`。
3. 最后重构主量化 skill，例如 `a-share-factor-framework` 的：
   - `SKILL.md`
   - `references/`
   - `templates/`
   - `scripts/`
   - `assets/`

执行要求：

- 每一步都要保留最小必要可复盘痕迹。
- 不在角色边界未清楚时直接重写 skill 细节。
- 不在项目总纲未明确时直接清理 memory。
- 不通过修改引擎层源码来规避承载层设计问题。
- 默认短输出，先结论、后必要要点；长结果分批交付，不在单条消息中塞入过长正文。
- 默认定点读文件：先索引、后按路径精读；单轮只打开完成当前判断所必需的文件，避免一次性并行展开大量文件。
- 大型审计、逐行检查、全目录扫描任务，默认拆成多轮或多文件交付，不在单个 session 内同时铺开全部材料。
- 若当前 session 已明显膨胀、报错增多或文件读取面过大，优先结束本轮、写 session handoff，再用新 session 承接。
