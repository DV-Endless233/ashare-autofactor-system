---
name: a-share-factor-framework
description: 在 ${PROJECT_ROOT} 的 A 股因子框架中执行单因子/组合因子开发、三层 codex 落地、初步回测筛选与 evaluator 复核交接时的主技能。
---

# Trigger

当任务涉及以下任一情况时使用本技能：

- 在 `${PROJECT_ROOT}` 内新建、修改、审计单因子或组合因子
- 判断因子应落在 `rawsig/rawsigs`、`func.py + util/非rawsig` 还是 `*_codex.py`
- 按当前三层口径重写旧因子、旧 thin-shell wrapper 或旧 backtest 尾部
- 对新因子做初步测试、决定继续调参、换方向还是删除
- 需要把候选因子交给 `evaluator` 复核（**按三阶段流水线区分**：阶段 1 语义预审→阶段 3 复审），再交给用户人工审查

# Scope

本技能负责：

- 因子定义落地
- 三层结构定位
- `*_codex.py` 标准结构实现
- 因子值生成与初步回测
- 候选因子的保留 / 删除判断
- 向 `evaluator` 交接复核路径
- 生成全流程留档：`summary.md`、`formula.md`、`hypothesis.md`、`run_manifest.json`、`dvcoder_handoff.md`

本技能不负责：

- Hermes 引擎层源码改造
- 把未经复核和人工审查的候选因子直接写进 `${PROJECT_ROOT}/util/rawsigs`
- 把历史 `references/` 里的会话结论直接当成现成答案照搬

# Canonical context

- 项目级总规则以 `${PROJECT_ROOT}/HERMES.md` 为准。
- 本文件是量化执行主 skill 的方法入口。
- 本技能的 canonical 文件位置固定为 `${HERMES_HOME}/skills/data-science/a-share-factor-framework/SKILL.md`，由 `dvcoder` 与 `evaluator` 共用；不要再各自维护 profile-local 副本。
- `references/` 是二级材料；其中很多是过去 session 的经验记录、调试记录、专题说明、 dated note。
- `references/` 的 active 集合应按主题分组维护，archive 只保留追溯材料，不作为默认规则入口。
- 需要进一步展开时，先打开 `references/README.md` 再按分组读取具体 note。
- 维护 `references/` 时，优先把分组子文档挂到 `references/README.md`，不要依赖 nested linked_files 自动暴露全部文件。
- 如果 `references/` 与 `${PROJECT_ROOT}/HERMES.md`、本 `SKILL.md`、或当前已确认的标准代码样例冲突，以：
  1. `${PROJECT_ROOT}/HERMES.md`
  2. 本 `SKILL.md`
  3. 当前标准代码样例
  4. `references/`
  - 很多财务口径的 dated 说明
- 发现 dated / session-specific / 已过时 reference 时，后续应清理，不继续把旧经验当硬规则。
- `references/01-architecture/expert-feedback-single-factor-principles.md` — 专家反馈的 5 条硬规则完整推理，供理解规则背后的经济学理由
- `references/04-audit-and-governance/dvcoder-profile-cost-optimization.md` — dvcoder 配置项（reasoning_effort / max_turns / context_length / compression）的 token 开销分析与风险边界记录，改配置前必须参考

# Non-negotiable rules

- 先统一口径，再写代码。
- 先读现有框架，再加新逻辑。
- 先给最小可运行版本，再扩展。
- 先产出可验证文件，再讲解释。
- 外部研报只学方法，不套结论。
- 共享逻辑优先放第二层，不要在叶子层重复内联。
- `*_codex.py` 是薄叶子封装，不承担本该进共享层的公共逻辑。
- 初步测试不通过时，先改参数；改参数仍不行，再换方向；换方向仍不行，删除候选，不保留伪资产。
- 初步完成的候选因子不能直接入正式库，必须先过 evaluator 复核。dvcoder 完成实现后**无论指标是否达标，都必须向 evaluator 报告**（未达标→失败报告请求方向；已达标→提交全面审查），再过用户人工审查。
- **因子必须是单因子，不是多因子组合。** 因子必须能从单一经济学含义出发，任何数学表达方式均可（不限 加减乘除），如 FCF = OCF - CapEx、现金利润率 = OCF / NetProfit。**禁止任何缺乏单一经济学含义的多因子组合**——zscore 线性加权或任意系数组合（如 zscore(OCF) + zscore(CapEx) - penalty(Debt)）只是典型违规形式，核心问题不是用了 zscore，而是叠加了多个独立经济含义且各分量权重缺乏经济学依据。判断标准：能用一个有经济学含义的名称概括的因子是单因子；需要用多项成分才能描述的，不是。
- **每轮起始必须加第一性原理引导。** dvcoder 在接受任务后、进入语义空间之前，必须先说"从第一性原理出发"，强制从经济学含义角度理解问题，而不是复用上一轮的误判或错误假设。
- **门控（gating）/ 奖励（reward）默认不加。** 门控和奖励本质上是基于历史数据构造的条件结构，无法保证未来仍然有效，因此默认禁止使用。唯一例外：当经济学含义明确要求门控时（如现金利润率 = OCF / NetProfit，当分子和分母同时为负时比值反而为正——这是经济含义矛盾，必须门控掉），才可加门控。其他所有经济学含义不确定的场景，一律不加门控和奖励。
- **`dvcoder` 和 `evaluator` 不得调用 `kanban_create`。** 只有 `default` 能创建新的 kanban task。这是一个强制硬规则，用于防止：
  - dvcoder 直接创建 evaluator task（跳过 default 对审查规格的设计）
  - evaluator 直接创建 dvcoder task（跳过 default 对方向转换的判断）
  - 任何 profile 完成自己任务后"顺手"创建下一个 task，导致调度逻辑分散
  正确做法：完成工作后以 `kanban_block(reason="review-required")` 或 `kanban_complete()` 结束。见 `${PROJECT_ROOT}/HERMES.md §5.1`。
- **evaluator task 不得设置 parents 依赖指向 dvcoder task（HERMES.md §5.2）。** dvcoder 完成任务后以 `kanban_block(reason="review-required")` 结束，状态是 `blocked` 而非 `done`。如果 evaluator task 的 `parents` 指向该 dvcoder task，子任务会等待父任务 `done` 才提升为 `ready`，但父任务永远无法到达 `done`——导致 evaluator 永远无法被分派。创建 evaluator task 时，应在 body 中引用 dvcoder 产出的文件路径，不设 parents 依赖。
- **创建 task 时必须使用 `idempotency_key` 参数防止重复创建（HERMES.md §5.3）。** key 格式固定为 `round{RoundNum}-{phase}`，如 `R19-semantic`、`R19-eval-prelim`、`R19-operator`、`R19-eval-review`、`R19-eval-failure`。当 dispatcher 或 default 因 crash 后重试再次创建同一 key 的 task 时，系统自动返回已存在的 task id。
- **永不停机循环：** 本系统是一个永不停止的因子挖掘循环。当 evaluator 通过某个因子后，流程是：归档到 `evaluator_passed/` → 标记为人工终审候选 → **继续创建下一轮 task**。不要因为出了一个候选就停止。只有用户手动叫停才会停止。

**近达标候选的归档规则（用户判断）：** 当因子方向经 evaluator 正式关闭且用户判定后，即使指标未达 3/3 硬门槛（如 2/3，ICmean~0.025, IR~1.45 略低于 1.5 阈值），也可以由用户决定将其存档到 `evaluator_passed/`。这不算"通过审查"，而是"已验证到 plateau 的经济学信号存档"——供未来可能的多因子构建或组合信号分析时复用。归档后方向仍然视为已关闭，不继续迭代。关键信号：方向正确、多窗口结果一致、只是强度差一点（IR 1.3-1.45 vs 1.5 门槛），且已达 plateau。

# 三层结构口径

这是当前最高优先级口径：

## 第一层：原子信号层 — `util/rawsigs/<组>/<组>.py`

位置：`${PROJECT_ROOT}/util/rawsigs/` 下的各原子信号文件
例如：`profit/profit.py`、`income/income.py`、`asset/asset.py`、`debt/debt.py`、`capexp/capexp.py` 等

- 负责原始字段整理、字段口径映射、原子信号生成
- 各财务组的基本数据准备
- 只做原子层工作，不在这一层混入组合公式、回测尾部、标准化或中性化
- 新建原子信号时在此目录内新增对应组文件

## 第二层：共享函数库 — `func.py` + 已有的 `util/` 其他 `.py` 文件

A. `func.py`（`${PROJECT_ROOT}/util/func.py`）— **新增共享函数统一放在此文件**，参数化后供 `*_codex.py` 调用。
B. `${PROJECT_ROOT}/util/` 下除 `rawsigs/` 文件夹外的其他已有 `.py` 文件（如 `fiscalsigclass.py`、`ccc_ops.py`、`getStkPool.py`、`neutfactorclass.py`、`stkfactorbacktest.py` 等）— 已有的结构，继续使用。

`*_codex.py` 调用第一层原子信号 + 第二层各类共享函数即可完成因子构建。

## 第三层：叶子因子层 — `*_codex.py`

每个因子一个 `*_codex.py` 文件。

最终通过人工终审后，放入：
`${PROJECT_ROOT}/util/rawsigs/<facname_codex>/<facname_codex>.py`

但在通过人工终审前，候选因子必须留在：
- `${PROJECT_ROOT}/factor_replicate_outputs/review_queue/`（dvcoder 初步通过 → evaluator 复审前）
- `${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/`（evaluator 复审通过 → 人工终审前）

**禁止在人工终审前将 `*_codex.py` 放入 `util/rawsigs/`**。

# `*_codex.py` 必须遵守的结构

标准叶子结构以如下文件为参考：

- `${PROJECT_ROOT}/util/rawsigs/profit_compound_acc_codex/profit_compound_acc_codex.py`

固定顺序：

1. `class xxx_sig_(stkfactor):`
2. `def __init__`
3. `def initdataclass_`
4. `def sigconstructperiods_`
5. `if __name__ == '__main__':`
6. `periods = WindTradingDay_(...)`
7. `self = xxx_sig_(...)`
8. `sigdata = self.getfac_(periods=periods)`
9. `stkpool = getstkpool_(periods=periods, listtdays=240, noSTtdays=60)`
10. `pd.merge(...)`
11. 去极值
12. `neutfactorclas_()`
13. `Stkfactorbacktest_()`
14. `RankIC / group_test / print`

标准执行骨架：

```python
class profit_compound_acc_codex_sig_(stkfactor):
    def __init__(self, ...):
        ...

    def initdataclass_(self):
        ...

    def sigconstructperiods_(self, periods=()):
        # 这里调用 func.py / util 非rawsig 的共享公式与工具
        ...


if __name__ == '__main__':
    import pandas as pd
    from util.WindTradingDay import WindTradingDay_
    from util.getStkPool import getstkpool_
    from util.utilfun import winsomadsort_
    from util.neutfactorclass import neutfactorclas_
    from util.stkfactorbacktest import Stkfactorbacktest_

    periods = WindTradingDay_(
        fromdt='20100101',
        todt='20260401',
        IfMonthFirst=True,
    )['date'].tolist()

    self = profit_compound_acc_codex_sig_(...)
    sigdata = self.getfac_(periods=periods)
    stkpool = getstkpool_(periods=periods, listtdays=240, noSTtdays=60)
    sigdata = pd.merge(stkpool, sigdata, on=['date', 'Stkcd'], how='inner')

    sigdata[self.facnameuse] = sigdata.groupby('date')[self.facnameuse].transform(
        lambda x: winsomadsort_(x, mad_n=5)
    )

    neuclass = neutfactorclas_()
    neuclass.init_size_indclass_()
    neusig = neuclass.lntotcap_ind_neut_(
        sigdata[['date', 'Stkcd', self.facnameuse]],
        Ifsize=True,
        Ifind=True,
    )

    btclass = Stkfactorbacktest_(
        stksig=neusig.dropna(),
        startdt='20100101',
        enddt='20260401',
        freq='m',
        groupnum=10,
    )

    RankIC, RankICmean, RankICIR = btclass.RankIC_()
    groupret, lsret, sigret, stksig_group, lsdf = btclass.group_test_()

    print('RankICmean:', RankICmean)
    print('RankICIR:', RankICIR)
    print('lsret:', lsret)
```

执行要求：

- `*_codex.py` 继承 `stkfactor`
- `sigconstructperiods_` 内的公式实现优先调用第二层共享逻辑
- `__main__` 保留完整最小回测尾部
- 去极值在 merge 后、中性化前
- 中性化默认走 `lntotcap_ind_neut_`
- 回测默认走 `Stkfactorbacktest_`
- **`__main__` 中不写 `lsdf.to_csv()` / `lsdf.to_excel()`**。`group_test_()` 返回的 `lsdf` 通过 `baskettest_()` 计算顶部/底部组的日度组合收益，对稀疏分组（如 0/3 失败的因子）返回大量 NaN，导致写入的 CSV/Excel 文件只有首行有值。正确做法：只写 `print('lsret:', lsret)` 和 `metrics.json`（metrics.json 中的 lsret 从 sigret 的按日期-分组均值相减计算，不受此问题影响）。参考标准写法：`${PROJECT_ROOT}/util/rawsigs/profit_compound_robust_growth_codex/profit_compound_robust_growth_codex.py`。

