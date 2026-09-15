---
name: a-share-factor-review
description: 在 ${PROJECT_ROOT} 的 A 股因子框架中执行 evaluator 独立复核、准入判断、人工终审前交接与失败回流判定时使用的薄审查技能。
version: 1.0.0
author: dvcoder
license: MIT
metadata:
  hermes:
    tags: [quant, a-share, review, evaluator, governance]
    related_skills: [a-share-factor-framework, quant-research-loop-governance]
---

# Trigger

当任务涉及以下任一情况时使用本技能：

- `evaluator` 需要审查 `dvcoder` 提交的语义设计方案（阶段 1 预审：经济学含义、单因子合规、因子库重复性）
- `evaluator` 需要复核 `dvcoder` 提交的候选因子（阶段 3 复审：检查实现是否与语义预审一致）
- `evaluator` 需要审查 `dvcoder` 提交的失败报告（指标未达标），并给出下一轮方向
- 需要判断候选因子是否达到"可提交人工终审"的准入条件
- 需要给出通过 / 不通过 / 有条件通过结论与明确回流动作
- 需要处理"`evaluator` 通过但人工终审不通过"的下一轮回流判定

# Scope

本技能负责：

- 独立复核代码、因子值、quick backtest、留档与路径一致性
- 执行准入判断并输出结构化审查结论
- 记录审查风险、证据、回流点与人工终审前状态
- 随使用轮次不断吸收新的审查坑点、证据模板与回流规则

本技能不负责：

- 代替 `dvcoder` 主导新因子构思与主实现
- 代替人工做最终拍板
- 用抽象判断取代证据核查

# Canonical context

- 项目级总规则以 `${PROJECT_ROOT}/HERMES.md` 为准。
- 公共量化方法规则以共享技能 `a-share-factor-framework` 为准。
- 本技能只补薄的审查层：审查动作、证据结构、准入判断、回流规则。
- 三层结构口径见 `a-share-factor-framework` 的「三层结构口径」章节，此处不重复。关键的准入规则：**`util/rawsigs/` 中的 `*_codex.py` 必须通过人工终审才能放入**；候选期间只能放 `review_queue/` 或 `evaluator_passed/`。
- 详细审查细则见 `references/evaluator-triage-checklist.md`。
- 7 维结构化审查模板见 `references/seven-dimension-review-template.md`，确保审查全面覆盖经济学含义、单因子合规性、代码质量、因子库重复性、改进轨迹、修改意见、下一轮方向。
  1. `${PROJECT_ROOT}/HERMES.md`
  2. `a-share-factor-framework`
  3. 本技能
  为准。

# Default review loop

**首先识别提交类型**：dvcoder 提交时会在 context 中标注提交属于哪种模式。

**task 创建禁令：evaluator 不得调用 `kanban_create`。** 本技能只负责审查（读+写评论），不负责创建下游 task。审查完成后通过 `kanban_block(reason="review-required")` 或 `kanban_complete()` 结束。下游 task 由 `default` 负责创建。违反此禁令会导致调度逻辑混乱（evaluator 越权编排下一轮，跳过 default 的方向判断）。

**永不停止循环：** evaluator 通过某个因子后，标记为可提交人工终审候选即可——循环继续，不停止。`default` 会在归档后创建下一轮 task。不要试图阻止循环或要求停止。

本审查技能支持两种模式：

## 模式 A：语义预审（阶段 1 — 审查因子能不能做）

在 dvcoder 进入算子空间之前，接收语义设计方案审查。

审查内容仅三项：
1. **经济学含义是否成立** — 因子是否能用单一经济学名称概括
2. **单因子合规性** — 任何数学表达方式均可，但必须是单一经济学含义（不是多因子组合）。判断标准：能用一个有经济学含义的名称概括的是单因子；需要用多项成分才能描述的，不是
3. **因子库重复性** — 四层强制查重（严口径 2026-09-07）：①公式/口径一致 ②单调等价（倒数/差分/取负/镜像/窗口滞后变体）③参数实例（库内参数化家族声明参数域内的实例 = 重复，即使因子值未物化）④同经济含义。数据源：`factor_library.db` + `util/factor_library_registry.json` + `util/rawsigs/` 代码核对。**dvcoder handoff 必须含查重报告，缺失则直接打回补报告**（防 R93 复发）

输出结论：**通过（进入算子空间）** 或 **打回（回到语义空间重新构思）**。

### 模式 A 方向校验

即使模式 A（语义预审）不进行完整复审，**只要审查结论中包含了 `## 下一轮方向建议`，就必须在输出前执行方向预校验子程序**（见下文「方向预校验子程序（强制）」）。R111 案例：evaluator 在模式 A 中确认 Revenue Growth 重复后推荐了 Asset Turnover 和 Interest Coverage——两者均在之前轮次中正式关闭（R54/R55），导致 default 创建 R112 前需要额外的方向校验工作。根因：方向预校验仅在模式 B/C 中强制，模式 A 无此要求，但模式 A 的下一轮方向建议同样被 default 用于编排。

## 模式 B：复审（阶段 3 — 检查因子构建对不对）

复审步骤（在语义预审已通过的前提下）：

1. 读取 `${PROJECT_ROOT}/HERMES.md`、`a-share-factor-framework`、被审查对象与必要留档。
2. 先核对候选目录是否齐全，默认入口是：
   - `${PROJECT_ROOT}/factor_replicate_outputs/review_queue/<facname_codex>/`
3. 检查内容（**不重复检查经济学含义和单因子合规，已在语义预审通过**）：
   - 实现是否与语义预审通过的方案一致
   - 三层架构是否正确（rawsig/rawsigs → util/非rawsig → *_codex.py）
   - 代码正确性、因子值完整性
4. 输出结论：通过 / 不通过 / 有条件通过
5. **下一轮方向预校验（强制步骤，evaluator 不得跳过）**：在写下 `## 下一轮方向建议` 前，必须执行「方向预校验子程序（强制 — 所有模式通用）」中的完整三层校验流程（failure_registry.db → review_queue/ → factor_library.db），对每个拟推荐方向做关闭/重复状态验证，并在结论中记录校验日志。R62/R72/R111 的重复案例表明，evaluator 会依赖记忆中的旧方向名推荐已被自己关闭的方向。

