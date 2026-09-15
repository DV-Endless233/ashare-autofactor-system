# 因子库重复审计方法（严口径 2026-09-07 沉淀）

> 背景：老师发现 evaluator_passed 清单中 amihud_dxy_10 与 `util/rawsigs/amihud_dxy/amihud.py` 重复、
> SUE 与 `sueall/sueall.py` 重复后，对 36 个候选做了全量审计。本文沉淀「如何对一个候选或一批候选做因子库查重/审计」的操作方法，
> 供 dvcoder 语义阶段、evaluator 预审以及未来人工终审前的大批量复核使用。**边界口径：参数实例 = 重复（用户/老师 2026-09-07 确认）**。

## 1. 基准数据源（按序核对）

1. `factor_library.db` —— **权威文件在 `${PROJECT_ROOT}/database/factor_library.db`**。
   ⚠️ `${PROJECT_ROOT}/factor_library.db` 与 `${PROJECT_ROOT}/util/factor_library.db` 可能是 **0 字节占位**，别读错。
   表 `factor_library` 列：factor_name / economic_meaning / math_formula / formula_hash / metadata_json / rankic / … / entry_channel。
2. `util/rawsigs/<dir>/<main>.py` —— 代码级证据，**判定重复的最终依据**。
3. `docs/factor_library_catalog.md` —— 164 条 auto-extracted 含义；**很多 textbook 文件含义是 "Created on …" 垃圾**，只能辅助不能依赖。
4. `util/factor_library_registry.json`（自动生成）+ 重建脚本 `util/build_factor_registry.py`。
5. `rawsigs_list.xlsx` —— 只是**导入列技术清单**（原始数据列名），不是语义索引，别当含义表用。

hermes venv python（`${HERMES_HOME}/hermes-agent/venv/bin/python`）自带 openpyxl + pandas，可直接读 xlsx。

## 2. 审计步骤

1. 读候选清单（xlsx 或 handoff），逐行取 Round / 因子名 / 经济学含义 / 公式（公式列 `{}` 表示下标）。
2. 先做**名字 token 匹配**（快筛，但**不足够**：`cfo_yield_level` 与 `cf2p` 无公共 token；`SUE` 与 `sueall` token 也不重叠）。
3. 对命中的库内目录 + 所有同族候选目录，读其主 py：
   - `def __init__(self, ...)` 的**参数默认值**（lookback/window/lagqnum/signamex/signamey…）
   - 注释里的参数域声明（`signamex in np nptopc gp op ...`）
   - `super().__init__('xxx_' + param)` —— **参数化命名铁证**（amihud_dxy_<N> 即此类）
4. 判定层级：①公式/口径一致 ②单调等价（倒/差/负/缩放/镜像）③参数实例（落在既有家族声明参数域内，即使因子值未物化）④同经济含义。
5. 输出分层：A 确定重复 / B 参数实例 / C 内部重复或镜像 / D 家族相邻-需老师定口径 / E 新因子。
   严口径处置：A+B+C 剔除；D 保留但标注待口径；E 保留。

## 3. 已知参数化家族与实例（2026-09-07 代码证据）

| 库内家族 | 参数域 | 被重复的实例判例 |
|---|---|---|
| `amihud_dxy` | `lookbacktdays`（默认 60，`amihud_dxy_<N>` 命名） | R125 amihud_dxy_10 |
| `x2p` / `profit2p` | signamex∈{np,nptopc,nptopcad,gp,op,ebit,ebitda,totp,nptopcall_*}；y∈{totcap,floatcap,freefloatcap,avg*}_1Q | R96 op_yield、R97 ebit_yield、R98 np_yield、R99 gp_yield、R100 pretax_yield |
| `cf2p` | signamex='cfo'，cap 分母 | R94 cfo_yield_level |
| `d2p` | facnameuse dividend_ttm/dividend_lyr → mktcap | R93 dividend_yield_level（R85 曾自识别关闭，R93 复发） |
| `profit2ev` | signamex∈profit 域，y='ev' | R71 OP/EV、GP/EV；R73 EBITDA/EV |
| `profit2income` | signamex∈profit 域，y='totopinc' | R88 gross_profit_margin_level（gp/totopinc） |
| `gp_growth_qoq_codex` | lagqnum_now/base（毛利TTM增长率） | R22 gp_growth_qoq（lag4q 变体） |
| `retskew60_codex` | window=60（默认），rolling skew | R103 return_skewness |
| `turnover` | freeturnover/turnover 原始信号 | R122 -mean20(freeturnover)（取负+平滑=单调等价） |
| `sueall` / `surall` / `suprofit` / `sud_generic_codex` | 意外盈利族（ΔNP−mean)/std 或 DeltaYoY 标准化 | R107 SUE |
| `b2p` | 默认 signamex='eqtopc', signamey='totcap' | R110 B2P（参数一字不差） |
| `stdff3resid` | FF3 残差 vol（对比 CAPM 残差 ivol 属 D 类） | R128 ivol（需口径） |

## 4. 关键 Pitfalls

- **factor_library.db 的 `math_formula` 对 initial_inventory 条目存的是 `class extends: Name(...)` 代码签名片段，不是数学公式**
  → `formula_hash`（md5 规范化公式+metadata）对"用数学表达式重写/参数化实例"的候选**永远不会命中**。哈希只防精确复跑。
- 旧版 skill 的「公式、口径、回测区间三维一致才是真重复」定义过窄，且与「单调等价也算」自相矛盾 → 2026-09-07 已废，改为四层强制查重。
- **候选批次内部也可能互相重复**：R22 cogs_pass_through_gap 与 gross_profit_qoq_gap 公式逐字相同；R137(Δ4Q)/R138(Δ2Q) 是同族窗口变体 —— 审计时也要查批次内部。
- 语义预审 handoff **必须附查重报告**（比对了哪些家族/参数域/证据路径），缺失时 evaluator 不得 PASS（防 R93 类复发：查重结论未持久阻断后续轮次）。
- 关闭方向写 failure_registry.db 时登记**家族/参数域指纹**，default 建新轮前复查。