# dvcoder 三阶段执行闭环（主入口）

本系统采用三阶段流水线：**语义预审 → 算子+验证 → evaluator 复审**。详见 `## 7. dvcoder 的三阶段执行闭环`。

## 0. 因子库查重（强制前置-语义预审阶段的第一步）

在进入任何实现之前，**必须先执行四层强制查重**，确认候选不是库内既有因子（含参数化家族在声明参数域内的任何实例）。**严口径（2026-09-07 用户/老师确认）：参数实例 = 重复。**

判定标准：
1. **公式/口径重复** — 候选公式与库内条目公式一致（或仅数据口径/回测区间不同）→ 重复。"回测时间区间一致"不是必要条件：同公式换回测区间不构成新因子。
2. **单调等价重复** — 经倒数/差分/取负/重缩放/镜像可映射到库内因子 → 重复。
3. **参数实例重复** — 候选是库内参数化家族声明参数域内的实例 → 重复，**即使该参数组合的因子值尚未物化**。判例：`amihud_dxy_<lookback>`（amihud.py 默认 60，R125 的 10d 实例 = 重复）；`x2p/profit2p` 的 `signamex∈{np,nptopc,gp,op,ebit,ebitda,totp,...}`（R96-R100 yield 家族）；`profit2ev` 的 gp/op/ebitda（R71/R73 EV 家族）；`profit2income(gp/totopinc)`（R88 毛利率水平）；`cf2p`（R94 cfo_yield）；`d2p`（R93 dividend_yield）；`gp_growth_qoq_codex` 的 lag 变体（R22）。
4. **同经济含义重复** — 名称/写法可不同，但经济学含义相同 → 重复。判例：SUE（R107）↔ `sueall/surall/suprofit/sud_generic_codex` 意外盈利族；B2P（R110）↔ `b2p.py`（默认 eqtopc/totcap，一字不差）；return_skewness（R103）↔ `retskew60_codex`（默认 window=60）。

查重数据源（按序）：`${PROJECT_ROOT}/database/factor_library.db` → `${PROJECT_ROOT}/util/factor_library_registry.json`（v1 自动生成，含各家族 `init_defaults` 与 `param_domain_hints`）→ `${PROJECT_ROOT}/util/rawsigs/` 代码核对。注册表是辅助索引：命中或存疑时**必须**打开 `rawsigs/<name>/<name>.py` 核实代码证据；发现家族参数域未登记时运行 `python ${PROJECT_ROOT}/util/build_factor_registry.py` 重建。

> 批量候选/单候选审计的操作方法、已知参数化家族清单（amihud_dxy_<N>、x2p/profit2p/cf2p/d2p/profit2ev/profit2income、sueall 意外族等）与判例：见 `references/factor-library-dedup-audit-method.md`。

**查询方式**（详见 `a-share-factor-review` skill 的「dvcoder 读取规范」章节）：

```python
import sqlite3, hashlib, json, re

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
    return row is not None
```

存在则退回语义空间。**但是 dvcoder 不得跳过 evaluator 自行关闭方向**——即使 dvcoder 确信是重复，仍必须提交 evaluator 做正式确认。提交的 handoff 应包含结构化证据包，供 evaluator 直接验证，避免 evaluator 浪费 token 重复查找证据。

**自识别重复的标准 handoff JSON 格式（R85 案例验证）：**

```json
{
  "stage": "semantic_pre_review",
  "candidate": "Dividend Yield = dividend_ttm / totcap",
  "dvcoder_verdict": "duplicate",
  "duplicate_evidence": [
    "${PROJECT_ROOT}/util/rawsigs/d2p/d2p.py — implements d2p_sig_('dividend_ttm2totcap')",
    "${PROJECT_ROOT}/database/facdata/stock/dividend_ttm2totcap.feather — factor value file exists",
    "factor_library.db — d2p entry already registered",
    "${PROJECT_ROOT}/util/dividend_payout_stability_utils.py — loads d2p_sig_('dividend_ttm2totcap')"
  ],
  "coverage_snapshot": {
    "existing_periods": 196,
    "existing_rows": 425420,
    "existing_per_date_median": 2051
  },
  "request_to_evaluator": [
    "confirm whether candidate is fully covered by existing entry",
    "if not duplicate, explain the novelty boundary explicitly",
    "if duplicate, close primary direction and stop operator entry"
  ]
}
```

**规则要求：**
1. dvcoder 不得因自发现重复而用 `kanban_complete()` 结束 task，仍必须用 `kanban_block(reason="review-required")` 提交
2. 证据包必须包含至少两类来源（因子值文件 + 库条目 + rawsigs 代码），不能仅凭记忆或名称相似断言重复
3. evaluator 收到后做正式确认——若 evaluator 发现不重复（如公式虽同名但口径/滞后不同），则重开方向
4. evaluator 确认重复后关闭方向并提供下一方向建议，default 清理 blocked task 并创建下一轮

**注意**：
- `formula_hash`（md5 精确匹配）只是四层查重中的**第一层工具**；**严禁仅凭哈希未命中即判定不重复**，必须继续家族/参数实例与单调等价检查。2026-09 审计证明：amihud_dxy_10、SUE、B2P、return_skewness、x2p 家族实例全部哈希不命中但全部为重复。
- 若 `factor_library.db` 中无匹配，仍需对照 `util/rawsigs/` 中相似方向的因子检查**单调等价/镜像/参数实例关系**，见 `a-share-factor-review` Pitfalls
- 即使指标优秀，重复因子也不应构建
- **语义预审 handoff 必须附带查重报告**（列出逐条比对的库内家族/参数域/证据路径，或"四层均无命中"结论）；查重报告缺失时 evaluator 不得给出 PASS（2026-09-07 规则，防 R93 复发：R85 曾关闭 dividend_ttm2totcap，R93 又原样重建 dividend_yield_level）
- 守则：`只学方法，不套结论` 不只适用于外部研报，也适用于因子库——因子库中的因子是"已有结论"，新因子必须是因子库之外的新概念

## 1. 因子定义

先明确：

- 因子经济学逻辑
- **与因子库的差异性**（明确指出与 `${PROJECT_ROOT}/util/rawsigs/` 中已有因子的区别）
- 变量映射
- 股票池
- 中性化口径
- 回测区间
- 频率
- 快速验收指标

## 2. 三层定位

先判断本次工作落在哪里：

- 原子字段/原子信号 → 第一层
- 共享公式/共享工具 → 第二层
- 最终叶子封装 → 第三层

## 3. 最小实现

先写最小可运行版本，不一次性堆太多参数和变体。

## 4. 初步测试

最少检查：

- 因子值是否生成成功
- merge 后样本是否异常缩水
- 去极值/中性化是否报错或产生结构性空值
- `RankICmean / RankICIR / lsret` 是否可解释
- 代码、产物、说明是否一一对应

## 5. 失败回流规则

如果初步测试不通过，固定顺序如下：

1. **先改参数**
   - 如 `lagqnum`
   - `window`
   - `fiscaltype`
   - 频率
   - 分组数
   - 去极值 / 中性化细口径

2. **改参数仍不行，再换方向**
   - 改变量关系
   - 改算子表达
   - 改假设方向
   - 改候选机制

3. **换方向仍不行，删除**
   - 删除失败候选代码与中间产物
   - 不把失败候选伪装成沉淀资产
   - 不把失败候选送入正式库

## 6. 每轮目录结构与产出规范

### 目录结构

每轮一个目录，统一放在 `review_queue/` 下：

```
review_queue/roundX_direction_name/
├── xxx_codex.py              ← 第三层叶子文件（内含 __main__ 回测尾部，不写独立runner）
├── data/                      ← .feather 因子值文件
├── backtest/                  ← .xlsx .csv 回测结果（RankIC/groupret/lsdf）
└── result/                    ← 留档文件（不加 roundX_ 前缀，已在目录中）
    ├── formula.md             ← 数学公式 + 变量映射
    ├── hypothesis.md          ← 经济学含义 + 预期有效性 + 失效条件
    ├── summary.md             ← 短摘要 + 文件索引（不内嵌 formula/hypothesis/manifest）
    ├── run_manifest.json      ← 机器可读的配置清单
    └── dvcoder_handoff.md     ← 必写交接文件（向 evaluator 报告用）
```

### 共享函数规范

各轮之间共用的公式/工具函数，**不放在轮次目录内**。应下沉到：
- 原子信号 → `${PROJECT_ROOT}/util/rawsigs/`（对应组名下）
- 共享公式/工具 → `${PROJECT_ROOT}/util/`（非 rawsig 目录）

### 禁止事项
- 不写独立 runner 文件（codex 的 `__main__` 已经承担了）
- 不写轮次专属 family_func（共享函数下沉）
- 文件不加 roundX_ 前缀（已在对应目录中）

## 7. dvcoder 的三阶段执行闭环

本系统采用三阶段流水线：**语义预审 → 算子+验证空间 → evaluator 复审**。

### 阶段 1：语义预审（先审因子能不能做）\n\ndvcoder 完成语义空间构思后（因子名称、经济学含义、公式草案、变量映射），**先提交 evaluator 做语义预审**。\n\n**提交方式：** 必须使用 `kanban_block(reason="review-required: <语义预审包路径>")`，**不得使用 `kanban_complete()`**。因为 `kanban_block` 会触发 pipeline 规则1（创建 evaluator 预审 task），而 `kanban_complete` 会让调度器认为本轮已完结，跳过下一阶段。

evaluator 预审仅审查三项：
1. 经济学含义是否成立、是否能用单一名称概括
2. 单因子合规性（不是多因子组合）
3. 因子库重复性（`${PROJECT_ROOT}/util/rawsigs/` 中无等价因子）

通过后才进入算子空间。打回则回到语义空间重新构思，**不浪费编码时间**。

### 阶段 2：算子空间 + 验证空间

- 按三层架构（rawsig/rawsigs → util/非rawsig → *_codex.py）构建。
- codex 内含 `__main__` 回测尾部，不写独立 runner。
- 调参通过 `__init__` 参数进行。
- 若指标不达标，先在算子空间内调参；若仍无效，回到语义空间改方向（**不需重新走 evaluator 预审，除非改了经济学含义**）。

### 阶段 3：初筛 + evaluator 复审

dvcoder 整理完整留档后，根据结果走对应路径：

**路径 A — 三项指标中至少两项达标且经济学含义已通过语义预审（复审）**
- dvcoder 提交 evaluator 做复审（检查实现与语义预审一致、三层架构正确、代码正确性）
- evaluator 通过 → 提交人工终审
- evaluator 不通过 → 给出修改方向，dvcoder 继续下一轮

**路径 B — 三项指标仅一项达标或全部未达标（失败报告）**
- dvcoder 向 evaluator 提交失败分析：做了什么尝试、当前最佳值、卡住的原因
- evaluator 审查失败报告，给出下一轮修改方向
- dvcoder 按 evaluator 方向进入下一轮迭代

**dvcoder 不得自评"不送 evaluator"。** 无论通过还是失败，都必须向 evaluator 报告。

**提交方式规则：**
- dvcoder 完成**语义探索**后 → 必须使用 `kanban_block(reason="review-required: <语义设计包路径>")` 提交给 pipeline，**不得用 `kanban_complete()`**
- dvcoder 完成**算子实现**后 → 必须使用 `kanban_block(reason="review-required: <实现产物路径>")` 提交给 pipeline，**不得用 `kanban_complete()`**
- evaluator 完成任务后 → 使用 `kanban_complete()` 正常结束
- `kanban_block` 告诉 pipeline "有产出需要下一道工序"，pipeline 会自动创建 evaluator task
- `kanban_complete` 告诉 pipeline "本轮已完结"，下一阶段不会被自动触发

若首轮任务发现以下基础目录不存在，`default` 或 `dvcoder` 应在继续执行前自动创建：

- `${PROJECT_ROOT}/docs/session_handoffs/`
- `${PROJECT_ROOT}/factor_replicate_outputs/review_queue/`
- `${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/`

`evaluator` 在审查时以此作为最低参考门槛（非硬性否决线）。即使指标未达门槛、但改进轨迹清晰（如连续多轮 IR 从 0.97→1.26→1.72），`evaluator` 也应给出阶段性方向建议而非直接否决。  

## 8. Multi-Round 迭代进化规程（历史参考）

> ⚠️ **规则约束提醒**：本节中的"非线性升级轮"、"信号源 Swap"等章节提及的 gated / regime / OR 门结构来自旧范式历史经验。**在当前新规则下**：
> - 禁止多因子组合（单因子规则——任何缺乏单一经济学含义的多因子组合均不允许）
> - 门控/奖励默认不加，除非经济学含义明确要求
> - 因此 regime fusion、OR gate、threshold gate 等结构**不得再自动沿用**，除非能提供明确的、非历史数据优化的经济学理由
>
> 本节保留旧经验作为方法学参考（记录哪些路走过），但不代表当前轮次可以直接沿用这些结构。

