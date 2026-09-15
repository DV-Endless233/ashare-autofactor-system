# 因子库缺口清单

本文件记录 `${PROJECT_ROOT}/util/rawsigs/` 中**不存在**的因子经济学维度，供 dvcoder 和 evaluator 确认新因子的新颖性。

> 使用方式：在进入语义空间前先读本文件，避免构建已有因子或过于常识性的因子。
> 当找到真正的新因子后，在本文件中添加记录并标注"已覆盖"。

## 因子库已有方向（不要重复）

| 类别 | 已有因子 | 核心公式 |
|------|----------|----------|
| 现金流比率 | cf2at, cf2debt, cf2income, cf2profit, cf2p, cf2ev, fcf, fcff2ev | OCF/Asset, OCF/Debt, FCF, FCF/EV |
| 盈利比率 | profit2at, profit2eq, profit2ev, profit2income, profit2p | Profit/Asset, Profit/Equity |
| 增长类 | profit_acceleration/compound/robust/unexpected/yoysig, cf_acceleration/pctrank | 利润/现金流增长变体 |
| 债务类 | debt, findebt, berbagai leverage | Debt/Asset, Debt/Equity |
| 质量/应计 | noa, quality_gap_family_codex, cfo_sq_op_sq2totasset | 净经营资产、应计利润 |
| 研发 | rdexp, rdexp2at, rdexp2p | 研发支出/资产/利润 |
| 股息 | dividend, dividend2income, dividend2profit | 股息/利润 |
| 资本支出 | capexp | 资本支出绝对额 |
| 其他 | turnover, momentum, amihud, sue, surall, betabarra | 换手、动量、流动性 |
| 会计稳定性 | gross_margin_stability_std12q, admin_expense_stickiness, admin_expense_rate_stability_std12q | 费用/利润率的时间序列稳定性 |

## 已探索并关闭的方向（不要在相同经济学方向上重复投入）

以下方向已在 pipeline 中被 evaluator 正式关闭或标记为重复。新的候选因子如果与以下任一方向的原始经济学名称一致，即视为重复。

| 方向 | 经济学含义 | 探索轮次 | 结论 | 关闭原因 |
|------|-----------|---------|------|---------|
| 有效税率 / 税负 | ETR, (TotProfit - NP)/TotProfit, tax gap | R18, R30, R36, R41 | ❌ 关闭 | 利润表所得税字段受 ROA 主导，无独立增量信号 |
| 增量 ROIC | ΔOperatingProfit / Δ(FixedCapital + WC) | R21, R45, R50, R58 | ❌ 关闭 | 多轮累计 0/9+，A 股横截面预测力不足，增量信息被盈利比率吸收 |
| 经营杠杆 (DOL) | ΔOP/ΔRev, fixed_asset_intensity | R17, R29, R46 | ❌ 关闭 | 三方向四轮累计 0/9：弹性/强度/回撤严重性均 0/3 |
| 劳动效率 | Revenue / Employee, OP / Employee | R28, R42 | ❌ 关闭 | 4 seed 全部裁决；seed2/3 条件通过但因 staff 数据缺失阻塞，方向已关闭 |
| 应计利润质量 | (NP - CFO)/Assets, (ΔAR - ΔAP)/Revenue | R19, R20, R37, R42, R65 | ❌ 关闭 | R42 cash_confirmed_earnings + R65 total_accruals 属同一方向双种子 0/3 |
| 财务杠杆水平 | TotalLiabilities/Equity, Interest-Bearing Debt/Equity | R66, R67 | ❌ 关闭 | IC~0.002 t-stat=0.617，信号被近邻杠杆因子（asset2eq, dtoabarra, blevbarra）吸收 |
| 研发强度 | R&D Expense / Total Assets | R68 | ❌ 关闭 | 与现有 rdexp2at 完全重复（exact formula match） |
| 资本配置(总量) | Sales/CapEx, CapEx/Depreciation, Cash Reinvestment Ratio | R38, R39, R40, R63, R64 | ❌ 关闭 | CapEx 方向 5 种子全部 0/3，整个"固定资本配置"语义族为失效信号 |
| 动量构造 | PPEM (价格路径效率), price-related 构造指标 | R52 | ❌ 关闭 | 与标准 ret20 动量相关度 0.963，无独立增量 |
| Revenue Quality | ΔAR/ΔRevenue, receivables quality | R54, R56 | ❌ 关闭 | 结构性数据链断裂（ΔAR/ΔRev 97% 数据丢失）；cash_coverage_repair_mom 0/3 |
| 资产增长率 | Δ4Q(TotalAssets) / TotalAssets_lag4Q | R57 | ❌ 关闭 | 经典美国资产增长异常在 A 股横截面预测力不足 |
| 资产周转率变化 | Δ4Q(Rev_TTM / TotalAssets) | R54 | ❌ 关闭 | 总资产含大量非经营资产稀释信号；2020 年后 IC 全面退化 |
|  Expense Stability | selling_expense_rate_stability_std12q | R62 | ❌ 关闭 | 全样本 0/3，近窗 2/3 但 lsret 仅 1.8-2.5%，fillna(0) 产生伪稳定信号 |
| 利息覆盖倍数 | OP_TTM / FinancialExpense_TTM | R51, R53, R55 | ❌ 关闭 | 2/3 平台（IC~0.025, IR~1.25），8 变体均未提升到 3/3；2021 年后 IC 持续走弱 |

