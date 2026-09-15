# R19–R20 nwc_accrual 方向死胡同确认

## 轮次序列

| 轮次 | 表达式 | 结果 | 关键诊断 |
|------|--------|------|---------|
| R19 | Δ(acctrcv+inventories+prepay-acctpayable) / totopinc | 0/3 | ICmean=0.0023, IR=0.17, lsret=0.7% |
| R20 | Δ(acctrcv+inventories+prepay-acctpayable) / total_assets | 0/3 | ICmean=0.0024, IR=0.18, lsret=1.8% |

## 核心方法论教训

**多分母确认失败 = 分子/方向层面的问题，不是表达层面的问题。**

totopinc 和 total_assets 是差异极大的两个分母（前者是收入口径，后者是存量规模口径）。如果两者都给出相同的 0/3 结论，说明问题不在分母选择上，而在分子定义本身——Δ(acctrcv+inventories+prepay-acctpayable) 这个营运资本增量表达式在 2020 年后的 A 股已经失去了横截面区分力。

## 关键信号

- Pre-2020 IC 累计: +0.64（有信号，均值 0.0057）
- Post-2020 IC 累计: -0.20（转负，均值 -0.0030）
- 分母切换仅改善 ICmean +0.0001 — 可忽略

## 结论

正式判定"营运资本应计率（nwc_accrual）"为死胡同方向，推荐下一方向：Incremental ROIC（ΔROIC）。

## 参考

- evaluator R19 审查结论: `t_bb3da1f5`
- evaluator R20 审查结论: `t_1964aa50`
- 相关 handoff: `${PROJECT_ROOT}/docs/session_handoffs/2026-07-09_t_bb3da1f5_evaluator_nwc_accrual_round19.md`
- 相关 handoff: `${PROJECT_ROOT}/docs/session_handoffs/2026-07-09_t_1964aa50_evaluator_nwc_accrual_ta_round20.md`