**Evaluator 下一方向建议的优先级规则：** evaluator 给出的下一方向建议是参考而非命令。如果该方向已被以前轮次完全探索并正式关闭（如曾被 evaluator 自己判定 0/3 关闭），用户可以行使 domain authority 否决该建议并指定其他方向。dvcoder 和 default 不应在用户明确否决后仍继续执行 evaluator 的建议方向。default 在编排时应在 task body 中注明"用户否决了 X 方向"以避免混淆。

当单轮完成后（无论是否达到指标门槛），由 default 创建下一轮 task 或由 evaluator 决策是否结束迭代。每轮是一个独立的 kanban task，由 default 编排、dvcoder 执行。禁用一次性把所有轮次全写在同一个 task body 里。

### 每轮的标准结构

```
[前置知识] 引用的 handoff 文件路径 + 1-2 句摘要
[本轮方向] 明确正在改进哪个维度（变量、表达、结构、参数）
[seed 列表] 至少 3 个 seed：主 seed、简洁对照、统基基线
[留存约束] 产物命名规范、目录
```

### 轮次演进序列（参考 6 轮经验）

1. **方向验证轮** — 用最小变体验证经济学假设是否成立，IC 方向是否合理
2. **表达迭代轮** — 换变量换算子，最大可能挖掘该方向的信号强度
3. **非线性升级轮** — 引入 gated / interaction / regime 等条件结构
4. **网格验证轮** — 有限参数网格搜索，确定是否已到 plateau

### 信号源 Swap（signal transpose）模式

> ⚠️ 注意：以下提及的 OR gate / regime fusion 来自旧轮历史经验，在新规则（门控默认不加）下不得自动沿用。此处保留仅作方法学记录。

当网格验证确认当前信号维度已到 plateau 后：

- **保留已证明有效的结构**（如 OR gate、regime fusion），不要从头开始重新设计结构
- **换掉信号维度本身**（如从 finexp/asset 融资压力换到 OCF/OPProfit 现金流质量）
- 单维度结构改良优先于双通道并行。R7+R8 经验：单维度 regime fusion（如 cash quality 自身分档）的效果优于 OR 门融合两个不同信号维度（cash quality × finexp）
- 换信号源后第一轮只用水平对比（level 级信号），而不是马上叠 UNEXPECTED 或交互项

### 跨轮结果比较格式

在汇报多轮演进时，使用以下标准表格格式，按 "Method → ICmean → IR → lsret" 列排列，附带与 baseline 的差值标记：

```
R3 baseline:    penalty           ICmean=0.0133  IR=0.97   lsret=0.048
R5 best:        fusion_rf_gap     ICmean=0.0124  IR=1.26   lsret=0.059
R7 best:        OCF/OPProfit      ICmean=0.0148  IR=1.90   lsret=0.059  ← 最大跃迁
R8 best:        Regime Fusion     ICmean=0.0169  IR=1.78   lsret=??     ← 历史最高 ICmean
```

后轮对照（fusion_rf_gap、penalty）必须在每轮复跑以确保跨轮可比性。当控制组复跑结果与前轮一致时，在汇报中注明。

### 轮间交接规范

每轮 dvcoder 完成时须在 `${PROJECT_ROOT}/docs/session_handoffs/` 下写 handoff 文件，内容至少包含：

- 本轮研究方向与测试变体
- 最优结果（IR / ICmean / lsret）与对照基准
- 关键发现（哪个方向有效/无效、参数敏感性）
- 下一轮建议 seed 列表（含主 seed + 简洁对照 + 统基基线）
- 核心产物索引路径

default 在创建下一轮 task body 时引用该 handoff 文件路径，并在开头附 1-2 句最关键摘要。dvcoder 读取后先读 handoff 文件，再理解当前任务。

### 高原检测（Plateau Detection）

当出现以下全部条件时，**当前表达层已到 plateau，禁止继续调参**：

- 网格搜索 20+ 变体的 IR 极差 < 0.02
- 参数格点间的 avg IR / avg lsret 差异 < 1%
- ICmean 连续 2+ 轮没有明显跃升

 plateau 后的标准动作：

1. **换信号源（signal transpose）**：从当前财务维度切换到另一个，**保留已证明有效的结构，换掉信号维度本身**。例如将惩罚项从"融资压力（finexp/asset）"换成"现金流质量（OCF/OPProfit、OCF/Revenue）"，R7 经验表明这种 transpose 可带来 IR 从 1.26 → 1.90 的量级跃迁。
2. **单维度 regime fusion**：换信号源后，不要立刻叠双通道。R8 证明 OR 双通道（现金质量 × 融资压力）不如单维度 regime fusion（现金质量自身分档）。优先在单个新信号维度内做 regime/threshold 结构改良，而不是并行多个维度。
3. **换结构**：从单因子增量切换到组合融合或加权投票
4. **换数据粒度**：从月频换到更细频率，或引入条件波动率校准
5. **阶段性边界测试**：若 IR>1.0 已有一定区分力，可送 evaluator 做阶段性审查（不带门槛期望）

## 9. 三 Profile 自治循环规程（default 编排用）

> ⚠️ **注意**：本节的编排规则已被 `${PROJECT_ROOT}/HERMES.md §5.1` 的 task 创建权限规则取代。**只有 `default` 能创建新的 kanban task。** `dvcoder` 和 `evaluator` 不得调用 `kanban_create` 创建下游 task。本节保留 default 编排动作的详细步骤供参考，但不改变 `HERMES.md` 的约束。

当需要 dvcoder → evaluator → dvcoder → evaluator → ... 的自治循环时，default 按以下流程编排。这是一个**永不停止的因子挖掘循环**，每出一个候选因子就归档到 `evaluator_passed/`，然后继续下一轮。

### 循环结构
```
dvcoder Round N → blocked → evaluator 审查 → 给下一轮方向 → dvcoder Round N+1 → ... → 最终报告
```

### default 的编排动作
1. 创建 dvcoder task（含完整 spec、技能、门槛）
2. dvcoder 完成后状态变为 blocked（review-required）
3. default 读取 dvcoder 的产出和 handoff。**但在创建 evaluator task 前，必须先通过 SQLite 检查该轮次是否已有对应的 done 状态 evaluator task（中段已完成检测）：** 如果 evaluator 已在上个 pipeline tick 之间被调度并完成审查（常见于 evaluator 快速完成任务而 cron 在下个 tick 才触发），则不应创建新的 evaluator task，直接跳到步骤 6 清理 blocked task + 步骤 7 按审查结论推进。检测方法：`sqlite3 ${HERMES_HOME}/kanban.db "SELECT id FROM tasks WHERE title LIKE '%R{N} evaluator%' AND status='done' ORDER BY completed_at DESC LIMIT 1;"`。_R80 案例：evaluator 语义预审在 2 分钟内完成 PASS，pipeline 下个 tick 误以无 evaluator task 而尝试创建新任务。_

**中段 evaluator 完成后的结论读取：** 当 evaluator 在 mid-cycle 完成时，default 可以通过 `kanban_show(task_id=...)` 读取 evaluator task 的 `runs[-1].summary` 和 `runs[-1].metadata` 来提取 verdict（duplicate/PASS/FAIL）和下一方向建议。不需要等待 comment 结构化输出——metadata 中的 summary 字段已经包含 evaluator 的完整结论。_R112 案例：evaluator 语义预审在 ~70 秒内完成，runs[0].summary 包含完整 verdict 和方向建议。_
4. 创建 evaluator task（引用 dvcoder 的产出路径，要求给出下一轮方向建议）
5. evaluator 完成任务后，default 读取审查结论和下一轮方向
6. **清理上游 blocked task（含 dvcoder + evaluator）：** 这一步必须优先执行。
   1. **清理 dvcoder blocked task：** 如果 dvcoder task 仍为 `blocked` 状态（review-required），使用 `kanban_complete()` 将其关闭（附上 evaluator 审查摘要和方向结论）。理由：(a) blocked task 在 evaluator 完成后无法继续等待任何下游工序，留在 board 上成为 stale 任务；(b) `kanban_list()` 显示的 blocked 计数会掩盖真正需要关注的 review-required 项；(c) 即使方向被 evaluator 关闭且不再需要 dvcoder 继续工作，task 也需要正常完成而非残留。_R67 经验：evaluator 关闭方向后 dvcoder 的 blocked task 若不及时清理，后续管道推进时 kanban board 数据变得不准确。_
   2. **清理 evaluator blocked task：** 如果 evaluator task 也因 `kanban_block(reason="review-required")` 结束（而非 `kanban_complete`），且其审查工作已完成（review 已写入 comment，产物已迁移），同样使用 `kanban_complete()` 将其关闭。evaluator 使用 `kanban_block` 结束的常见场景是等待人工终审——但该 task 的审查工作本身已完成，留在 board 上作为 blocked 会阻塞管道感知（default 在 `kanban_list(blocked)` 中无法区分"正在审查中"和"审查完成待清理"）。_R73 经验：evaluator 完成 PASS 审查后以 kanban_block(review-required) 结束，若不清理，下一轮管道检测到 blocked task 存在但内容已审查完成，造成 board 状态与事实不一致。_
   3. **清理规则例外：** 如果 evaluator task 是 `kanban_block` 且仍在**运行中**（如等待人类输入的 DIAGNOSTIC 模式），不清理。仅清理审查工作已明确完成的 blocked task。
7. 根据审查结论决定：
   1. **通过（含 3/3 达标或 evaluator 认定为可提交人工终审）：** 将候选因子转入 `evaluator_passed/` 目录标记为人工终审候选，然后继续创建下一轮 dvcoder task。下一轮方向选择优先级：
      - 优先使用 evaluator 在审查结论中给出的 `下一轮方向建议`（若有）
      - **当 evaluator 的方向建议全部被方向校验规程验证为 stale 时：** 回溯最近 3-5 轮 evaluator PASS 审查中未使用的次要/备选方向（B-side）。evaluator 在 PASS 审查结论中常同时给出多个方向（如 "Next direction: Primary=X, or Secondary=Y"），但 pipeline 默认走 Primary 链；如果 Primary 链耗尽，Secondary/B-side 方向可能仍是干净的未探索方向。_R132 案例：R128 IVOL PASS 审查建议 "Earnings Stability or FCF Margin"，pipeline 走 Earnings Stability→Earnings Persistence→Employee Productivity (data blocked)，FCF Margin 作为 B-side 方向仍干净可用。_
      - 若 evaluator 未提供方向建议（PASS 审查中常见）或 B-side 也已关闭：default 根据因子库缺口分析自主选择。选择方法：从 `evaluator_passed/` 和 `util/rawsigs/` 中已有的经济学维度中，找到未被探索的财务/基本面维度；对照 `failure_registry.db` 排除已关闭方向；对照 `review_queue/` 中的历史尝试确认该方向未被充分探索；选择干净的单一除法/减法因子。在 task body 中记录选择理由。
      - 若所有已知的财务/基本面维度均已被探索或已关闭，选择与最近通过轮次不同语义族的方向（如估值族通过后，下一轮切换到效率族或偿债能力族），以保持方向多样性。_R73→R74 案例：evaluator 未提供方向，default 分析缺口后选择 cf2fa（OCF/FixedAssets）作为与已完成估值族（op2ev/gp2ev/ebitda2ev）不同的效率族方向。_
   2. **不通过（含方向关闭为重复/失败）：** 按 evaluator 给出的下一轮方向创建 dvcoder task。创建前必须执行方向校验规程（见下方）。
      - ⚠️ **"修正重启"边缘情况（corrected re-start）：** 当 evaluator 在模式 A（语义预审）中的 verdict 是"关闭为重复（duplicate）"但同时明确验证了一个**经过修正变量映射的版本**（同一语义族，同一经济学含义，仅修正了变量映射如分母从 `totdebt_bs` 改为 `findebt_bs`），且 evaluator 已隐含确认修正版本通过语义预审三项检查（经济学含义 ✓、单因子合规 ✓、因子库无重复 ✓）时：
        - **下一阶段应为算子实现（operator），而非新一轮语义探索（semantic）。** 因为语义预审已完成——仅仅是原始变量映射是重复的，修正映射后语义层面已通过。
        - default 在创建 task body 中必须注明"该方向为 evaluator 确认的修正重启版本，语义预审已通过，直接进入算子空间"。
        - 方向校验（failure_registry + factor_library + review_queue）应以修正后的变量映射为准，而非原始映射。
        - _R112→R113 案例：cfo_ttm/totdebt_bs 关闭为重复（cf2debt_codex），evaluator 验证 cfo_ttm/findebt_bs 无重复且语义有效 → default 直接创建 R113 operator task，跳过 R113 semantic。_
8. 重复 2-7 直到用户主动叫停
9. 最终由 default 汇总全部轮次的结果做报告

### default 的方向校验规程（防 evaluator 建议 stale 陷阱）

长时间自治运行后（如 R55→R62+），evaluator 的下一轮方向建议可能指向已在之前轮次中正式关闭的方向（因 evaluator 无 failure_registry 全局视角，且依赖记忆中的旧方向名）。default 在读取 evaluator 审查结论后、创建下一轮 task 前，必须执行以下校验：