## 模式 C：失败报告审查（阶段 2→3 之间 — 审查失败原因和方向）

当 dvcoder 指标未达初步条件时，审查其失败分析质量和下一轮方向：

1. 评估 dvcoder 的失败归因是否合理（是参数调尽？方向不对？数据覆盖不足？）
2. **必须检查 RankIC 时序模式，而非仅看聚合指标。** 常见但容易被忽略的模式包括：
   - **年报刷新期季节性尖峰**：如每年 2 月年报刷新期分母近零导致比值因子 IC 骤降（-0.8~-1.0），而差分形式无此模式。这指向比值形式对该经济变量的结构性不适用，而非"表达不稳定"。
   - **财报季系统性信号反转**：如每年 4 月（一季报）/ 8 月（中报）/ 10 月（三季报）前后 RankIC 规律性翻转。
   - **IC 方向错误但 long-short 接近零**：反号后 IC 改善但 long-short 仍不显著——说明信号横截面区分力不足，非简单的 sign 错位。
   - 如何检查：读取回测输出中的逐月 RankIC 列（如 metrics_summary.csv 或 backtest 产物的月度 IC 表），绘制时序趋势或检查极值月份。
3. **下一轮方向预校验（强制步骤）**：在输出下一轮方向前，执行「方向预校验子程序（强制 — 所有模式通用）」中的完整三层校验流程。对每个拟推荐方向（含 primary 和 secondary）做关闭/重复状态验证，排除已关闭方向，并在结论中记录校验日志。
4. 无需 pass/fail 判定。输出应包括：
   - 失败分析评价（含 RankIC 时序模式发现，若有）
   - 下一轮方向（继续同一方向换变量表达 / 换信号源 / 放弃该路径）
   - 具体修改建议（代码层或构思层）
5. 不提供人工终审入口（因为指标未达标）。

