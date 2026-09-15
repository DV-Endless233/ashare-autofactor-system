# Self-Funded Reinvestment Quality Factor Family

## 分类

属于 **growth 大类 × 成长质量子类**，而非纯增速或纯规模因子。核心关注的是增长的资金来源结构，而非增长率本身。

## 经济学含义

- 内含假设：由经营现金流支撑的再投资（capex + R&D）比靠外部融资硬撑的再投资更可持续
- 有效场景：企业需要持续投入资本以维持增长的行业（制造、科技、医药）
- 失效场景：金融行业（负债结构本身就是业务）、强周期底部所有公司杠杆同时升高

## 核心公式骨架

```
reinvest_int = (capexp + beta * rdexp) / totasset
cash_support = cfo / totasset
fin_depend   = <融资依赖代理变量>

factor = z(unexpected(reinvest_int)) + z(unexpected(cash_support)) - z(unexpected(fin_depend))
```

## 融资依赖惩罚的表达演进

这是该因子族的主要进化轴。

### V1: 粗融资代理

- `fin_depend_cff = max(cff, 0) / totasset`
- 问题：cff 是净融资现金流，混入偿还旧债/分红/再融资，语义不纯

### V2: 慢变量替代

- `fin_depend_debt = totdebt / totasset`
- 效果：稳定性提升（IR 从 0.24 → 0.49），但慢变量对边际变化不敏感
- 最佳变体 `self_funded_reinvestment_quality_debt_penalty_codex` IR=0.49

### V3: 边际压力替代（第二轮结果）

| 变体 | 惩罚表达 | RankICmean | RankICIR | vs V2 改善 |
|---|---|---|---|---|
| finexp_penalty 🏆 | finexp / totasset | **0.00923** | **0.668** | +42% / +35% |
| short_findebt_penalty | 短期有息负债 / totasset | **0.00779** | **0.611** | +20% / +24% |
| findebt_penalty | 有息负债 / totasset | 0.00547 | 0.446 | -16% / -10% |

结论：从 totdebt → finexp 方向正确（+42%），但线性加法框架本身限制了信号强度。空头区分改善（G1 从 +0.77% → -2.0%），但远未达到 0.03/1.5/15% 的硬门槛。

### V5: 条件门控结构（第五轮结果）

在 V4 行业排序胜出的基础上，不再使用连续乘子，改为 **piecewise / threshold / capped / fusion** 条件化门控：

| 变体 | 结构 | 核心逻辑 |
|---|---|---|
| **fusion_rf_gap 🏆** | OR 门控：低融资压力 **或** gap改善 | 两条通路任一条成立就解锁加分 |
| regime_rf | 简单开关：I(低融资压力) | 低融资压力区间才给再投资奖励 |
| threshold_rf | 阈值起算：pos(pos(-fin_z)-0.5) | 超过50%分位才计分 |
| capped_rf | 截断：min(pos(reinvest_z×gate), 1.5) | 控制极端值躁动 |

**结果**：IR 从 0.97 → 1.26（+30%），lsret 从 0.044 → 0.059（+34%）

关键框架变化：
```python
# V4 连续乘子
core = cash_z + zscore(reinvest_z * pos(-fin_indrank_z)) - fin_indrank_z

# V5 OR 门控（fusion 最优）
core = cash_z + zscore(reinvest_z * I(低融资压力 || gap改善)) - pos(fin_indrank_z)
```

### V6: 有限网格验证（第六轮结果）

在 V5 基础上做 3 参数 × 3 格点 × 2 结构 = 54 个变体 + 4 对照：

| 参数 | 格点 |
|---|---|
| fin_threshold (低融资压力门槛) | 0.0 / 0.25 / 0.5 |
| gap_threshold (自现金流改善门槛) | 0.0 / 0.25 / 0.5 |
| gate_cap (奖励封顶) | 1.0 / 1.5 / 2.0 |