**校验流程：**
1. 从 evaluator 审查结论中提取所有建议方向（包括 `next_direction_primary` 和 `next_direction_secondary` 列表中的每一个）。
2. 对每个建议方向，查 `failure_registry.db` 确认是否已被归档为失败：
   ```sql
   SELECT round, factor_group, root_cause
   FROM failures
   WHERE factor_group LIKE '%<关键词>%' AND archived = 0
   ORDER BY created_at DESC;
   ```
3. 同时查 `review_queue/` 目录看该方向是否已有轮次目录但 `evaluator_passed/` 无对应：
   ```bash
   ls ${PROJECT_ROOT}/factor_replicate_outputs/review_queue/ | grep -i <关键词>
   ls ${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/ | grep -i <关键词>
   ```
4. **查 factor_library.db 语义相近方向（即使步骤 2-3 均无关闭记录也必须执行）**：
   当推荐方向存在语义上类似的因子已录入 factor_library 时，方向并非不可用，但 task body 中必须注明与现有库条目的差异说明。_R82 案例：evaluator 推荐ΔROA，`profit2at_qmq`（NP/TA QoQ 变化）已在库中但从未 pipeline 评估。方向可用，但 dvcoder 需采用不同变量映射（如 OP_TTM 代替 NP_TTM）。_
   ```sql
   SELECT factor_name, math_formula, entry_channel, rankic, rankicir, lsret
   FROM factor_library
   WHERE factor_name LIKE '%<关键词>%' OR economic_meaning LIKE '%<关键词>%'
   ORDER BY entry_channel;
   ```
   注意区分两类 `entry_channel`：
   - `initial_inventory` 且指标全为空 → 早期导入，从未 pipeline 评估。方向可用，task body 中注明差异。
   - `human_final_review` 且有记录指标 → 视为重复方向，不推荐（除非 evaluator 要求换表达式重试）。
4. **⚠️ failure_registry.db 覆盖范围警告：** 该数据库仅约从 R54 起才有记录。更早的轮次（R17/R41/R42 等）虽经 evaluator 正式关闭但可能未录入 DB。因此 `failure_registry.db` 返回"无匹配"≠ 方向未关闭。当 DB 无匹配时，必须同时通过以下手段补充验证：
   - 查 `review_queue/` 目录下该方向的历史轮次目录名及其 `dvcoder_handoff.md` 中的 evaluator 结论
   - 反向读取最近 3-5 轮的 evaluator handoff 文件追踪方向流向
   - 查 `references/rounds-1-31-complete-history.md`（若轮次在此范围内）
5. 若 evaluator 的**所有**建议方向（含 secondary）均已在 `failure_registry.db` 或 handoff 追溯中关闭且 `evaluator_passed/` 无对应，执行 **handoff 链追溯**：反向读取最近 3-5 轮的 evaluator handoff 文件（`${PROJECT_ROOT}/docs/session_handoffs/R*evaluator*`），追踪 evaluator→evaluator 的下一轮方向建议链，发现**实际已被 pipeline 跟随的新方向**是哪个。
6. handoff 链追溯后，如果所有方向都已被关闭，从 evaluator 建议中选取**最后一个未被尝试的**方向。选定规则按优先级：
   - 优先选曾在 evaluator 历史审查中获得 **CONDITIONAL_PASS** 但因数据/技术阻塞未推进的方向（"条件通过受阻" > "0/3 正式关闭" > "方向重复/duplicate 关闭"）
     - ⚠️ **重新打开"条件通过受阻"方向前必须验证数据依赖是否已解决。** 例如检查 feather 缓存是否存在：`find ${PROJECT_ROOT} -name '*staff*' -o -name '*feather*' 2>/dev/null | head -5`。若数据依赖仍存在（如 staff feather 缺失且未运行过 `updatedata_()`），不应创建需要该数据的算子 task；而是在 task body 中注明"数据依赖待人工解决（需要运行 XX.updatedata_() 补数据）"，然后考虑下一个未尝试方向。_
   - 若无条件通过的方向，选距离当前轮次最远的关闭方向（关闭时间越久，pipeline landscape 变化越大，值得一次确认性重开）
   - 在 task body 中明确注明"该方向曾在前序轮次中被 evaluator 关闭/受阻，按方向校验规程作为最后一个未尝试方向重新打开"

**决策规则：**
- 至少一个建议方向在 `failure_registry.db`、review_queue/ 检查、handoff 追溯中均无关闭记录 → 正常创建该方向的 task
- 所有建议方向均关闭 → 执行 handoff 链追溯，选取链中断口处的新方向
- handoff 链追溯也找不到 → 检查最近 3-5 轮 evaluator PASS 审查的 B-side（次要/备选方向建议）：evaluator 在 PASS 结论中常同时建议多个方向（如 "Primary=X, or Secondary=Y"），Pipeline 默认走了 Primary 链但 B-side 可能从未探索。若 B-side 经方向校验为可用，以该方向创建下一轮；若 B-side 也已关闭或重复，再按优先级选取最后一个未尝试方向（见校验流程第 6 步）

#### 边缘情况：所有方向均 stale 且唯一可用方向为"条件通过受阻 + 数据依赖未解决"

当执行上述校验流程后，发现 evaluator 的所有建议方向均 stale（已完成/关闭/数据阻塞），且按优先级选取的最后一个未尝试方向（CONDITIONAL_PASS 方向）的数据依赖**仍未解决**时：

1. **不创建算子 task**（数据不可用，codex 无法运行）
2. **改为创建语义探索 task（Round+1）**，方向为该 CONDITIONAL_PASS 方向
3. 在 task body 中明确标注：
   - "该方向的语义预审已在前序轮次（R120）中通过 PASS"
   - "staff 数据依赖经核查仍未解决（feather 缓存不存在）"
   - "本轮为**数据重检语义轮**——dvcoder 需重新确认数据状态，若仍不可用则关闭方向并提交 evaluator 裁决"
4. 使用语义探索的 idempotency_key 格式：`R{N+1}-semantic`
5. 这不算"重复语义探索"——而是"数据状态重检"，因为前序语义工作在一轮之前（R120），中间已间隔 10+ 轮，数据依赖状态可能变化

_R131 案例：R130 failure review → evaluator 推荐 R120 (data blocked) 和 R122/R125 (done) 和 R126/R127 (closed)。方向校验确认全部 stale。按优先级选 R120（CONDITIONAL_PASS + 数据阻塞）。确认 staff data 仍不可用后，创建 R131 semantic task 作为数据重检轮，task body 中注明数据依赖的完整检查路径。_

**关键区别**：这与"修正重启"（corrected re-start）不同——修正重启是语义已通过、变量映射已修正、直接进入算子空间；数据重检轮是语义已通过但数据仍不可用，需要重新确认数据状态，先走 semantic（重检）而非 operator。如果数据状态变为可用，dvcoder 在语义重检结论中应建议"数据已就绪，可直接进入算子空间"——此时 default 可跳过下一轮的语义步骤，直接创建算子 task。

**示例 1（R62→R63 真实案例）：**
- evaluator 建议：① Incremental ROIC ② Asset Growth Rate ③ CapEx/Depreciation
- failure_registry.db 查询：Incremental ROIC 关闭于 R21/R45/R50/R58；Asset Growth Rate 关闭于 R57
- handoff 链追溯：R55→R56(revenue_quality)→R57(asset_growth)→R58(incremental_roic)→R59(profitability_stability, passed)→R60(admin_expense_stickiness, passed)→R61(admin_expense_stability, passed)→R62(selling_expense_stability, closed)
- 结论：CapEx/Depreciation 是唯一未尝试方向 → 创建 R63 任务

**示例 2（R68→R69 真实案例——全部建议均 stale + failure_registry 覆盖缺口）：**
- evaluator 建议：① 经营杠杆（primary）② 有效税率（secondary）③ 劳动效率（secondary）
- failure_registry.db 查询：三方向均无匹配（因 R17/R41/R42 早于 DB 覆盖范围，未录入）
- handoff 追溯补充：R17 经营杠杆 0/3 关闭（evaluator 结论"switch economic dimension"）；R41 有效税率 0/3 关闭（"tax gap 方向已关闭"）；R42 劳动效率 4 seed 全部裁决，关闭方向（但 Seed 2/3 获 CONDITIONAL_PASS，仅因 staff 数据缺失阻塞而非方向无效）
- 结论：均关闭/受阻。按优先级选取劳动效率（CONDITIONAL_PASS + 数据阻塞 > 0/3 正式关闭）→ 创建 R69 task，附方向说明

**示例 3（R80→R81 真实案例——evaluator failure_registry 预校验漏检 + 5 轮连续关闭后切换语义族）：**
- evaluator 建议：① ETR/有效税率（primary）② Inventory Turnover（secondary）
- evaluator 的 failure_registry 预校验返回无匹配（因 R18/R41/R25 早于 R54 DB 覆盖范围），误判为"可用"
- default 方向校验执行 review_queue/ 目录检查：找到 round18_effective_tax_rate（0/3 关闭）、round41_standard_rate_tax_saving_yield（0/3 关闭）、R25_inventory_turnover（CCC DIO 单调等价关闭）
- 同时检查 evaluator 的 secondary 列表中其他方向：labor（R42 CONDITIONAL_PASS 但 staff feather 仍缺失 → 数据阻塞），dividend_yield（无历史记录 → 可用）
- 结论：primary+secondary 均 stale→按最后未尝试方向选取 Dividend Stability → 创建 R81 task，附方向校验日志
- 背景：此时连续 5 轮关闭（R76→R77→R78→R79→R80），附加说明"这是系统运行以来最长的连续关闭序列。当前已探索方向覆盖：现金实现/财务费用/收入稳定/资本密集/商誉 + 早前 13 个通过方向。新增经济维度可能已有限。"
### 当 evaluator profile 不可用时的应急方案

#### 第一步：排查 kanban DB 完整性

evaluator 持续 crash（"pid not alive"、"exit code 1"）的常见根因是 **kanban DB 损坏**，而非 evaluator 配置问题。损坏的 DB 会导致 evaluator 子进程一启动读任务上下文就 crash，典型特征是同任务连续多轮 crash 而 dvcoder 正常运行。

**诊断方法：**
```
sqlite3 ${HERMES_HOME}/kanban.db "PRAGMA integrity_check;"
```
若输出非 `ok` 而是显示 `invalid page number`、`malformed` 等错误，则 DB 已损坏。

**修复方法（优先顺序 — 先尝试从当前损坏 DB 恢复，再回退到备份）：**

**第一步：尝试 `.recover` 恢复当前损坏的 DB（优先于使用旧备份）**

当前损坏的 kanban.db 虽然 PRAGMA integrity_check 失败，但只要 `file` 命令仍显示为 `SQLite 3.x database`，就值得尝试 `.recover`。这是最优路径——保留所有 task 元数据（包括最近的管道推进轮次），而旧备份可能滞后多日。_R140 案例验证：当前 DB 损坏但 file 显示 SQLite 3.x → `.recover` 成功恢复 370 条 task（含 R122-R140 全部活跃轮次），而 bak_before_recovery 仅含 193 条（滞后 7 天）。_

```bash
# 1. 保存损坏文件供取证
cp ${HERMES_HOME}/kanban.db ${HERMES_HOME}/kanban.db.corrupted_$(date +%Y%m%d_%H%M%S)

# 2. 判断能否尝试 .recover
file ${HERMES_HOME}/kanban.db
# 输出 "SQLite 3.x database" → 可尝试

# 3. 直接对当前 corrupted DB 执行 .recover
#    2>/dev/null 静默 defensive off 等无害 pragma 输出
sqlite3 ${HERMES_HOME}/kanban.db.corrupted_* ".recover" 2>/dev/null \
  | sqlite3 /tmp/kanban_recovered.db

# 4. 验证恢复结果的两层检查
sqlite3 /tmp/kanban_recovered.db "PRAGMA integrity_check;"
# 若返回 "ok"，继续下一步。若失败，跳转到第二步（备份恢复）

# 5. 关键验证：确认恢复出的 DB 含有实际数据，而非空 schema
#    ⚠️ 坑：.recover 有时只恢复 schema 而无数据（integrity_check=ok 但空表）
sqlite3 /tmp/kanban_recovered.db "SELECT COUNT(*) FROM tasks;"
# 若返回 > 0，恢复成功。若返回 0（空表），重试一次再接回备份恢复

# 6. 成功验证后替换为工作 DB
cp /tmp/kanban_recovered.db ${HERMES_HOME}/kanban.db
```

> **⚠️ `.recover` 空 schema 陷阱**：R140 经验表明，`.recover` 偶尔生成 schema-only DB（integrity_check="ok" 但 tasks 表为空）。此现象无一致性规律——同一 corrupted 源文件重新运行 `.recover` 即可正常恢复。若第一次恢复出空 schema，换输出文件名重试一次。

**第二步（`.recover` 失败时的回退）：从备份恢复**

当 `.recover` 失败或恢复出空 DB 且重试仍空时，回退到备份恢复：