若复审通过（路径 B），候选转入：
    - `${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/<facname_codex>/`
    - **必须同时复制 `backtest/` 子目录**（若 review_queue 中有）：`cp -r ${PROJECT_ROOT}/factor_replicate_outputs/review_queue/<facname_codex>/backtest ${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/<facname_codex>/`
    - 确保 `evaluator_passed/<facname_codex>/` 下包含：codex.py、data/*.feather、backtest/*（含 xlsx、metrics.json、rankic.csv、groupret.csv、sigret.csv）、result/*（含 formula.md、hypothesis.md、summary.md、dvcoder_handoff.md、run_manifest.json）
之后仍需等待人工最终审批，未经人工审批通过不得进入 `${PROJECT_ROOT}/util/rawsigs`。

# Human-final-review rule

当前阶段，`evaluator` 不是最终拍板者。

- `evaluator` 通过 = 可以提交人工终审
- 人工终审通过 = 才允许正式入库
- 人工终审不通过 = 不得直接入库，也不等于直接删除

# Bounce-back rule after human rejection

# Human-final-review summary compilation

当需要维护 `${PROJECT_ROOT}/evaluator_passed_factor_summary.xlsx`（人工终审前汇总表）时：

## 数据源规则

**分组收益（十档）必须使用 `*_codex_groupret.csv`，不得使用 `*_backtest.xlsx`。** 两者的区别：

| 来源 | 内容 | 用途 |
|---|---|---|
| `*_codex_groupret.csv` | 每个调仓日各分组的平均收益（10 组 × N 期） | 分组收益统计 |
| `*_backtest.xlsx` | 多空组合日度净值、年化收益、最大回撤等 | 单因子整体评估 |

backtest xlsx 包含的是 long-short 组合的日度净值，不是十档分组收益数据。用 xlsx 算分组收益会得到只有首行有值的稀疏数据（baskettest_ 的 lsdf 行为）。

## 文件打包命名规范

新增因子到 xlsx 后，同步打包 `groupret.csv` + `rankic.csv` 到一个 zip 中，命名规则：

```
r{轮次}-{因子名}-group.csv
r{轮次}-{因子名}-rankic.csv
```

例如：`r138-marginal_gross_profit_efficiency_delta2q-group.csv`

## xlsx 更新注意

- **MergedCell 陷阱**：原 xlsx 的注解行（如"1. 所有因子均已通过dvcoder回测..."）使用了跨列合并单元格（A29:J29 等）。使用 `ws.insert_rows()` 后，这些合并区域会留在原地覆盖新行。**修复方法**：写数据前必须先 `ws.unmerge_cells('A29:J29')` 等解除所有与新行区域重叠的合并单元格，再逐个单元格写入数据。
- **模板格式化**：新行应从已有数据行（如 row 2）复制字体、对齐、边框样式，避免格式断裂。
- 新增行应插入于注释行之前（`ws.insert_rows(last_data_row + 1, len(new_factors))`），保持注释在表格底部。

当出现"evaluator 通过、人工终审不通过"时，默认规则是：

1. 回到 `dvcoder`
2. 以上一轮 `${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/<facname_codex>/` 为输入种子
3. 优先从**语义空间 / 表达层**复盘：
   - 假设是否成立
   - 变量映射是否合理
   - 公式表达是否需要调整
4. 除非人工明确指出**数据口径错误**、**样本构造错误**或 **ETL 口径错误**，否则**不从 ETL 重跑起**
5. 新一轮候选重新进入 `review_queue`，再走完整复核链路

# 长期记忆数据库操作规范

本系统使用两个 SQLite 数据库记录失败经验和因子库统计（详见 `${PROJECT_ROOT}/HERMES.md §5.4`）。由 **evaluator 作为唯一写入者**，dvcoder 与 default 只读访问。

## evaluator 写入规范

### 写入 `failure_registry.db`（打回时立即写入）

**SQLite 路径**：`${PROJECT_ROOT}/database/failure_registry.db`

**适用场景**：
- 语义预审打回（模式 A）：写入 `step='semantic_review'`
- 全链路复审不通过（模式 B 不通过、路径 B 不通过、§6.3）：写入 `step='pipeline_review'`

**不适用**：回测指标未达初步条件的失败报告审查（模式 C）——这是正常参数化迭代，不是判定性失败。

**写入命令模板**：
```python
import sqlite3, json

conn = sqlite3.connect("${PROJECT_ROOT}/database/failure_registry.db")
conn.execute("""
    INSERT INTO failures (round, factor_group, factor_names, step,
                          scope, root_cause, verified, evaluator_verdict,
                          direction_provided)
    VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
""", (
    round_num,           # 如 "R19"
    factor_group,        # 如 "self_funded_reinvestment_quality"
    factor_names,        # 涉及的因子名，逗号分隔
    step,                # 'semantic_review' 或 'pipeline_review'
    scope,               # 失败范围描述
    root_cause,          # 根因
    evaluator_verdict,   # 审查结论原文
    direction_provided,  # 0 或 1
))
conn.commit()
conn.close()
```

**写入要求**：
1. `scope` 必须写明失败范围（哪个因子/哪个设计决策出问题）
2. `root_cause` 必须是根因，不是现象描述
3. `direction_provided` 如实填写：若 evaluator 在审查结论中给出了明确修改方向填 1，模糊或无法给出方向填 0
4. 写入后 dvcoder 会在后续补充 `verified` 和 `verified_by` 字段

### 写入 `factor_library.db`（人工终审通过后写入）

**SQLite 路径**：`${PROJECT_ROOT}/database/factor_library.db`

**适用时机**：候选因子通过人工终审，被正式移入 `util/rawsigs/` 后，由 default 通知 evaluator 执行写入。

**写入命令模板**：
```python
import sqlite3, hashlib, json

def normalize_formula(formula: str) -> str:
    """归一化公式：去空格、统一运算符别名"""
    import re
    f = formula.strip()
    f = re.sub(r'\s+', '', f)
    return f

conn = sqlite3.connect("${PROJECT_ROOT}/database/factor_library.db")

formula_raw = "OCF / TotAsset"  # 从 formula.md 提取
metadata = {"signamex": "cfo", "fiscaltypex": "ttm",
            "signamey": "totasset", "fiscaltypey": "bs"}
canonical_meta = json.dumps(metadata, sort_keys=True)

formula_hash = hashlib.md5(
    (normalize_formula(formula_raw) + canonical_meta).encode()
).hexdigest()

conn.execute("""
    INSERT OR IGNORE INTO factor_library
        (factor_name, economic_meaning, math_formula, formula_hash,
         metadata_json, rankic, rankicir, lsret,
         entry_channel, artifact_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'human_final_review', ?)
""", (
    factor_name,          # 目录名
    economic_meaning,     # 经济学含义（一句话）
    formula_raw,          # 原始公式字符串
    formula_hash,         # md5 去重 key
    canonical_meta,       # 标准化 JSON
    rankic,               # RankICmean
    rankicir,             # RankICIR
    lsret,                # LS 收益率
    artifact_path,        # evaluator_passed/ 下目录路径
))
conn.commit()
conn.close()
```

**写入要求**：
1. `formula_hash` 由 evaluator 在写入时计算，使用归一化公式 + 排序后的元数据 JSON
2. 若因 `UNIQUE(formula_hash)` 冲突导致 INSERT 失败，说明该因子已在库中——不要覆盖，应报知 default
3. `rankic` / `rankicir` / `lsret` 取自该因子最后通过的回测结果

## dvcoder 读取规范

### 读取 `factor_library.db`（语义预审时查重）

dvcoder 在提出因子设计方案（公式 + 变量映射确定后）执行：

```python
import sqlite3, hashlib, json

def check_duplicate(formula_raw: str, metadata: dict) -> bool:
    conn = sqlite3.connect("${PROJECT_ROOT}/database/factor_library.db")
    formula_norm = re.sub(r'\s+', '', formula_raw.strip())
    canonical_meta = json.dumps(metadata, sort_keys=True)
    fhash = hashlib.md5((formula_norm + canonical_meta).encode()).hexdigest()
    row = conn.execute(
        "SELECT factor_name FROM factor_library WHERE formula_hash = ?",
        (fhash,)
    ).fetchone()
    conn.close()
    return row is not None  # True = 已存在
```

存在则退回语义空间，在 handoff 中注明"该因子与 `${matched_name}` 重复"。**（严口径 2026-09-07）哈希命中即重复；哈希未命中 ≠ 不重复** —— 必须继续执行参数实例/单调等价/同含义三层检查：读取 `${PROJECT_ROOT}/util/factor_library_registry.json`（含各家族 `init_defaults`/`param_domain_hints`）枚举候选是否为库内家族实例（如 `amihud_dxy_<N>`、`x2p` 的 gp/op/ebit/totp、`profit2ev` 的 gp/op/ebitda、`gp_growth_qoq_codex` 变体），存疑时打开 `rawsigs/<name>/<name>.py` 核对。

### 读取 `failure_registry.db`（查历史教训）

dvcoder 在进入语义空间前可选查历史教训：

```sql
SELECT round, factor_group, step, scope, root_cause, direction_provided
FROM failures
WHERE factor_group LIKE '%<当前方向关键词>%' AND archived = 0
ORDER BY created_at DESC
LIMIT 5;
```

# Required review artifacts

默认要求被审查目录至少包含：

- `<facname_codex>.py`
- `<facname_codex>.feather`
- `<facname_codex>_backtest.xlsx` 或同等 quick backtest 结果
- `summary.md`
- `run_manifest.json`
- `dvcoder_handoff.md`
- `formula.md`
- `hypothesis.md`
- 必要时的 `metrics.json` / `metrics.csv`

# Output format

默认输出至少包含：

- `审查结论`
- `审查口径`
- `证据`
- `主要问题`
- `风险`
- `反直觉质疑` — 每轮必写 3 个，从相反角度攻击假设：
  1. 如果这个因子的经济学含义是反的，什么证据会支持？
  2. 变量映射中最脆弱的假设是哪一个？如果它不成立，因子还剩多少信号？
  3. 这个因子在哪个市场环境下必然失效？
- `回流动作`
- `当前候选路径`
- `## 下一轮方向建议` — **PASS 审查也必须包含**。即使审查结论是通过，也需给出下一轮探索方向（可以是同语义族的不同表达式，或切换新语义族）。若无法给出，在结论中明确声明"无法推荐"并注明原因。default 读取时按以下策略选择：优先用 evaluator 建议 → evaluator 未建议时根据因子库缺口自主选择。_R73 教训：PASS 审查未包含下一轮方向建议，default 需自行分析缺口选择新方向。_

dvcoder 在下一轮迭代中必须逐一回应这 3 个反直觉质疑，否则不得进入算子空间。

# 方向预校验子程序（强制 — 所有模式通用）

**本条规则独立于模式 A/B/C**。只要 evaluator 的审查结论包含 `## 下一轮方向建议` 章节（无论审查结论是通过、打回、不通过还是失败报告），在输出前必须执行此子程序。R111 再次验证：模式 A 的 evaluator 在确认重复后推荐了已关闭方向，说明方向校验不是单一模式的局部规则，而是一个跨模式强制步骤。

## 执行流程

### 第 1 步：编译拟推荐方向列表
从拟输出的 `下一轮方向建议` 中提取所有方向关键词（含 primary 和 secondary 列表中的每一个）。

### 第 2 步：对每个关键词执行三层校验

每一层都必须执行，缺一不可：

**层 A — failure_registry.db 查询：**
```sql
SELECT round, factor_group, root_cause
FROM failures
WHERE factor_group LIKE '%<关键词>%' AND archived = 0
ORDER BY created_at DESC;
```

**层 B — review_queue/ 目录查询（即使层 A 无匹配也必须执行）：**
```bash
# Step 1: Search directory names
ls ${PROJECT_ROOT}/factor_replicate_outputs/review_queue/ | grep -i <关键词>
ls ${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/ | grep -i <关键词>

# Step 2: If any match found, drill into codex filenames (directory name may be broader than actual formula)
for dir in $(ls ${PROJECT_ROOT}/factor_replicate_outputs/review_queue/ | grep -i <关键词>); do
  echo "=== $dir ==="
  ls ${PROJECT_ROOT}/factor_replicate_outputs/review_queue/$dir/*codex*.py 2>/dev/null
done

# Step 3: Check formula.md for the exact formula being tested
for dir in $(ls ${PROJECT_ROOT}/factor_replicate_outputs/review_queue/ | grep -i <关键词>); do
  echo "=== $dir/formula.md (first 15 lines) ==="
  head -15 ${PROJECT_ROOT}/factor_replicate_outputs/review_queue/$dir/result/formula.md 2>/dev/null
done
```
若 `review_queue/` 中有该方向历史目录但 `evaluator_passed/` 无对应 → 该方向可能已被前序 evaluator 关闭，但也可能是因标准升级而归档后允许重新评估。**必须执行以下操作：**
1. **列出该目录下所有 `*codex*.py` 文件名** — 有时目录主题名（如 `round29_operating_leverage_fixed_asset_intensity`）比实际测试的 codex 公式（`fixed_asset_intensity_codex.py` 实现 `fixasset/totasset`）更宽泛，仅检查目录名可能错过精确公式匹配。
2. **读取 `result/formula.md`** 确认实际测试的数学公式与当前候选是否一致。
3. **读取 `dvcoder_handoff.md`** 确认 evaluator 的正式裁决结论。
4. **若 `result/dvcoder_handoff.md` 不存在（归档目录常见的结构差异）**，检查目录根是否有 `*_REMOVAL_NOTE.md` 或其他归档说明文件。归档说明文件可能明确标注"允许在当前标准下重新评估"（如 `ccc_simple_codex_R4_archived/R4_REMOVAL_NOTE.md` 案例）——这种条目不应按"evaluator 关闭"处理，而应按"方向可用但需在当前框架下重新验证"处理。
5. **判定规则**：归档目录中说明文件明确允许重新评估 → 方向可用，在 task body 中注明差异即可。归档目录中 evaluator 结论为正式关闭（如 0/3/failure）→ 按 stale/closed 处理。

⚠️ **目录命名泛化坑（R117 案例）**：一个 review_queue 目录可能以一个宽泛的主题命名（如 `round29_operating_leverage_fixed_asset_intensity`），但内部 codex 文件精确实现了当前推荐的公式（如 `fixed_asset_intensity_codex.py` 实现 `fixasset / totasset`，与推荐公式 100% 一致）。仅靠目录名 grep 匹配然后判断"该目录是关于不同经济对象"是不够的——必须检查 codex 文件名和 formula.md。R117 evaluator 正是因此误将已关闭方向标记为"clean"。

**层 C — factor_library.db 语义相近方向查询（即使层 A+B 均无关闭记录也必须执行）：**
```sql
SELECT factor_name, math_formula, entry_channel, rankic, rankicir, lsret
FROM factor_library
WHERE factor_name LIKE '%<关键词>%' OR economic_meaning LIKE '%<关键词>%'
ORDER BY entry_channel;
```
注意区分两类 `entry_channel`：
- `initial_inventory` 且指标全为空 → 从未 pipeline 评估。方向可用但需差异化说明。
- `human_final_review` 且有记录指标 → 正式入库因子，除非另有要求否则视为重复。

**⚠️ 层 C 的 SQL 关键词搜索盲区 — 逆关系/倒数关系的捕获（R120 案例）：**
纯 SQL 的 `LIKE '%<keyword>%'` 搜索对逆关系（倒数）几乎不设防：当推荐方向是 `equity_to_assets`（equity/total_assets，关键词 "equity"），而库中存在 `asset2eq`（total_assets/equity，因子名不含 "equity"，经济含义列也可能不含该词），SQL 查询返回无匹配。但两者是严格的单调等价逆关系——X/Y 与 Y/X 互为倒数映射。

**对纯除法因子（X/Y 形式）的附加检查步骤（在标准 SQL 查询之后执行）：**
1. 对每个推荐方向，判断其是否为纯除法因子（形如 `X / Y`）。
2. 若为纯除法，**构造逆关系搜索**：将分子和分母互换，查询因子库中是否存在形如 `Y / X` 或包含逆关系的 formula：
   ```sql
   SELECT factor_name, math_formula, entry_channel
   FROM factor_library
   WHERE factor_name LIKE '%Y%' AND factor_name LIKE '%X%'
      OR math_formula LIKE '%Y / X%' OR math_formula LIKE '%Y/X%'
      OR math_formula LIKE '%Y%X%'  -- 宽泛匹配，检查分子分母是否互换
   ORDER BY entry_channel;
   ```
3. 同时检查 `util/rawsigs/` 目录中是否存在逆关系的原子信号或 codex 文件：
   ```bash
   find ${PROJECT_ROOT}/util/rawsigs/ -name '*.py' | xargs grep -l '<Y>.*<X>\|<X>.*<Y>' 2>/dev/null | head -5
   ```
4. 若逆关系版本在 factor_library 或 rawsigs 中存在（无论 entry_channel 是否为 initial_inventory），该方向标记为 `inverse_duplicate` 并排除。
5. 例外：如果逆关系版本是 `initial_inventory` 且从未 pipeline 评估，且两变量映射有经济上的正交理由（如 `OCF/Revenue` vs `Revenue/OCF` 中一个不可解释），可以在 task body 中注明差异后允许推进——但 evaluator 必须在结论中明确记录这一判断理由。

### 第 3 步：校验日志记录
在审查结论中（`## 下一轮方向建议` 章节之前或之后）记录校验日志，格式：
```json
{
  "direction_validation_log": {
    "checked_keywords": ["asset_turnover", "interest_coverage"],
    "results": {
      "asset_turnover": {"stale": true, "closing_round": "R54", "source": "failure_registry + R105 evaluator reconfirm"},
      "interest_coverage": {"stale": true, "closing_round": "R55", "source": "failure_registry + R55 evaluated handoff"}
    },
    "conclusion": "primary+secondary both stale → must recommend new direction"
  }
}
```

### 第 4 步：判定规则
- 至少一个推荐方向在全部三层校验中均无关闭/重复记录 → 正常输出，附校验日志
- 若 primary 已被关闭但 secondary 未关闭 → 输出 `primary_stale: true` 并注明关闭原因，以 secondary 为主
- 若 primary+secondary 均关闭 → **不得继续推荐已关闭方向**，必须推荐全新的、三层校验均无记录的方向
- 若当前语义族所有方向均关闭 → 推荐与当前维度前驱轮次不重复的外部方向（如估值→现金流）

### ⚠️ failure_registry.db 盲区警告
该数据库仅从约 R54 起才有记录。更早轮次的关闭方向（R17/R18/R41/R42 等）可能未录入 DB。因此层 A 返回"无匹配"≠ 方向可用。必须同时执行层 B（review_queue/ 目录查询）作为补充验证。当 DB 无匹配但 review_queue/ 中存在历史目录时，以历史目录中的 evaluator 结论为准。

# Common pitfalls

1. 只看作者摘要，不核对产物路径与代码。
1. **MD 摘要文件是手动的，不是 cron。** `failure_registry_summary.md` 和 `factor_library_catalog.md` 只在用户要求时由 default 从 SQLite 聚合生成。不要自动更新它们，也不要设置 cron 定时刷新。
2. 复核通过后还继续把人工终审入口指向 `review_queue` 而不是 `evaluator_passed`。
3. 把"人工终审不通过"误判成必须从 ETL 重新开始。
4. 没有 `dvcoder_handoff.md` 就直接放行。
5. 让 `evaluator` 自己补主方案，导致作者与审稿人角色混淆。
6. **未达门槛的候选仍按正常复核流程处理。** 当 candidate 的指标未达到参考门槛（RankICmean>0.015, IR>1.5, lsret>4%）时，evaluator 不应直接退回，而应完成完整审查，给出改进方向建议。指标未过门槛不是跳过 evaluator 的理由。
7. **语义预审阶段不越界审查代码。** 在模式 A（语义预审）中，只审三项：经济学含义、单因子合规、因子库重复性。不要要求 dvcoder 提供代码、回测结果或完整留档——那些是算子空间（阶段 2）的产物，语义阶段还没有。
8. **复审阶段不重复审查经济含义。** 在模式 B（复审）中，不要重新审查经济学含义和单因子合规——这些已在语义预审中通过了。只检查实现是否与语义预审通过的方案一致、三层架构是否正确、代码是否正确。
7. **跳过因子库查重**：审查时未检查 `${PROJECT_ROOT}/util/rawsigs/` 是否有等价因子，导致重复因子通过审查。这比指标未达门槛更严重——重复因子不应入库。
- **审查结论中不包含下一轮方向建议**：在自治循环模式下，evaluator 的审查结论必须包含 `## 下一轮方向建议` 章节，否则 default 无法编排下一轮 dvcoder 任务。PASS 审查（如 3/3 达标）尤其容易遗漏此项，因为 evaluator 认为"通过了只需等人工终审"。正确做法：无论通过与否，都给出明确的下一轮方向。PASS 审查时方向可以是："该语义族仍有 X 个未探索的变体"或"切换到 Y 新语义族"。如果 direction_provided=0（无法推荐），在结论中注明原因。_R73 案例：ebitda2ev PASS 审查未包含下一轮方向建议，default 需自行分析因子库缺口。_
- **共享层文件放在 review_queue 内而非 util/ 非 rawsig 区域。** dvcoder 可能在 review_queue/<facname>/ 目录下同时放置共享函数文件和叶子 codex 文件。若发现共享函数不在 `${PROJECT_ROOT}/util/` 下，应标注为结构性位置问题——即便当前阶段可以容忍，也要在留档中注明，后续进入正式库前必须迁移。
- **归零轮审查**：当 dvcoder 提交"归零轮"（standalone script 而非 codex）结果时，evaluator 应放宽代码架构要求（不需要 stkfactor 子类），但严格审查：(a) 因子是否是干净单因子，(b) 经济学含义是否自洽，(c) 指标的可解释性。归零轮的代码结构是临时的，但因子定义和回测口径必须正确。
- **多因子组合 vs 单因子的核心判断标准**：不是看是否用了 zscore，也不是看是否用了加减乘除——而是看：**能否用一个经济学名称概括这个因子的全部含义**。如果不能（例如需要说"这是现金支持 + 质量门控再投资 - 低质量惩罚的三部分组合"），那就是多因子组合。判断时检查：(a) 去掉任一分量后经济学含义是否崩塌——如果去掉一个分量含义仍然完整，说明该分量是独立的冗余信号，(b) 各分量的权重是否有经济学依据——如果加权系数是等权、经验值或调参来的，没有经济理由，就是多因子组合。
- **子门槛渐进改进候选的处理。** 当 dvcoder 连续多轮提交的候选因子均未达到硬门槛（ICmean>0.015, IR>1.5, lsret>0.04），但每一轮都有明确可测的改进（如 IR 从 0.97 → 1.26，lsret 从 0.044 → 0.059），evaluator 不应直接按"不通过"了事。应看两个维度：(a) 改进轨迹是否仍在收敛，还是已经 plateau；(b) 当前最佳候选是否已有实际区分力（如 IR>1.0 的因子在多因子组合中仍可贡献边际价值）。若已到 plateau 且不够门槛，应在审查结论中注明"当前表达层已到 plateau，建议换层而不是继续调参"，不做一刀切的不通过判定。
- **当 evaluator profile 不可用时**：如果 evaluator 自身反复 crash（非配置问题），default 可使用 `delegate_task` 生成独立子 agent 替代审查。子 agent 独立运行、不共享上下文、加载审查技能。这是应急方案，优先仍应修复 evaluator profile。
- **多因子组合轮次堆叠陷阱**：当 dvcoder 连续 3+ 轮在同一个 multi-component 结构上层层堆叠（如 R7→R8→R9 从 4分量→5分量→线性blend），evaluator 应在第一轮就标记为多因子组合违规并要求"归零"拆解，而不是让违规结构在多轮迭代中持续膨胀。累积违规轮次越多，dvcoder 沉没成本越大，修正越困难。
- **系统性单因子合规集体沦陷**：当回溯审查发现全部轮次（如 R7-R11 共 5 轮）均因同一类问题（如多因子组合）不通过时，说明这不是单轮偶然问题，而是 dvcoder 的工作范式偏差。审查结论应指出范式层面需要修正，而非逐轮打回。同时，应识别"最有价值的资产"（如信号最强的那一轮的核心理念），要求在该核心理念上做"归零拆解"而非在上层继续堆结构。
- **并行 deegate_task 审查大型回溯**：当需要对大量历史轮次做回溯审查时（如 5-11 轮），可拆分为多组并行子 agent 以提高效率。例如 R1-R6 一组、R7-R11 一组。每组的 context 中要包含完整审查规格和 cross-group 一致性说明，确保审查标准统一。
- **evaluator 不得调用 kanban_create**：本技能不负责创建下游 task。审查完成后由 default 读取结论并创建下一任务。evaluator 调用 kanban_create 会造成调度逻辑混乱（跳过 default 的方向判断），属于严重流程违规。
- **永不停止循环意识**：当 evaluator 判定某个因子通过审查时，不要以为流程就此结束。标记为可提交人工终审候选后，default 会继续创建下一轮 task 以挖掘更多因子。审查结论中的"下一轮方向建议"在通过场景下也应给出——用于 default 判断下一轮选哪个方向继续。
- **同一候选项被多次调度审查**：R28 rev_per_cashpay 被 dispatcher 先后调度到 3 个不同的 evaluator task（t_766f690e, t_45003478, t_555e24ff），3次审查得出相同结论（0/3，正式关闭），浪费计算资源。根因：dvcoder 的 blocked task 在 evaluator 审查完成后未被及时清理，导致重新调度。evaluator 审查完成后应检查 kanban 上是否仍有同一个因子的残留 blocked task，若发现有，应主动 cleanup：调用 `kanban_complete(task_id=<stale_dvcoder_task_id>)` 将其关闭。**`kanban_complete` 接受 `task_id` 参数**（不传则默认当前任务），因此 evaluator 可以跨 task 清理——这与 `kanban_create` 禁令无关（create 是编排，complete 是清理）。注意：仅清理同一个因子的残留 blocked task，不要清理其他 evaluator 的活任务。
- **dvcoder 任务持续 crash 时的协同诊断**：当 evaluator 被多次调度审查同一 dvcoder 候选，且每次审查前 dvcoder 都 crash 了（runs 为空或 status=crashed），这往往不是 dvcoder 的代码问题，而是 kanban DB 损坏或 dvcoder 的 Codex session token 过期。diagnostic 优先级：(1) 检查 kanban DB integrity， (2) 检查 dvcoder gateway 是否独占（无并行 gateway）， (3) 通知用户运行 `hermes model -p dvcoder` 重新认证。直接走审查流程是浪费 token——每次都读到同一份无变化的产物。
- **发现代码提前入库应主动要求回滚**：R16 中 evaluator 发现 dvcoder 已将 3 个 codex.py 直接写入 `util/rawsigs/quality_gap_family_codex/`（违反"未经 evaluator 复核和人工终审不得进入 rawsigs"规则），但 evaluator 仅标注了状态，未强制回滚。正确做法：要求在继续审查之前先将代码撤回 review_queue/，或至少 clear tag 标记使其不可用于推断。若不回滚，则后续 evaluator 审查天然失效——因为代码已达"终审后"位置。
- **单调等价关系查重**：R25 候选 A（COGS/Inventories avg）通过了标准因子库查重（未找到 exact formula match），但被后续审查发现与 CCC 代码中的 DIO（inventory_days = inventories / COGS × 360）存在严格的单调等价关系。DIO 和 inventory_turnover 互为倒数（差一个 360 缩放因子），属于同一经济学信号的不同数值表达。语义预审阶段不能只查 exact formula match，还应对照因子库中相似维度的因子检查是否存在单调等价关系（倒数/差分/取负等同构变换）。可疑模式：新候选的分子分母与库中某因子的分母分子互换后再缩放。
- **增长率分母 abs 诊断**：当审查 growth-rate 类因子（g(gp)、g(np)、g(op) 等）时，若 dvcoder 使用了原始值做分母（`(X_t - X_{t-1}) / X_{t-1}`），应主动检查 abs 分母版本（`(X_t - X_{t-1}) / abs(X_{t-1})`）的指标。R22/R23 gp_growth_qoq 审查中，abs 分母将 IC 从 0.017 提升至 0.031（+82%），IR 从 1.52→2.22，lsret 从 5.4%→11.2%。若 abs 版本显著更优，应在审查结论中建议 dvcoder 切换为 abs 分母口径；若有重大差异，还应要求 rerun 确认。
- **sign-flip 语义许可判断**：当 dvcoder 提交 sign-flip 诊断结果时（如 R33 dividend_payout_change_6m sign-flip 后 2/3），evaluator 需独立判断：(a) 原始因子方向是否有清晰的经济学定义——若方向原本模糊（如 payout_change 正负均可解释为不同信号），sign-flip 在语义上允许；(b) 若语义允许，仍需按标准门槛（ICmean>0.015, IR>1.5, lsret>0.04）3/3 判定——2/3 不通过；(c) 在审查结论中明确记录 sign-flip 的语义判断理由，供后续人工终审参考。R33 案例：dividend_payout_change 的原始方向 ambiguous（分红增加可以是好消息或坏消息），sign-flip 允许，但仅 2/3 未达门槛 → 关闭 R33。
- **归档目录允许重新评估陷阱 — review_queue 层 B 误判（R127 案例）**：方向预校验的层 B 找到 `review_queue/ccc_simple_codex_R4_archived/` 时，该目录以 `_archived` 结尾且无 `evaluator_passed/` 对应项，看似"方向已关闭"。但读取 `R4_REMOVAL_NOTE.md` 后发现其内容明确声明"按早期宽松标准通过，按当前严格标准不应入库，已于 2026-07-13 移出，如需恢复或重新评估需走当前标准的完整审查流程"——这是**标准升级归档**而非**evaluator 正式关闭**。与真正的 evaluator 关闭（如 R17/R58 的 0/3 裁决）有本质区别。**正确做法**：层 B 发现 review_queue/ 匹配后，若 `result/dvcoder_handoff.md` 不存在，必须检查目录根是否有 `*_REMOVAL_NOTE.md` 或类似归档说明文件。若说明文件明确允许重新评估，该方向算"可用但需差异化说明"，不按 stale/closed 处理。归档说明文件的结构可能为扁平根目录（非 `result/` 内），搜索命令：`ls <dir>/*REMOVAL* <dir>/*ARCHIVE* <dir>/*NOTE* 2>/dev/null`。

- **目录命名泛化陷阱 — review_queue 层 B 根系匹配失败（R117 案例）**：当方向校验层 B 执行 `ls review_queue/ | grep -i <关键词>` 时，返回的目录名可能因主题概括过宽（如 `round29_operating_leverage_fixed_asset_intensity` 包含了 "fixed_asset" 关键词）而被 evaluator 误判为"不同经济对象"跳过。但实际目录内部包含的 codex 文件（如 `fixed_asset_intensity_codex.py`）精确实现了 `fixasset / totasset` 这一公式。**根因**：evaluator 看到目录名中的"operating_leverage"就以为这是 R17/R29 DOL 方向的同类，没有进一步检查 codex 文件名和 formula.md。**正确做法**：层 B 找到任何 grep 匹配后，必须执行三步骤：(1) 列出目录下所有 `*codex*.py`，(2) 读取 `result/formula.md` 前 15 行确认实际公式，(3) 读取 `dvcoder_handoff.md` 确认 evaluator 结论。不要仅根据目录主题名判断经济对象是否相同。
- **next_round 方向不一致陷阱（R52→R53 教训）**：evaluator 在失败审查或复审结论中给出"下一轮方向"建议时，务必确认建议的方向与当前任务探索的方向属于同一语义族。R52（动量方向 PPEM）失败后，evaluator 的 next_round 建议指向了 R51（旧成长方向 Interest Coverage），导致 cron 创建了错误的 R53。正确做法：failure review 结论中的 next_round 应该是在当前探索方向上切换新表达/新语义子方向，而不是跳回其他方向。如果当前方向已正式关闭（如 PPEM），建议应为"关闭该语义族，在 X 新方向上重新开始"而非"切换到另一个已完成的方向上继续迭代"。evaluator 在输出结论前应核查当前 task 的探索方向与建议方向是否一致。
- **stale/closed 方向重复建议陷阱（R62+ 教训，R72 复现，R111 再确认）**：长时间自治运行后（如 R55→R62+），evaluator 的"下一轮方向建议"越来越倾向于引用已在前序轮次中正式关闭的方向。R62 evaluator 建议了 Incremental ROIC（R21/R45/R50/R58 已关闭）和 Asset Growth Rate（R57 已关闭）；R72 evaluator 建议了 R&D Intensity（R68 已关闭为重复）；R111 evaluator（模式 A）在确认 Revenue Growth 重复后推荐了 Asset Turnover（R54 关闭）和 Interest Coverage（R55 关闭）——都是前序 evaluator 自己关闭的方向。**根因**：evaluator 在给出下一轮方向时依赖记忆中的旧方向名，没有执行三层校验（failure_registry + review_queue + factor_library）。**解决方案**：此陷阱已被提升为模式 A/B/C 共用的方向预校验子程序。evaluator 在输出 `## 下一轮方向建议` 前必须执行该子程序，不得跳过。若预校验发现所有拟推荐方向均已关闭，则必须推荐全新的、三层校验中均无记录的语义方向。
- **逆关系/倒数关系盲区 — 层 C SQL 关键词搜索不捕获倒数（R120 案例）**：方向预校验的层 C 使用 `factor_name LIKE '%<keyword>%'` 查询，当推荐方向的因子名与库中已有因子的名称完全不同但互为倒数时（如推荐 `equity_to_assets`、库中已有 `asset2eq` = total_assets/equity），SQL 的关键词搜索不会命中。纯除法因子 X/Y 必须附加逆关系检查：构造 Y/X 搜索因子库和 `util/rawsigs/` 目录，确认不存在逆关系等价物。**判定规则**：若逆关系在库中（无论 entry_channel），除非有经济上的正交理由（参见层 C 附加检查步骤的例外规则），否则视为重复。R120 案例验证：equity_to_assets 经逆关系检查应标记为 `inverse_duplicate: asset2eq exists in factor_library as initial_inventory`。
- **参数实例/家族变体盲区 — 哈希精确匹配不捕获库内参数化家族的实例（2026-09 审计）**：因子库大量目录是参数化家族（`amihud_dxy_<lookback>`、`x2p`/`profit2p`/`cf2p`/`d2p`/`profit2ev`/`profit2income` 的 signamex 参数域、`gp_growth_qoq_codex` 的 lag/window、`retskew60_codex` 的 window）。候选只要落在这些家族**声明参数域**内（即使因子值文件尚未物化）即视为重复。判例：R125 amihud_dxy_10 ↔ amihud_dxy（60d 默认）；R107 SUE ↔ sueall/surall/suprofit 意外盈利族；R110 B2P ↔ b2p.py（默认 eqtopc/totcap，参数一字不差）；R103 return_skewness ↔ retskew60_codex（window=60）；R93-R100 yield/EV 家族 ↔ x2p/profit2p/cf2p/d2p/profit2ev。查重辅助索引：`${PROJECT_ROOT}/util/factor_library_registry.json`。**R93 复发教训**：R85 曾自识别 dividend_ttm2totcap=d2p 重复并关闭，R93 又原样重建并通过 → 语义预审 handoff 必须附四层查重报告，无报告 evaluator 不得 PASS。
- **metrics.json key 大小写不一致导致指标读取遗漏**：不同轮次的 metrics.json 使用不同的 key 命名约定——有的用 `rankic_mean`（全小写下划线），有的用 `RankICmean`（大驼峰），有的用 `RankICMean`。更有部分因子把指标写在 `comparison_*.json` 内嵌列表中而非独立 metrics.json。evaluator 在读取指标时不能只查 `RankICmean`——必须同时尝试 `rankic_mean` / `rankicMean` 等变体，且检查 `backtest/` 目录下所有 `.json` 文件。参考 `references/evaluator-metrics-read-patterns.md`。

## Workarounds

## evaluator profile 不可用时的审查方案

### 第一步：排查 kanban DB 完整性

evaluator 持续 crash（"pid not alive"、"exit code 1"）时，**先检查 kanban DB 是否损坏**，而非直接假设 profile 配置问题。损坏的 DB 导致 evaluator 子进程启动时读任务上下文立即 crash，特征是同一个 profile 的 dvcoder 正常、只有 evaluator 任务连续 crash。

诊断：`sqlite3 ${HERMES_HOME}/kanban.db "PRAGMA integrity_check;"`。非 `ok` 时修复：`.recover` 管道重建 DB。修复后 dispatcher 自动重调度。

### 第二步：DB 完好时的 delegate_task 回退

当 evaluator profile 反复 crash 且 DB 完好时，default 可用 `delegate_task` 启动独立审查子 agent：

```
default → delegate_task(
  goal="独立审查...",
  context=<审查规格：路径、门槛、检查项、因子库清单>,
  toolsets=["file","terminal","web"]
)
```

要求：
- 子 agent 加载 `a-share-factor-framework` 和 `a-share-factor-review` 技能
- `context` 必须包含完整审查规格和因子库对比清单
- 审查结论写入 kanban 评论作为留存证据
- 这是应急方案——优先方案仍是修复 evaluator profile 使其正常调度

# Verification checklist

- [ ] 是否先读取了 `${PROJECT_ROOT}/HERMES.md`
- [ ] 是否同时参考了 `a-share-factor-framework`
- [ ] 是否核对了 `review_queue/<facname_codex>/` 目录内容
- [ ] 是否检查了 `summary.md`、`run_manifest.json`、`dvcoder_handoff.md`
- [ ] 是否确认 `formula.md` 与 `hypothesis.md` 不被塞进 `summary.md`
- [ ] 复核通过后是否明确转入 `evaluator_passed/<facname_codex>/`
- [ ] 是否明确提示“仍需人工最终审批”
- [ ] 若人工终审不通过，是否默认回到 `dvcoder` 且以上一轮 `evaluator_passed` 为种子
- [ ] **因子是否有明确的经济学含义** — 必须主动提问，不能仅因代码跑通而放行
- [ ] **因子是否是单因子，不是多因子组合** — 确认因子能用单一经济学名称概括，禁止任何缺乏单一经济学含义的多因子组合，不限于 zscore 形式
- [ ] **因子是否基于历史数据调整的比率/门控/奖励** — 确认因子不用历史最优回溯的参数
- **因子是否与因子库重复** — 四层强制查重（严口径 2026-09-07）：公式/口径一致、单调等价、**参数实例（库内参数化家族声明参数域内实例 = 重复）**、同经济含义，任一层命中即重复；数据源 factor_library.db + `util/factor_library_registry.json` + rawsigs 代码
- **因子公式的会计关系是否成立** — 复审阶段必须检查因子公式中涉及的会计字段间的关系是否正确。常见错误：将 totopinc(营业收入)混淆为 np(净利润)、用 gp - 四项费用冒充营业利润(漏了投资收益等项目)、用 Δgp/rev 的量纲混合计算。见 references/02-data-pipeline-and-neutralization/a-share-income-statement-formula-chain.md
- **是否涉及混合量纲（change/level 比值）** — 当因子公式中出现分子是变化量、分母是水平值时标记为审查关注项。例如 Δ(gp)/totopinc 中分子是毛利变化量而分母是营收总量。此类结构可能导致信号来自规模差异而非真实 alpha
- **代码提前入库是否已强制追回** — 若发现候选因子代码已提前写入 util/rawsigs/，必须确认已从 rawsigs/ 删除并迁至 review_queue/，而非仅标注状态
- [ ] **下一轮方向建议是否已给出** — 在自治循环模式下，必须有下一轮方向建议章节
- [ ] **下一轮方向是否已通过三层预校验** — 每个推荐方向（含 primary+secondary）必须在输出前执行方向预校验子程序（failure_registry + review_queue + factor_library 三层校验）。校验日志（`direction_validation_log`）必须记录在审查结论中（查了哪些关键词、每层的结果、判定依据）。已在方向预校验子程序中汇总。R111 再次确认：单层校验（仅 failure_registry）不充分，必须三层全查
- [ ] **打回时是否写入了 failure_registry.db** — 语义预审打回和全链路复审不通过时必须写入
- [ ] **direction_provided 是否如实填写** — evaluator 没给出方向时填 0，dvcoder 严禁自行修改
- [ ] **入库时是否写入了 factor_library.db** — 人工终审通过的新因子必须由 evaluator 写入 factor_library.db