## 通过审查的候选因子（已通过 evaluator 复审，待人工终审）

以下因子已通过 evaluator 全链路复审，转入 `evaluator_passed/`，等待用户人工终审批准后才可写入 `util/rawsigs/`。

| 候选因子 | 通过轮次 | ICmean | IR | lsret | 滞留天数 |
|---------|---------|-------|---|-------|---------|
| gross_profit_qoq_gap | R22 | 0.0337 | 2.196 | 0.112 | 10d ⚠️ |
| cogs_pass_through_gap | R23 | 0.0260 | 2.129 | 0.098 | 10d ⚠️ |
| gp_growth_qoq | R22/R23 | — | — | — | 10d ⚠️ |
| retention_plowback_change | R34 | — | — | — | 9d ⚠️ |
| retained_profit_asset_intensity_change | R35 | — | — | — | 9d ⚠️ |
| gross_margin_stability_std12q | R59 | — | — | — | 3d |
| admin_expense_stickiness | R60 | — | — | — | 3d |
| admin_expense_rate_stability_std12q | R61 | — | — | — | 3d |

滞留天数超过 3 天的标记 ⚠️。人工终审应优先审查最老的候选。

## 空缺方向（尚未确认是否被探索）

| 方向 | 状态 | 备注 |
|------|------|------|
| 现金转换周期 (CCC) | ✅ 已有简单实现 | Round 4 基础实现，需回归验证 |
| 现金流稳定性 (Cash Flow Stability) | 🟡 R69 语义进行中 | σ_roll12Q(OCF_TTM / TotAsset_BS)；与 cf2at (水平) 正交，二阶稳定性信号；2026-07-23 创建 R69 语义预审 |

## 已确认饱和的经济学框架

截至 R69，以下经济维度族已在单因子框架内被充分验证，不建议在同一框架内继续探索：
- **定价乘数类**：账面/市值比、盈利收益率等已在 factor_library 中（b2p, profit2p, cf2p, ev-based）
- **盈利水平类**：ROA, ROE, 净利率、毛利率等已有稳定实现
- **资本结构类**：杠杆比率（资产负债率/产权比率/利息覆盖）已被穷尽
- **费用稳定性类**：毛利率/管理/销售三项费用稳定性均已验证（R59→R62）
- **增长类**：利润/现金流增长率变体已在 factor_library 中覆盖
- **应计类**：营运资本应计/总应计均被关闭

若用户希望继续在现有框架下挖掘新因子，建议方向：(a) 引入非财务数据源（供应链、舆情、专利）；(b) 改变方法论（多因子组合、条件 alpha）；(c) 换频率（周频/日频）。

## 填坑记录

| 日期 | 方向 | 状态 | 轮次 | 结果 |
|------|------|------|------|------|
| 2026-07-06 | CCC (现金转换周期) | 进行中 | Round 4 | 待回归验证 |
| 2026-07-14 | 盈利稳定性 (Gross Margin Stability) | ✅ 通过 | R59 | evaluator_passed/ |
| 2026-07-20 | Admin Expense Stickiness | ✅ 通过 | R60 | evaluator_passed/ |
| 2026-07-20 | Admin Expense Rate Stability | ✅ 通过 | R61 | evaluator_passed/ |
| 2026-07-20 | Revenue Quality | ❌ 关闭 | R56 | 数据链断裂 |
| 2026-07-20 | Asset Growth | ❌ 关闭 | R57 | 经典异常在 A 股不成立 |
| 2026-07-20 | 财务杠杆水平 | ❌ 关闭 | R66-R67 | IC~0.002 |
| 2026-07-20 | 资本配置(CapEx/Deprec + Cash Reinvestment) | ❌ 关闭 | R63, R64 | 0/3 |
| 2026-07-20 | 利息覆盖倍数 | ❌ 关闭 | R51, R55 | 2/3 平台 |
| 2026-07-20 | Selling Expense Stability | ❌ 关闭 | R62 | 0/3, fillna(0) 伪信号 |
| 2026-07-20 | Total Accruals (R65) | ❌ 关闭 | R65 | 与 R42 同方向 |
| 2026-07-20 | 研发强度 (R&D Intensity) | ❌ 关闭 | R68 | 与 rdexp2at 重复 |
| 2026-07-23 | 现金流稳定性 (Cash Flow Stability) | 🟡 进行中 | R69 | 语义预审阶段 |