```bash
# 1. 检查所有备份文件的完整性
for f in ${HERMES_HOME}/kanban.db.bak_* ${HERMES_HOME}/kanban.db.malformed_*; do
  [[ "$f" == *-shm || "$f" == *-wal ]] && continue
  result=$(sqlite3 "$f" "PRAGMA integrity_check;" 2>&1)
  echo "$(basename $f): $result"
done

# 2. 优先选择返回 "ok" 的最新备份（直接 cp 可用）
#    若无 "ok" 备份，选 malformed 备份用 .recover 修复
cp ${HERMES_HOME}/kanban.db.bak_before_recovery ${HERMES_HOME}/kanban.db

# 3. 验证
sqlite3 ${HERMES_HOME}/kanban.db "PRAGMA integrity_check;"
```

**⚠️ 恢复后关键步骤：检查 failure_registry.db 是否需要初始化。注意 `failure_registry.db` 是独立数据库，不受 kanban DB 损坏影响。**

`bak_before_recovery` 备份通常早于 R56+ 的管道推进。恢复后 `failure_registry.db` 可能为空或只有少量旧记录——因为管道在恢复后继续运行了多轮，而 evaluator 写入的失败记录在 DB 损坏时没有被传回新的备份 DB 中。

**关键区别：非 SQLite 头损坏 vs 正常 SQLite 损坏**：当 `PRAGMA integrity_check` 返回 `file is not a database (26)` 而非 `malformed`/`invalid page number` 时，说明 DB 文件头已被完全覆写（非 SQLite 格式），此时无法对当前 `kanban.db` 直接运行 `.recover`。必须从备份文件中找一个仍是 SQLite 格式的文件——即使 `PRAGMA integrity_check` 返回 `malformed`，只要 `file` 命令显示 `SQLite 3.x database`，就值得尝试 `.recover`。判断流程：`file ${HERMES_HOME}/kanban.db` → 非 SQLite → 扫描备份文件 `file ${HERMES_HOME}/kanban.db.malformed_*` → 找到 SQLite 格式的备份 → `sqlite3 <备份> ".recover" | sqlite3 /tmp/recovered.db` → 验证。

**⚠️ `.recovered` 0 字节陷阱**：系统自动恢复机制可能创建 0 字节的 `kanban.db.recovered` 文件。`PRAGMA integrity_check` 对该空文件返回 "ok"（空 schema 也是合法的），但实际不含任何数据。不要误以为该文件是可用备份——它只是空的 schema-only DB。恢复操作永远基于 `.bak_*` 或 `.malformed_*` 文件手动执行 `.recover`，而非依赖系统自动创建的 `.recovered` 文件。

**恢复后必须执行的操作**：读取 `review_queue/`、`evaluator_passed/`、`docs/session_handoffs/` 中的 handoff 文件，按时间顺序提取 evaluator 结论（关闭 / 通过 / 重复），补写 `failure_registry.db` 记录。每个关闭方向写入一条：

```python
# 从 handoff 文件提取状态后写入
conn.execute("""
    INSERT OR IGNORE INTO failures 
        (round, factor_group, factor_names, step, scope, root_cause, verified, evaluator_verdict, direction_provided)
    VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
""", (
    round_num,        # 如 "R63"
    factor_group,     # 如 "capex_to_deprec"
    factor_names,     # 涉及的因子名
    step,              # 'semantic_review' 或 'pipeline_review'
    scope,             # 失败范围
    root_cause,        # 根因
    f"DB recovery reconstruction: closed during pipeline, original kanban records lost",
    direction_provided  # 0 或 1
))
```

**自动补写不写 evaluator_passed 通过的记录**——通过的候选已在 `evaluator_passed/` 目录下有产物，不需要写在 failure_registry 中。

**手顺总结**：恢复 DB → 扫描 handoffs 重建轮次状态 → 补 failure_registry → 读取最新 evaluator 的下一方向建议 → 创建下一轮 task。

**次级方法（当 malformed 备份也不可用时）：**
```
sqlite3 ${HERMES_HOME}/kanban.db ".recover" | sqlite3 /tmp/kanban_recovered.db
cp /tmp/kanban_recovered.db ${HERMES_HOME}/kanban.db
```
修复后用 `PRAGMA integrity_check` 验证。修复后 evaluator 任务会被 dispatcher 自动重新调度，无需人工干预。

#### 第二步：DB 完好时的回退方案

如果 DB 完整性检查通过，但 evaluator profile 仍持续 crash（非配置问题导致），default 可以使用 `delegate_task` 生成一个独立子 agent 作为审查者：
- 子 agent 独立运行，不共享当前 conversation 上下文
- 加载 `a-share-factor-framework` 和 `a-share-factor-review` 技能
- 在 `delegate_task` 的 `context` 中传入完整审查规格（路径、门槛、检查项）
- 子 agent 的审查结论作为 evaluator 的等价物写入 kanban 评论
- 注意：这是应急方案，优先仍应使用 evaluator profile

#### 第三步：DB 恢复后的管道状态重建（mid-pipeline task gap）

当 kanban DB 因损坏需要从早前的备份恢复时（如从 02:05 的 `bak_before_recovery` 恢复，而当前实际时间已是 14:30），恢复后所有在备份时间戳之后创建的 kanban task 记录会丢失。**重建流程**：

1. **先保存损坏文件供取证：** `cp kanban.db kanban.db.corrupted_$(date +%Y%m%d_%H%M%S)` — 不可丢弃，因为所有丢失的 task 元数据（id、创建时间、comments）只在原 malformed DB 中。

2. **扫描文件系统重建状态：**
   - 检查 `review_queue/` 目录按时间排序：`ls -lt ${PROJECT_ROOT}/factor_replicate_outputs/review_queue/ | head -10`
   - 检查 `evaluator_passed/` 目录按时间排序：`ls -lt ${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/ | head -10`
   - 检查 `docs/session_handoffs/` 目录：`ls -t ${PROJECT_ROOT}/docs/session_handoffs/ | head -10`

3. **优先检查 `pipeline_state_handoff.md` 加速重建：** 当丢失的轮次较多（5+ 轮），先查找最新的 `session_handoffs/` 目录下是否有 `pipeline_state_handoff.md` 或类似汇总文件（如 `R72/pipeline_state_handoff.md`）。该文件是跨轮状态汇总，包含当前最新轮次、方向校验结论、evaluator_passed 滞留清单等，比逐个读取 dvcoder_handoff.md 效率更高。若找不到汇总文件，再按以下流程逐轮追溯。

4. **对每个丢失的轮次，读取 dvcoder_handoff.md 确定状态：**
   ```
   review_queue/RXX_<direction>/result/dvcoder_handoff.md
   ```
   关键信息：阶段标识（semantic / operator）、verdict（通过/失败/待审）、提交路径。

4. **状态归因规则：**
   - 若 `evaluator_passed/` 中存在且目录名匹配 → 已通过 evaluator 审查，无需重建
   - 若 `dvcoder_handoff.md` 包含 "review-required" 且 `evaluator_passed/` 无对应 → 需重建 evaluator task
   - 若仅 `review_queue/` 中有语义设计包（无 codex 文件）→ 需重建 evaluator 语义预审 task

5. **创建替代 task：**
   - 使用 `idempotency_key` 格式 `round{RoundNum}-{phase}`（已在恢复前 DB 中不存在，是安全的）
   - 在 task body 中注明 "DB恢复重建：原kanban记录于 YYYY-MM-DD HH:MM DB损坏时丢失"
   - evaluator task body 中尽量引用磁盘上的完整产物路径（即使原 task body 丢失，产物仍在）

6. **验证与常见问题：** `kanban_list()` 确认新建 task 状态为 `ready`。若 dispatcher 已跳过该轮次继续推进，则只需补齐最近一轮的 evaluator review task，恢复链条即可继续。
   - ⚠️ **`kanban_list(limit=200)` 可能触发 I/O 错误**：恢复后的备份 DB 对大范围查询敏感。若遇到 `disk I/O error`，改用更小 limit（如 `limit=50`）或按状态过滤的查询（`status=blocked` / `status=ready`）。这不影响 DB 完整性——较小的查询正常工作。

7. **检查 cron job 状态：** DB 损坏期间，管道推进器 cron job 可能因反复失败被系统自动暂停（`paused_at` 字段非空）。恢复后必须检查并重新启用：
   ```bash
   # 检查 cron 状态
   python3 -c "
   import json
   with open('${HERMES_HOME}/cron/jobs.json') as f:
       d = json.load(f)
   for j in d['jobs']:
       print(f\"{j['name']}: enabled={j['enabled']}, state={j['state']}, paused_at={j.get('paused_at','n/a')}\")
   "
   ```
   若 `enabled=false` 或 `state=paused`，使用 `cronjob(action='enable')` 重新启用，或手动修改 `jobs.json` 中对应 job 的 `enabled=true`、`state=scheduled`。注意 `state=scheduled` 但 `paused_at` 非空是恢复后的正常中间态——下次调度会清除 paused_at。

# 候选因子存放位置与复核流程（按三阶段流水线）

## 阶段 1：语义预审产物

语义设计方案不用存 review_queue，dvcoder 完成语义构思后直接提交 evaluator（通过 kanban comment 或 handoff 文件）。通过后进入算子空间。

## 阶段 2：算子空间产物

候选因子目录放在：
- `${PROJECT_ROOT}/factor_replicate_outputs/review_queue/roundX_direction_name/`

目录结构：
├── xxx_codex.py
├── data/（.feather）
├── backtest/（.xlsx .csv）
└── result/
    ├── summary.md（短摘要 + 文件索引；不承载 formula/hypothesis/manifest 正文）
    ├── formula.md
    ├── hypothesis.md
    ├── run_manifest.json
    └── dvcoder_handoff.md（必写）

## 阶段 3：evaluator 复审通过后

候选因子转入：
- `${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/<facname_codex>/`

之后仍需等待人工终审。未经人工审批通过不得进入 `${PROJECT_ROOT}/util/rawsigs`。

## 当 evaluator 通过但人工终审不通过

- 默认回到 `dvcoder`
- 以上一轮 `${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/<facname_codex>/` 为输入种子
- 优先从语义空间 / 表达层复盘：
  - 机制假设是否站得住
  - 变量映射是否偏了
  - 公式表达是否需要调整
- 除非人工明确指出数据口径错误、样本构造错误或 ETL 口径错误，否则不从 ETL 重跑起
- 新一轮候选重新进入 `review_queue`，再走完整复核链路

## 删除规则

- 初测不通过且经过"调参 → 换方向"后仍无效的候选，删除。
- 未通过 `evaluator` 复核的候选，不进入正式库。
- 未通过用户人工审查的候选，不进入正式库。
- **失败候选的清理粒度：** 删除时区分两类产物：
  - **删除**：`*_codex.py`、因子值文件（`.feather`）、回测结果（`.xlsx`/`.csv`/`metrics*.json`）—— 这些是具体实现和测试产物，失败后无保留价值。
  - **保留**：`formula.md`（数学公式 + 变量映射）、`hypothesis.md`（经济学含义 + 失效条件）—— 这些是方法学记录，供后续反思："什么表达路径已充分验证不可行"，避免重复投入。`summary.md` 和 `run_manifest.json` 视情况可留可删。

# Deliverables

默认交付尽量包括：

- 因子实现代码
- 因子值文件
- quick backtest 结果
- `RankICmean / RankICIR / lsret`
- 候选因子所在目录路径
- `summary.md`
- `formula.md`
- `hypothesis.md`
- `run_manifest.json`
- `dvcoder_handoff.md`
- 当前结论：通过 / 不通过 / 删除
- 下一步动作：交 evaluator / 等待人工审查 / 删除重来

# Reference policy