**结论：网格是 plateau 而非山峰。** 所有 OR 变体 IR 在 1.246-1.258 之间，极差 < 0.013。参数调优几乎不产生增益。

| 维度 | 关键发现 |
|---|---|
| OR vs AND | OR (1.25) 全面优于 AND (1.19-1.23) |
| 参数敏感性 | IR 极差 < 0.013，plt plateau |
| ICmean | 卡在 0.012，连续 2 轮无跃升 |
| red flag | 全为 false |

**当前表达层到 plateau，需要换层。**

## 已知非线性门控家族的分类

按复杂度和迭代顺序排列：

| 类型 | 操作 | 示例 | 效果 |
|---|---|---|---|
| 连续门控 (R4) | gated × 连续乘子 | reinvest × pos(-fin_z) | IR=0.97, lsret=0.044 |
| 惩罚门控 (R4) | 只惩罚尾部分位 | pos(fin_z - 0.8) | IR=0.97, lsret=0.044 |
| 交互项 (R4) | Z(a)×Z(b) 协同 | Z(reinvest)×Z(cash) | IR=0.94, lsret=0.050 |
| 条件门控 (R5) | I(条件) 开关 | I(fin<0.25) | IR=1.19, lsret=0.057 |
| 融合门控 (R5) | OR 双条件 | I(条件A\|\|条件B) | IR=1.26, lsret=0.059 |
| AND 门控 (R6) | AND 交集 | I(条件A && 条件B) | IR=1.23, lsret=0.061 |
| 截断门控 (R5) | capped 上限 | min(gate, 1.5) | IR=1.19, lsret=0.057 |

### V5 候选方向（第三轮：表达方式升级）

V1→V3 一直在做「换字段」级别的修改，组合结构始终是线性加法：
```
Z(reinvest) + Z(cash_support) - Z(penalty)
```
第三轮不再仅限于换字段，而是引入不同的**表达方式和组合结构**，利用 util/ 非 rawsig 空间中之前未使用的算子（详见 `references/03-factor-patterns/util-non-rawsig-operators-catalog.md`）：

D1: 边际融资压力法 — `delta_(finexp/asset, 4Q)` 替代 level
D2: 投资-融资比值法 — `reinvest_int / (finexp/asset)` 或 `cfo / finexp`
D3: 增速惩罚法 — `yearonyeargrowth(finexp/asset)` 或 `gro_xmy_periodssig_`
D4: 行业内排序法 — `get_sigindrank_(finexp/asset)` 替代原始值
D5: 正交组合 — `SymOrth_(delta + YoY)` 多维度惩罚去冗余

## 实现注意事项

- `rdexp` 在 A 股覆盖 ~46%，缺失补 0 会混淆"未披露"与"真实为 0"
- 共享函数应放在 `util/` 非 rawsig 区域，而非 `review_queue/<facname>/` 目录（当前初版可容忍，正式入库前必须迁移）
- `stkfactor` 的 `WindTradingDay_(IfMonthFirst=True)` 确保月频调仓日期正确
- 中性化统一用 `lntotcap_ind_neut_(Ifsize=True, Ifind=True)`

## 与现有 growth 因子的正交性

| 因子方向 | 差异点 |
|---|---|
| profit_acceleration / compound / robust | 本因子不关心利润增速多快，关心增长的钱从哪来 |
| cf_acceleration / cf_pctrank | 本因子不只关注现金流水平或变化，还叠加了投资端和融资端的结构 |
| rdexp / rdexp2at / capexp（静态比率） | 本因子是动态时序变化 + 三表联动，而非截面杠杆比 |
| growth_generic_qmq | 本因子不依赖 QoQ 增长率，而是 unexpected 分解 + 净差结构 |

## 已知风险

- 三个子项做 z-score 再相加，默认等权，未做动态权重
- `cff` 为净融资流，正负分别表示净融入/净偿还，max(cff,0) 会丢失偿还信息
- `unexpected` 分解用 rolling mean/std 而非 ARIMA，可能残留季节性和趋势漂移
