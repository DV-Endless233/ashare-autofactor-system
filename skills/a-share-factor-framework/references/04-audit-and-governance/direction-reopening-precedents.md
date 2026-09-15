# 方向重开判例与规则细化

本文件记录 default pipeline 在执行方向校验规程时遇到的非平凡重开判例。当 evaluator 的建议方向均被 `failure_registry.db` 标记为关闭，管道的重开决策记录在此，供后续类似场景对照。

## 核心区分：关闭类型决定重开空间

方向关闭分为**两类**，重开的难易度不同：

### 类型 A：Duplicate 关闭（公式已入库）

- 特征：`step='semantic_review'`，`root_cause` 包含"与已有 XX 完全重复"
- 判定范围：**公式级别的精确匹配**（含单调等价变换）
- **重开空间：大** — 只关闭了该公式，同经济学方向下的不同表达式（如不同分子、不同分母、不同窗口）**未被关闭**
- 前提：新表达式必须在 `factor_library.db` 中无 `formula_hash` 精确匹配

### 类型 B：0/3 或 Pipeline 关闭（方向已测试失败）

- 特征：`step='pipeline_review'`，`root_cause` 包含"IC~0.002"、"weak signals"、"结构性问题"等
- 判定范围：**经济学方向级别的关闭** — 即使换表达式/分母/窗口，仍视为同一方向
- **重开空间：小** — 除非 evaluator 明确标注"可换表达式重新尝试"或属于 CONDITIONAL_PASS+数据阻塞
- 依据：common pitfalls 中"方向重复陷阱"规则——"被关闭的是经济学方向而非具体公式"

### 类型 C：Data Coverage 关闭（数据结构性不足）

- 特征：`step='pipeline_review'`，`root_cause` 包含"数据覆盖不足"、"valid_ratio"、"结构性覆盖"
- 判定范围：与分子/分母无关的数据源自身问题
- **重开空间：取决于数据问题是否可绕过** — 如限定 post-2019 子样本、等待数据扩源、使用替代代理变量等
- 注意：分母变化（asset → revenue）不会解决分子数据源本身的问题，除非数据覆盖仅针对特定分母的计算口径

## 判例 1：R92 R&D Intensity（2026-07-27）

### 场景

R91 evaluator 复审通过（short_term_debt_cash_coverage, conditional_pass）后，方向校验发现所有 3 个建议方向均关闭：
- **Primary**: R&D Intensity (rdexp_ttm/totopinc_ttm)
  - R68: **duplicate 关闭** — rdexp_ttm/totasset_bs == 已有 rdexp2at（step=semantic_review）
  - R83: **data coverage 关闭** — rdexp 数据覆盖率 < 50% pre-2019（step=pipeline_review）
- **Alt1**: Asset Growth Rate (Δtotasset_bs)
  - R57: **0/3 关闭** — IC=-0.011~-0.009, IR=-0.72~-0.45（step=pipeline_review）
- **Alt2**: Total Debt/Equity
  - R66/R67: **pipeline 关闭** — financial_leverage_level, IC~0.002（step=pipeline_review）

### 重开决策

按方向校验规程中的优先级规则（CONDITIONAL_PASS > 0/3 > duplicate），选取 R&D Intensity 作为最后一个方向重开。

**决策逻辑：**
1. **R68 是 duplicate 关闭（类型 A），非 0/3 公式失败** — R68 判定 `rdexp_ttm/totasset_bs` = rdexp2at，但 evaluator 建议的 `rdexp_ttm/totopinc_ttm`（营收分母）公式不同，factor_library.db 中无 exact match
2. **R83 是 data coverage 关闭（类型 C）** — rdexp 数据覆盖率不足，但需由 dvcoder 在语义空间中评估是否可通过子样本（post-2019）或替代口径绕过
3. evaluator 的 primary 推荐方向
4. 按优先级规则：duplicate 关闭（类型 A）优先级最低，适合作为"最后一个未尝试方向"重开

### 关键限制条件

- **分母变化不影响 data coverage**：R83 的 rdexp 数据覆盖率不足与分母（totasset vs totopinc）无关。分子 rdexp 的数据源问题不因分母变化而解决。
- **若重开后仍遇 data coverage 不足**：dvcoder 必须在语义空间中明确说明是否可以接受 post-2019 子样本回测（仅 7 年数据），并在 evaluator 语义预审阶段获得批准。
- **若 R68 是 0/3 关闭（类型 B）而非 duplicate**：则不会重开，因为同经济学方向已被信号层面否决。

### 对比：方向重开 vs 方向重复陷阱

本判例与"方向重复陷阱"（common pitfalls）的关系：

> "被关闭的是'经济学方向'而非'具体公式'。判断标准：新候选的经济学解释能否用被关闭方向的原始经济学名称概括。若可以，则为重复探索。"

- 此处新候选的经济学名称也是"R&D Intensity"——按字面规则应判定为重复
- 但**例外成立**的原因是：R68 不是 0/3 信号失败，而是 exact formula duplicate。关闭范围窄于经济学方向本身
- **原则**：duplicate 关闭只锁公式，不锁经济学方向。0/3 关闭锁经济学方向（除非 evaluator 明确允许换表达式）

## 使用本文件

- 新增判例时按时间倒序插入顶部
- 每次判例需写明：场景、各类关闭类型、决策逻辑、关键限制条件
- 后续方向校验遇到类似结构（分子相同、分母不同 + 原关闭为 duplicate）时，先查本文件确认已有判例