- `references/` 是辅助材料，不是第一入口。
- 主 `SKILL.md` 保持类级别主结构：只放稳定的触发条件、边界、三层架构、执行闭环、交接门槛、交付物与检查清单；不要把一次 session 的清理记录、恢复记录、文件盘点、linked_files 全量清单堆回主文。
- 很多 `references/` 来自过去的 session learnings、debug 记录、专题实现说明。
- 凡是带日期、session 色彩、一次性 debug 结论的 reference，都要按“可能过时”处理。
- 使用 `references/` 时，优先学方法、模板、坑点；不要把旧经验原封不动当当前结论。
- `references/README.md` 是唯一默认导航入口；按 `01-architecture / 02-data-pipeline-and-neutralization / 03-factor-patterns / 04-audit-and-governance` 分组索引 active 文档。
- `references/single-factor-economic-meaning.md` 是单因子判断指南，包含✅/❌ 示例与自查清单。
- `references/first-principles-startup.md` 是每轮第一性原理启动模板，dvcoder 进入语义空间前必须参考。
- `references/04-audit-and-governance/autonomous-dvcoder-evaluator-loop.md` 是自治 dvcoder→evaluator 多轮迭代循环的运行规程，由 default 编排时使用。
- `references/04-audit-and-governance/pipeline-round-audit.md` 是跨轮次审计规程，当需要盘点全部已探索轮次时使用：收集 handoff → 整理状态表 → 交叉验证 review_queue + evaluator_passed → 识别缺口和重复 → 输出报告。
- `references/04-audit-and-governance/cron-pipeline-blindspot-fix-20260728.md` — 管道推进 cron 盲区修复记录（R114 6.5h 卡顿根因 + 修复方案）
- `references/04-audit-and-governance/codex-api-connectivity-test.md` 是 dvcoder GPT 账号连通性测试方法，使用 Codex Responses API 而非标准 Chat Completions API。
- `references/factor-library-gaps.md` 是因子库缺口清单，记录已有因子分类和已验证缺失的经济学维度，供 dvcoder 确认新颖性时查阅。
- `references/r16-r18-failure-cycle-methodology.md` 是 R16-R18 三轮连续失败的方法学记录，记录被充分验证不可行的表达路径及其根因（结构性分母近零、信号强度不足、维度同质性），供后续避免重复投入。
- `references/r113-r114-conditionally-passed-data-blocked-pattern.md` 是最近两轮（R113→R114）的模式记录，包含 2/3 近阈值 CONDITIONAL_PASS 的 evaluator 自主归档处理，以及数据阻塞方向的语义 task 创建模式。default 在编排时遇到类似情况可参考。
- `references/pipeline-cron-blocked-task-blindspot.md` 是 pipeline cron 对 blocked dvcoder task 的检测盲区修复记录（R114 案例：6.5 小时延迟），说明 cron prompt 中"刚完成"时间模糊词的危害和修复方案。default 和 orchestrator 在修改 pipeline cron prompt 时必须参考。
- `references/rounds-1-31-complete-history.md` 是 Rounds 1-31 完整因子挖掘历史总览，包含每轮方向、指标、结论和跨轮模式总结。当不确认某方向是否已试过时，优先查询本文件后再决定新方向。包含成功模式（qoq增长率差额）、失败模式（多因子组合违规、方向重复、同源重复）和流程问题（代码提前入库、重复调度、候选项卡阻塞）。
- `references/02-data-pipeline-and-neutralization/financial-data-group-matrix.md` 是财务数据加载函数与 group 的映射表，说明不同数据组分别用哪个 family func 加载。
- `references/02-data-pipeline-and-neutralization/a-share-income-statement-formula-chain.md` 是 A 股利润表公式链的数据库验证版，包含字段映射、真实数据验证的会计关系链、常见误解纠正。当需要验证因子公式中的会计关系是否正确时（如 gp 是否 = rev - cost、np 是否 = totp - tax），优先参考此文件。
- `references/03-factor-patterns/standalone-single-factor-backtest.md` 是\\\"归零轮\\\"独立脚本回测模板，供 dvcoder 在快速测试多个单因子时参考。
- `references/kanban-task-creation-chain.md` 是 kanban task 创建链的权威参考，明确 dvcoder/evaluator 不得调用 kanban_create 以及 default 的永不停机编排流程。详见 `${PROJECT_ROOT}/HERMES.md §5.1`。
- `references/03-factor-patterns/pairfactorclass-patterns-catalog.md` 是 `pairfactorclass_` 共享类的可用模式目录，当需要写薄叶子 codex 时优先查阅。
- 当用户要求在改 workflow / 改代码之前先盘点或精修 active references 时，先给出当前 active references 的完整分组清单（组别 + 数量 + 文件名），再分开说明：哪些已是当前 canonical 方法口径，哪些仍属于待修改项；不要把 active 与 archive、盘点与改造建议混成一团。
- `archive/legacy_references/` 只用于追溯旧 session/debug/recovery/dedup/dated 材料，不作为默认规则来源。
- 后续整理 `references/` 的目标不是“linked_files 数量最大化”或“把历史文件全收回”，而是：
  - 只保留不过时内容
  - 删除重复内容
  - 按主题分组
  - 让主文与 reference 分层清晰
- 后续整理时，应优先删除：
  - 已被新主规则覆盖的旧说明
  - 只记录一次性会话现象的旧 note
  - 与当前三层口径冲突的旧规则
  - 仅为了补齐 coverage 而恢复、但没有 durable 方法价值的旧文档

# Common pitfalls

- 把项目级规则、profile 工作流、skill 细则、历史经验混写在一起
- 把共享逻辑写进 `*_codex.py`
- 只改叶子层，不核对第一层和第二层
- 初步测试不通过还继续保留失败候选
- 没经过 `evaluator` 复核就直接跳过审查（dvcoder 不得自评"不送 evaluator"，无论指标是否达标都必须向 evaluator 报告，失败报告或全面审查均可）
- 不把旧 dated reference 当成当前硬规则
- **DB 恢复后任务丢失陷阱 — mid-pipeline task gap**：当 kanban DB 因损坏从早前备份恢复后，备份时间戳之后创建的所有 task 记录会消失。典型表现：`kanban_list()` 显示所有 task 均为 `done` 状态且无 running/blocked task，但 `review_queue/` 目录中最新轮次显示有 ~1-2 小时前的 dvcoder 产物（含 codex + 回测 + handoff），说明管道已在备份后推进了多轮。修复：按「第三步：DB 恢复后的管道状态重建」流程，从磁盘扫描重建丢失的 task。同时记录损坏源 DB 文件供取证（`cp kanban.db kanban.db.corrupted_$(date +%Y%m%d_%H%M%S)`），不要直接覆盖。⚠️ 注意：idempotency_key 在恢复后的 DB 中不存在，即使原 task 已被调度过，新建 task 也不会被去重——这是正确的，因为原 task 确实需要重建。
- **DB 恢复后 stale running task 陷阱（R117 案例）**：从旧备份恢复 kanban DB 后，可能残留一批在旧 DB 中标记为 "running" 的 task。这些 task 在旧 DB 中曾有 worker 执行过，但因 DB 损坏+恢复切断了 worker 的 PID 追踪，永远不会再完成。如果不手动清理，它们会持续占据 "running" 状态，干扰 pipe 对当前活跃 task 的感知。诊断方法：`sqlite3 ${HERMES_HOME}/kanban.db "SELECT id, title, status, assignee, datetime(started_at,'unixepoch') FROM tasks WHERE status='running' AND started_at < strftime('%s','now','-2 hours');"`。对于每个在旧备份中遗留的 running task，检查其 round 的 handoff 文件和 `review_queue/` 产物确认当前完成状态。若 round 已通过 evaluator 审查或正式关闭，直接 `kanban_complete(task_id=...)` 清理。_R117 案例：DB 恢复后发现 R117 operator 仍在 running，但 handoff 文件确认 evaluator 已完成失败审查（FORMAL_CLOSE）。使用 `kanban_complete(task_id=t_bc0d96f7)` 清理。_

- **`.recover` 恢复后空表验证缺失（R140 教训）**：从 corrupted DB 执行 `.recover` 并 `PRAGMA integrity_check=ok` 后，不要直接使用。必须额外执行 `SELECT COUNT(*) FROM tasks` 确认实际表中有数据。`.recover` 可能只重建了 schema（tasks 为空表）而 integrity_check 仍报 "ok"。发现空表后，重试 `.recover`（换输出文件名）通常能成功恢复数据。同一 corrupted 源文件重复运行 `.recover` 有时也产生不同结果——第一次空表、第二次含数据。

- **选择性重建（pipeline 已推进时的优化）**：当备份恢复后管道已推进很多轮（如从 Jul 28 备份恢复，实际已到 R135），不要逐轮重建所有中间 evaluator task。用 handoff 文件确认每轮已完结状态：遍历 `docs/session_handoffs/` 找到最近一轮 evaluator 的总结 handoff → 确认该轮与备份中最旧缺失轮之间的所有 round 均已有 evaluator 结论（通过 handoff 文件名和 review_queue/ 产物确认）→ 只创建最新 pending 阶段的 task（如 R135 operator）。中间轮次的 evaluator task 虽然 kanban 中不存在，但已在文件系统中完成，不需要重建。这样做避免浪费计算资源和产生大量虚假 evaluator task。_R117→R135 案例：18 轮丢失，但所有中间轮均已通过 handoff 确认完成，只重建 R135 operator。_

- **Cron job repeat=1 陷阱**：创建看门狗 cron job 时，`repeat` 参数默认为 `1`（跑一次就退役），即使 schedule 设的是 `10m` 这样的重复周期。必须确认 `${HERMES_HOME}/cron/jobs.json` 中的 `repeat.times` 为 `null` 才等于无限循环。修复方式：`python3 -c "import json, os; d=json.load(open(os.path.expanduser('${HERMES_HOME}/cron/jobs.json'))); [j.update({'repeat':{'times':None,'completed':j.get('repeat',{}).get('completed',0)}}) for j in d['jobs'] if j['repeat'].get('times')==1]; json.dump(d, open(os.path.expanduser('${HERMES_HOME}/cron/jobs.json'),'w'), indent=2)"`。验证：`cronjob(action='list')` 中 `repeat` 字段应为 `forever`。
- **Cron pause 未持久化陷阱（R141 案例）**：调用 `cronjob(action='pause')` 后，`enabled` 可能看似变为 `false` 但下次调度周期又被自动恢复。诊断方法：pause 后立即调用 `cronjob(action='list')` 确认 `enabled=false` 且 `state=paused`；间隔几分钟后再检查一次确认持久化。若重新变为 `enabled=true`、`state=scheduled`，需要再次 pause。R141 案例：a-share-auto-pipeline 第一次 pause 未持久化，从 10:51 到 14:45 持续运行了近 4 小时。第二次 pause 成功。根因可能是 scheduler 重启或内部恢复机制。降低风险的方法：pause 后验证两次（立即 + 下一次调度窗口后）。
  **管道 job 自愈（2026-09-07 验证）**：a-share-auto-pipeline 自己仍被调度执行、且 `${HERMES_HOME}/cron/jobs.json` 中该 job 是 `enabled=true` + `state=scheduled` + `paused_at` 非空（同批 pause 的 pipeline-progress-reporter 已 `enabled=false` 持久化）时，说明该 job 的 pause 失败——管道 cron 可以在自身运行内直接自愈：① `cp jobs.json jobs.json.bak_$(date +%Y%m%d_%H%M%S)` 备份；② 用 python json 读写把该 job 置为 `enabled=false, state=paused`（保留 paused_at 字段）；③ `python3 -m json.tool jobs.json > /dev/null` 校验语法；④ 再读回确认两个管道 job 均为 paused。与"用户故意重新 enable"的区分：手动 re-enable 通常会清除 paused_at；`enabled=true` 与 paused_at 并存且 job 持续 firing 是 pause 失败的签名。
- **Pipeline cron 盲区：blocked dvcoder 不触发 evaluator 创建（R114 案例）**：当 dvcoder 因数据依赖（如 staff feather 缺失）等非 "review-required" 原因调用 `kanban_block()` 时，旧版 cron 规则依赖 "刚完成"模糊时间窗口和 block reason 关键词识别，会跳过 evaluator task 创建。R114 在 06:52 blocked，直到 13:27（6.5 小时后）evaluator 才被分派。**修复**（2026-07-28）：将 cron prompt 改为无条件扫描所有 blocked dvcoder task——只要该 round 无对应 evaluator task，就创建。阶段判断依据 task title（含 "语义空间探索" → 语义预审；含 "算子空间实现" → 算子复审），不依赖 block reason。同时增加中段 evaluator 已完成检测（SQLite 查重）避免重复创建。详见 `${HERMES_HOME}/cron/jobs.json` 中 a-share-auto-pipeline 的 prompt 字段。
- **基础设施阻塞的 dvcoder task 不应触发 evaluator 创建（R141 案例）**：当 dvcoder 的 blocked reason 为**基础设施故障**（如 "GPT 账号被封"、"token 过期"、"API 配额耗尽"、"所有子进程 exit code 1 持续崩溃"）时，不应创建 evaluator task。因为 dvcoder 没有产出任何语义设计或算子实现供审查——evaluator 拿到的是一个空任务，只会浪费 token 然后静默退出或被 pipeline 误判为 "审核通过跳过"。"无条件扫描所有 blocked dvcoder task" 的正确前提是：block 原因必须是语义探索或算子实现完成后的 review-required 交接。基础设施故障的 blocked task 应留在 board 上等待用户解决，pipeline 应跳过该 round 不做任何动作。判断方法：读取 task_events 中 kind='blocked' 的 payload.reason，若包含 "账号"、"token"、"API"、"封"、"配额"、"exit code 1"、"crash" 等基础设施关键词，则跳过 evaluator 创建。若 reason 以 "review-required" 开头或指向具体产物路径，则正常创建。_R141 案例：blocked reason="dvcoder GPT 账号今早被封，所有子进程 exit code 1 持续崩溃。等待账号恢复" → pipeline 正确跳过 evaluator 创建。_
- **dvcoder Codex token 过期导致子进程静默退出**：当 dvcoder 的 kanban 任务持续 crash（"pid not alive"、"protocol violation"），且 DB integrity check 通过、无并发现象 gateway 时，根因可能是 Codex session token 已过期。诊断：在用户终端运行 `hermes model -p dvcoder`（需要交互式终端，无法在子进程中执行）。典型场景：用户更换了 ChatGPT 账号但没有重新认证 Codex token。修复后测试：创建最小连通性 kanban task（priority=99，只输出一行确认文字）验证。Hermes cron 系统在检测到持续失败后会自动暂停该 job（`paused_at` 字段写入时间戳）。恢复 DB 后 cron 状态仍为 `paused`，管道不会自动恢复。
  诊断：恢复 DB 后必须检查 `cron/jobs.json` 中推进器 job 的 `state` 和 `paused_at`。
  修复：`hermes cron enable a-share-auto-pipeline` 或手动设置 `enabled=true`、`state=scheduled`、清除 `paused_at`。
  验证：确认 `next_run_at` 为合理的未来时间戳，或等待下次调度触发。
  经验：Jul 20 13:18 DB 损坏 → cron 暂停 → Jul 23 21:47 DB 恢复后才发现，期间 3.5 天管道完全静默。DB 恢复检查清单必须包含 cron 健康检查。
- **多分母确认失败陷阱**：当同一因子（相同分子定义）用两个不同的分母（如 totopinc 和 total_assets）都得到 0/3 的相同结论时，说明问题不在表达式/分母层面，而在分子/方向定义本身。此时应判定该语义方向为死胡同，正式关闭，不再继续调参。这是 R19→R20（nwc_accrual）的关键经验。
- **构建因子前不查因子库**：直接动手写代码，没有先检查 `${PROJECT_ROOT}/util/rawsigs/` 是否已有等价因子。常见错误：把 FCF/TotalAssets 当成新因子，但 `fcf`（OCF-CapEx）和 `cf2at`（OCF/TotalAssets）已在库中。
- **只换字段不换表达式结构**：当因子 2+ 轮迭代后信号强度停滞（如 RankICmean 0.009 vs 0.015），不要在同一个线性加法框架内继续枚举变量。详见 `references/03-factor-patterns/factor-idea-generation-pitfalls.md` 的「严重误区」章节。可用算子参考：`references/03-factor-patterns/util-non-rawsig-operators-catalog.md`
- **后台进程跑回测替代 delegate_task**：当回测任务超过 600 秒（delegate_task 超时上限）时，使用 `terminal(background=True, notify_on_complete=True)` 替代。命令格式：`cd <工作目录> && PYTHONPATH=${PROJECT_ROOT} /Users/dv/.local/bin/python3.11 <脚本.py>`。回测完成后通过 `process(action='log')` 读取完整输出。
- **方向重复陷阱**：当一个经济学方向已被 evaluator 正式关闭后（如 R17 经营杠杆 YoY 弹性被判定不通过），不要使用不同的算术表达式或代理变量重新探索同一经济学维度（如 R29 用 fixed_asset_intensity 代理重新尝试经营杠杆信号）。被关闭的是"经济学方向"而非"具体公式"。判断标准：新候选的经济学解释能否用被关闭方向的原始经济学名称概括。若可以，则为重复探索。例外：evaluator 在结论中明确标注"可换表达式重新尝试"。
- **factor_library 语义重叠盲区**：default 在方向校验时，failure_registry 和 review_queue 检查均不会捕获 factor_library 中已存在的语义相似因子（如 `profit2at_qmq` 是 ΔROA 的一个初始库条目）。必须加查 factor_library 步骤。当发现重叠时，方向不算关闭，但 task body 中必须注明差异说明，要求 dvcoder 采用不同的变量映射表达。_R82 案例：ΔROA 方向校验时发现 profit2at_qmq 已在库中但从未 pipeline 评估，仍创建任务但标注差异化要求。_
- **参数化 codex 家族重复陷阱 — lagqnum/参数变体不是新因子（R133 案例）**：当因子库中已存在一个支持参数化控制的 codex（如 `cf2income_codex` 通过 `__init__` 的 `lagqnum` 参数支持任意滞后），提出一个仅参数值不同（如 lagqnum=1 代替 lagqnum=0）的候选不是"新因子"，而是**参数扫描**。判定标准：(a) 现有 codex 的类定义是否已经支持该参数（检查 `__init__` 的形参列表）；(b) 候选的公式结构是否与现有 codex 完全一致（仅参数值不同）；(c) 经济学含义是否完全相同。满足全部三条则为参数化 codex 家族重复，应在语义预审阶段直接打回，不需要进算子空间验证各参数值版本的信号差异。这与 formula_hash 精确匹配查重不同——公式的原始字符串不包含参数值，hash 不会匹配，但方向是重复的。dvcoder 在语义设计阶段应主动检查：候选因子是否只是现有 codex 的一个不同参数化调用。_R133 案例：OCF Margin (cfo_ttm_lag1/totopinc_ttm_lag1) 与 cf2income_codex (lag=0) 公式结构一致，cf2income_codex 的 `__init__` 已支持 lagqnum 参数化，仅参数值差异 → 语义预审判定为 duplicate。_
- **evaluator_passed/ 候选项卡持续堆积陷阱**：R22（gross_profit_qoq_gap, IC=0.0337, IR=2.196）和 R23（cogs_pass_through_gap, IC=0.0260, IR=2.129）是最早的 3/3 达标因子，此后陆续有 gross_margin_stability、admin_expense_stickiness、admin_expense_rate_stability 等通过审查，至今仍无人审核。每次管道健康检查必须包含 evaluator_passed/ 目录的滞留天数检查。当最老候选滞留超过 3 天时，default 应在管道推进报告中主动标记滞留清单和天数，提醒用户注意候选项卡堆积——但 default 不负责替代人工终审，只能持续标记。**滞留天数计算方法：** 使用 `stat -f "%Sm" <dir>` 获取目录修改时间，与当前时间差计算天数。报告格式：`Jul 13 20:17 | cogs_pass_through_gap_codex (10d)`。超过 3 天的候选加 ⚠️ 前缀。多个候选按滞留时间降序排列，最老的排第一。

- **dvcoder 迭代预算耗尽陷阱**：dvcoder 每次 task 有 70 次迭代预算（max_turns 配置）。codex 构建 + 组件加载 + 多变体回测 + 留档生成很容易耗尽预算，导致 task 以 blocked(reason=Iteration budget exhausted) 结束，而非正常的 kanban_block(review-required)。此时 pipeline 无法触发下一阶段。典型表现：codex 文件 + data feather 已产出，但 backtest/ 和 result/ 为空。防范方法：(1) 优先跑单变体验证，确认可行后再扩展到多 variant 扫描；(2) 长回测 (>60s) 主动切换为 terminal(background=True) 模式，不消耗迭代预算；(3) 分步执行——先一次运行只做因子值生成并存 feather，再单独做回测运行；(4) 若已耗尽且有部分产物，pipeline default 清理 blocked task 并创建 retry（idempotency_key 追加 -v2）。最好根本避免耗尽。

- **管道连续关闭检测**：当连续 5+ 轮均被 evaluator 关闭（含 0/3 失败关闭或 duplicate 关闭），说明当前框架内可探索的单因子经济学方向可能已接近饱和。default 在每次管道推进时自动检查最近轮次连续关闭计数。若检测到连续 5+ 轮关闭，在推进报告中标注关闭轮次序列（格式：`R62→R63→R64→R65→R66→R67→R68（共7轮连续关闭）`）和连续关闭计数，并在创建下一轮 task body 中附加说明："这是系统运行以来最长的连续关闭序列。当前已探索方向覆盖：X/Y/Z 等 N+ 经济学维度。新增经济维度可能已有限。"这是注意事项信号，不是终止信号——管道永不停止，但应提醒用户方向空间是否已框架用尽。判断标准：① 连续 5+ 轮关闭 ② 不同经济学维度（非同一方向的重复调参尝试）③ 跨轮使用的评估方法一致。
- **同状态重复巡检报告轰炸（2026-09-07 案例）**：10 分钟周期的管道推进 cron 在"唯一活跃异常是同一基础设施阻塞（如 R141 GPT 账号被封）、状态数天未变"时，若每 tick 都输出完整巡检报告，会向用户重复投递几乎相同的报告——2026-09-07 在用户已 pause 管道（07:42）但 pause 未持久化的情况下，11:13→11:58 连续 5 个 tick 各投递一份内容雷同的 R141 阻塞报告。**规则**：cron 在输出完整报告前，先用 `session_search(query=..., sort='newest', limit=3)` 检查本 job 最近几次运行（session_id 前缀 `cron_<job_id>_`）是否已报告过同一状态；若 kanban 状态与上次报告时完全一致、且本轮未执行任何新动作（无 task 创建/清理/修复），应输出 `[SILENT]` 而非重复报告。只有出现真正的新事实（新 task、状态变化、执行了修复动作如 re-pause）才输出报告。诊断"重复轰炸"的辅助手法：`ls ${HERMES_HOME}/cron/output/` 或 session_search 查最近 cron session 的 assistant 内容比对。
- **evaluator 静默分派失败陷阱**：当创建 evaluator task 后，任务状态变为 `done` 但 `runs: []`（无运行记录）、`events: []`（无事件记录），说明 dispatcher 提交了任务但 worker profile 从未实际执行。这不是 crash（crash 会在 runs 中留下 `outcome: "crashed"` 记录），而是静默退出。诊断方法：创建 task 后立即 `kanban_show()` 检查 `runs` 数组是否为空。若为空且状态为 done，说明 worker 被 claim 后未产生输出就退出了。根因排查优先级：profile 模型连通性 → skill 加载失败 → kanban DB 部分损坏 → 并发 gateway 冲突。恢复方法：用新的 idempotency_key（如追加 -v2）重新创建 task 强制新分派。
  **注意区分快速正常完成**：若 `kanban_show()` 的结果中 `runs: [...]` 有运行记录（含 run_id、started_at、ended_at、summary）且 `outcome: "completed"`，说明 evaluator 正常执行且快速完成了审查——这是健康的管道行为，不是静默分派失败。_R67 经验：evaluator 失败审查跑完完整流程（读 handoff、查 RankIC 时序、查 failure_registry、写 entry）仅需约 40 秒，一次 `kanban_create` 返回即 `status: done` 是合理的。_
- **lsdf CSV 日度多空收益空值问题**：`baskettest_()`（`util/utilfun.py:379`）返回的日度多空收益（lsdf）中，大多数日期的 `longret/shortret` 为 NaN，仅第一期有值。原因是 `baskettest_` 的日度净值计算在调仓间隔期返回 NaN。**lsret 指标不受影响**——它是从 `sigret` 按日期-分组的均值计算（`groupby(['date','siggroup'])['futret'].mean()` → long-short → cumprod → 年化），与 lsdf CSV 无关。评估时以 `metrics.json` 中的 `lsret` 为准，lsdf.csv 仅作参考。
- **构造性指标 vs 基本面经济比率陷阱（R52 PPEM 教训）**：dvcoder 在"超越常规思维"探索中，容易构造出表面上通过单因子合规检查（单一除法、单一名称、无门控）但实际缺乏经济学支撑的指标。R52 的 PPEM（价格路径效率动量 = 净位移/路径总长度）通过了语义预审（边际通过），但算子空间验证 0/3——与标准动量 ret20 相关 0.963，无独立增量。判断标准：因子的经济含义是否能用一句自然的财务/经济语言描述，且无需引入"效率"、"质量"、"压力"等无固定会计定义的抽象概念。如果解释时需要使用"该变量度量了 X 层面的 Y 效应"这种构造性措辞，而非"该变量是 Z 财务比率的变化率/比值"这种描述性措辞，则可能是构造性指标。正确的"超越常规思维"方向示例：找两个不同财务变量间的非标准但自然的比值（如 ΔGP/ΔRevenue 而非 GP/Rev）、探索会计恒等式两边的关系（如 ΔAccruals = ΔNP - ΔCFO 的时序表现）、或者发现基础字段中未被开发的经济关系（如特定行业折旧政策产生的信号差异）。错误的示例：把两个已知因子做某种数学运算生成新变量、将价格/换手率数据做多层变换构造新指标。R52 验证确认：纯价格路径构造无法超越标准动量，与其构造新指标不如寻找新的经济维度。
- **会计关系混淆陷阱 — 将 totopinc 误称为 income**：在因子语义设计文档中，totopinc（营业收入）经常被写为 income，导致读者以为是净利润。会计准则中 income=综合收益≈净利润，totopinc 是 revenue（营收）。两者相差 4-5 层会计处理。**语义预审阶段必须确认因子公式中出现的每个字段的中英文名称与会计层级的对应关系。** 见 references/02-data-pipeline-and-neutralization/a-share-income-statement-formula-chain.md。
- **accounts_receivable 字段覆盖陷阱（R118 经验）**：`asset` 组的 `accountsreceivable`（WIND 统一报表口径）在当前数据库中仅覆盖 ~73 只股票（~8K 行），而同一经济对象的 `acctrcv` 字段（trade receivables，资产负债表基础字段）覆盖 ~5310 只股票（~900K 行）。**规则**：构建涉及应收账款的因子时，优先使用覆盖完整的 `acctrcv`（可通过 `asset` 组 rawsig 按 `signame='acctrcv'` 加载），而非 `accountsreceivable`。evaluator 在 operator 审查时遇到覆盖率异常低（~K 级别行而非 ~M 级别）的字段，应主动怀疑是否为同一经济对象的低覆盖替代字段标签，并要求 dvcoder 排查正确字段名。
- **价格动量因子未跳过近期 20 个交易日**：构造价格动量因子时，必须通过 `skip_days=20` 参数跳过计算日之前最近 ~20 个交易日的收盘价。t 时刻的动量值不应包含 t 到 t-19 的价格数据。正确实现：`price_path_efficiency_(price_pivot, skip_days=20, lookback_days=240)`（已内置在 `util/func.py` 中）或 `ret20_codex` 的 `Lpar=20`。常见错误：直接用 `close_t / close_{t-240} - 1` 计算累计收益，会包含短期反转效应污染信号。**注意：此规则仅适用于价格动量（price-based momentum）因子，不适用于基本面/估值因子（如 b2p、profit2p 等财务比率）。** 估值因子使用财务报表数据，不涉及日频价格窗口，不需要 skip_days。
- **增长率分母符号处理（abs denominator）**：当计算 gp、np、op 等可正可负的财务变量的增长率时，用 `abs(previous_value)` 取代原始值做分母，可以保留方向信息并大幅提升信号质量。原理：负值增长率分母会导致符号翻转（负值变小 → 增长率反而为正）。R22/R23 g(gp) 验证中，abs 分母将 IC 从 0.017 提升至 0.031（+82%）、IR 从 1.52 提升至 2.22（+46%）、lsret 从 5.4% 提升至 11.2%（+107%）。实施方法：`sigdata['gp_gro'] = (gp_t - gp_tm1) / abs(gp_tm1)`。注意事项：(a) abs 不适用于分母接近零的场景（此时应直接丢弃而非 abs），(b) 当 gp_tm1 全为正时 abs 等价于原始值，无副作用。
- **混合量纲陷阱 — change/level 比值**：`Δ(gp)/totopinc` 中分子是变化量（亿级），分母是总量（百亿级），量纲不同。比值被分母规模主导而非被分子的变化幅度主导。design review 时应标记"分子是变化量、分母是水平值"的风险。正确的做法是分母用同量纲（如 `Δgp/gp_{t-1}` 毛利增长率）或直接算毛利率的环比变化。
- **修订单因子规则时砍掉正例**：当放宽或修改单因子规则表述时，保留 FCF = OCF - CapEx、现金利润率 = OCF / NetProfit 作为正例。这些例子帮助读者区分"有经济学含义的因子"和"无含义的构造性指标"，删除它们会降低规则的判读清晰度。除非用户明确要求移除，否则保留。
- **检测 plateau 后换层**：当网格搜索所有变体的 IR 极差 < 0.02 时，当前表达层已到 plateau，不要再继续调参，应换信号源、换数据结构或做组合融合。
- **多因子组合多轮堆叠陷阱**：连续 3+ 轮在同一个 multi-component 结构上层层堆叠（加门控→加交互项→线性 blend→再改权重），而不先解决"这个因子是不是单因子"的根本问题。每轮应先做单因子合规检查：如果当前结构已经是多因子组合，不要继续往上堆结构，先做"归零"拆解。
- **共享函数不应放在领域专用命名空间文件中（R129 教训）**：`run_quick_backtest_`（通用回测函数）从 `util.incremental_roic_utils`（领域专用命名空间 — 以 incremental ROIC 命名的文件）导入，造成两个问题：(a) 阅读者需要理解为什么增量 ROIC 的工具文件提供了 backtest 函数；(b) 其他 codex 文件对该文件的 import 形成了跨因子的隐式耦合。**规则**：通用函数（回测、去极值、度量计算等）应放在 `func.py` 或独立命名的 `util/quick_backtest_utils.py` 中；领域专用命名空间文件只放该因子专属的辅助逻辑。即使导入路径长几行，也比在因子模块间建立隐式耦合好。R129 evaluator 审查中发现 earnings_stability_utils.py 从 util.incremental_roic_utils import run_quick_backtest_。
- **财务数据加载 group 不匹配**：`_pivot_atomic` 只支持 cf/capexp/rdexp/asset/debt/findebt/expense 组；`_pivot_cash_quality_atomic` 只支持 income/profit 组。混用报 ValueError。详见 references/02-data-pipeline-and-neutralization/financial-data-group-matrix.md。
- **回测在 delegate_task 中超时**：完整 16 年 A 股月频回测（加载+中性化+跑回测）每个因子需 60-120s，多因子组合数分钟。delegate_task 600s 后超时截断。解决：用 terminal(background=True, notify_on_complete=True) 替代 delegate_task 执行回测。
- **evaluator_passed/ 目录结构不一致陷阱**：候选因子从 review_queue 迁移到 evaluator_passed 时，backtest/ 和 data/ 子目录可能未被复制（round34/35, R60, R73, cf2fa, op2ev/gp2ev 均有此问题）。backtest 文件可能散落在根目录（如 gross_margin_stability 和 R60）、缺少 data/ 子目录（如 op2ev/gp2ev 的 feather 留在 review_queue 中）、或同时存在 review_queue 和 evaluator_passed 两份副本。审计或汇总因子时，不能只查 evaluator_passed/backtest/，必须回查 review_queue/ 原始目录。a-share-factor-review skill 已加入 `cp -r backtest/` 强制复制指令，新迁移的因子不会再出现此问题。
- **代码提前入库的强制追回规则**：当发现 dvcoder 将候选因子在未通过 evaluator 复核和人工终审的情况下直接写入 `util/rawsigs/` 时，必须**直接从 rawsigs/ 删除并迁移到 review_queue/**，而不是仅标注状态留存库中。R16 的三个候选文件（core_profit_retention_codex, nonrecurring_drag_ratio_codex, nonrecurring_burden2income_codex）即是违规写入后从 rawsigs/ 删除至 review_queue/ 的真实案例。追回说明文件同步移至 review_queue/ 下，不在 rawsigs/ 中保留任何痕迹。：dvcoder 完成任务后以 `kanban_block(reason="review-required")` 或 `kanban_complete()` 结束。下游 task 由 `default` 负责创建。dvcoder 调用 `kanban_create` 会跳过 default 的编排判断，导致调度逻辑分散在多个 profile 中无法统一追踪。这是 R17 semantic pre-review 阶段出现断档（evaluator 审完没人创建下一任务）的直接根因。详见 `${PROJECT_ROOT}/HERMES.md §5.1`。
- **idempotency_key 阶段名不匹配陷阱**：创建 evaluator task 时必须使用与 dvcoder 不同的 phase 名。dvcoder 语义探索用 `R{N}-semantic`，evaluator 语义预审用 `R{N}-eval-prelim`，dvcoder 算子实现用 `R{N}-operator`，evaluator 复审用 `R{N}-eval-review`，evaluator 失败审查用 `R{N}-eval-failure`。使用重复 phase 名（如把 evaluator 的 key 写成 `R80-semantic` 而非 `R80-eval-prelim`）会导致 `kanban_create(idempotency_key='R80-semantic', assignee='evaluator')` 返回已存在的 dvcoder task id，**不会创建新的 evaluator task**——整个 pipeline 会误以为 evaluator task 已存在而跳过。_R80 教训：idempotency_key 命名表不透明，default 容易在 pipeline 中混淆 dvcoder 和 evaluator 的 phase 名。_
- **中段 evaluator 已完成检测（mid-cycle evaluator completion）**：当 pipeline 发现 dvcoder blocked(review-required) 时，可能对应 evaluator 已在上个 tick 之间被调度并完成审查。直接创建新的 evaluator task 会产生不安全重复（取决于 idempotency_key 是否准确匹配）。正确检测方法：在创建 evaluator task 前，先通过 SQLite 确认是否存在对应轮次的 done 状态 evaluator task：
  ```sql
  SELECT id, status, completed_at FROM tasks
  WHERE title LIKE '%R{N} evaluator%' AND status='done'
  ORDER BY completed_at DESC LIMIT 1;
  ```
  若返回有记录且 `completed_at` 在最近 1 tick 内，说明 evaluator 已完成审查：应跳过 evaluator 创建，直接清理 dvcoder blocked task 并创建下一阶段 task。
- **kanban_list / kanban_show I/O 错误（恢复后 DB 常见问题 — 现有 workaround 已证实不可靠）**：已恢复的 kanban DB 在 `kanban_list(status='...')` 状态过滤查询时可能触发 `disk I/O error`。**但更严重：即使是 `kanban_list(limit=5)` 和 `kanban_show(task_id=...)` 也可能同时失败**——R129 管道推进 session 中两者均在 `PRAGMA integrity_check=ok` 的 DB 上返回 `disk I/O error`。这说明索引页损坏的遗留影响不局限于大查询，小查询也同样会触发。**可靠替代方案：直接使用 SQLite 查询，完全绕过 kanban API 工具。** 推荐查询模式：
  ```sql
  # 检查所有活跃 task
  sqlite3 ${HERMES_HOME}/kanban.db "
  SELECT id, title, status, assignee, datetime(created_at,'unixepoch')
  FROM tasks WHERE status IN ('ready','running','blocked')
  ORDER BY created_at DESC LIMIT 20;
  "
  
  # 检查特定 task 的 body
  sqlite3 ${HERMES_HOME}/kanban.db "
  SELECT substr(body,1,200) FROM tasks WHERE id = '<task_id>';
  "
  
  # 检查 task runs（审查结论）
  sqlite3 ${HERMES_HOME}/kanban.db "
  SELECT id, task_id, outcome, substr(summary,1,300) as summary
  FROM task_runs WHERE task_id = '<task_id>'
  ORDER BY started_at DESC LIMIT 3;
  "
  
  # 中段 evaluator 已完成检测
  sqlite3 ${HERMES_HOME}/kanban.db "
  SELECT id, status, datetime(completed_at,'unixepoch')
  FROM tasks WHERE title LIKE '%R{N} evaluator%' AND status='done'
  ORDER BY completed_at DESC LIMIT 1;
  "
  ```
  不要因 `kanban_list` 和 `kanban_show` 都失败就误判为 DB 全损——直接 SQLite 查询通常正常工作，且返回完整数据。
- **三层结构混淆**：经常出现两类混淆：
  1. **Layer 1 vs Layer 3 混淆**：`util/rawsigs/` 同时包含 Layer 1（原子信号组文件如 `income/income.py`）和 Layer 3（`*_codex.py` 因子文件），但两者的准入规则完全不同。Layer 1 文件是现有财务组结构，新增原子信号时在该组文件内加；Layer 3 的 `*_codex.py` 必须通过人工终审后才能放进去。候选期间的 codex 文件只能放 `review_queue/` 或 `evaluator_passed/`。
  2. **Layer 2 与第一层混淆**：新增共享函数时应该放 `func.py`（Layer 2），而不是在 `rawsigs/` 下创建新文件。`rawsigs/` 下只有各组的原子信号封装文件，不存在独立的 `func.py`。写成"在 rawsig 新增原子信号"是安全的（Layer 1），但写成"需要新增 rawsig"会被驳回——新增的是原子信号封装，不是新增 `rawsigs/` 目录。

# Verification checklist

这是 `evaluator` 的强制全链路清单，不允许跳步。

- [ ] 是否明确了三层落点
- [ ] 是否保持 `rawsig/rawsigs → func.py + util/非rawsig → *_codex.py`
- [ ] `*_codex.py` 是否符合标准结构
- [ ] 是否已生成因子值与 quick backtest
- [ ] `RankICmean > 0.015`（1.5%）— evaluator 作为参考线。**dvcoder 不得因未达标而跳过 evaluator。**
- [ ] `RankICIR > 1.5` — 同上，evaluator 参考线
- [ ] `lsret > 4%` — 同上，evaluator 参考线
- [ ] 初测不通过时是否按“调参 → 换方向 → 删除”执行
- [ ] 初步通过的候选是否放在 `${PROJECT_ROOT}/factor_replicate_outputs/review_queue/<facname_codex>/`
- [ ] 是否已明确告知 `evaluator` 复核路径
- [ ] `summary.md` 是否只承担短摘要 + 文件索引，而未内嵌 `formula.md` / `hypothesis.md` / `run_manifest.json` 正文
- [ ] 是否已生成 `formula.md`、`hypothesis.md`、`run_manifest.json`、`dvcoder_handoff.md`
- [ ] `evaluator` 复核通过后，是否已明确告诉用户同一候选路径
- [ ] 若人工终审不通过，是否默认回到 `dvcoder` 且以上一轮 `evaluator_passed` 为种子
- [ ] 未经人工审查通过，是否没有写入 `${PROJECT_ROOT}/util/rawsigs`
- [ ] **因子是否有明确的经济学含义** — evaluator 必须主动提问，不能用"代码跑通了"替代经济学解释
- [ ] **因子是否是单因子，不是多因子组合** — evaluator 必须确认因子能用单一经济学名称概括，不包含多组独立经济含义的叠加。如果发现类似 zscore(A)+zscore(B)-penalty(C) 的构造或任何无单一经济学含义的复合结构，必须退回
- [ ] **因子是否基于历史数据调整的比率** — evaluator 必须确认因子不是用历史最优回溯出来的参数/比率/门控/奖励。如果发现门控或奖励，必须要求明确的经济学理由，否则退回

只要 `evaluator` 发现任一步缺失、跳步、证据断裂或路径不清，就必须打回到跳步之前的那一步重做，不能越过缺口继续放行。

