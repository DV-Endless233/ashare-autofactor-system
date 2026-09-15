# pairfactorclass_ 模式目录

## 概述

`pairfactorclass_` 是 `util/pairfactorclass.py` 中的共享因子构造类，支持多种预定义 `pattern`（模式），每个模式定义一种特定的因子构造公式。用于 `*_codex.py` 叶子层，通过参数化配置即可生成因子值，无需手写 `sigconstructperiods_`。

## 基本用法

```python
from util.pairfactorclass import pairfactorclass_

class my_factor_codex_sig_(pairfactorclass_):
    def __init__(self, ...):
        super().__init__(
            facnameuse='my_factor_codex',
            pattern='delta_ratio',          # ← 选一个模式
            agroup='profit',                 # 第一变量组
            signamea='gp',                   # 第一变量名
            fiscaltypea='ttm',               # 第一变量财务口径
            bgroup='income',                 # 第二变量组
            signameb='totopinc',             # 第二变量名
            fiscaltypeb='ttm',               # 第二变量财务口径
            lagqnuma=0,                      # 第一变量滞后期
            lagqnumb=0,                      # 第二变量滞后期
            lagqnum1=0,                      # 第三参数（模式相关）
            lagqnum2=1,                      # 第四参数（模式相关）
        )
```

## 可用模式

### `divide` — 简单比值

**公式**: `a / b`

| 参数 | 含义 |
|------|------|
| lagqnuma | 第一变量滞后期 |
| lagqnumb | 第二变量滞后期 |

**示例**: 营业利润率 `op / totopinc`

### `delta` — 变化量

**公式**: `a_t - a_{t-1}`（单变量自身环比变化）

| 参数 | 含义 |
|------|------|
| agroup / signamea | 被求差变量 |
| bgroup / signameb | 不使用（设为同一变量） |

### `delta_ratio` — 变化量比值

**公式**: `(a_t - a_{t-1}) / b_t`

第一变量的变化量除以第二变量的水平值。分子是变化量，分母是水平值，注意混合量纲问题。

| 参数 | 含义 |
|------|------|
| lagqnum1 | a 的滞后期（用于计算变化量） |
| lagqnum2 | a 的基准滞后期（通常=1） |

**示例**: R22 `gross_profit_qoq_gap` = `(gp_ttm_t - gp_ttm_{t-1}) / totopinc_ttm`

⚠️ **混合量纲陷阱**: 分子是变化量（亿级），分母是总量（百亿级）。比值很小且横截面差异被规模主导。优先考虑改为 `self_gro`（同量纲）或毛利率本身的环比变化。

### `gro` — 增长率（单变量）

**公式**: `g(a) = a_t / a_{t-1} - 1`

| 参数 | 含义 |
|------|------|
| lagqnum1 | 当期lag |
| lagqnum2 | 基准lag |

**示例**: 营收增长率 `g(totopinc_sq)`，毛利率增长率 `g(gp_ttm)`

### `gro_gap` — 增长率差（双变量）

**公式**: `g(a) - g(b)`

第一变量的增长率减去第二变量的增长率。衡量两个变量的增长差距。

| 参数 | 含义 |
|------|------|
| growth_legs_a | 用于 a 的增长率计算腿 |
| growth_legs_b | 用于 b 的增长率计算腿 |

**示例**: R23 `cogs_pass_through_gap` = `g(totopinc_sq) - g(totopcost_sq)`

会计含义：收入增长快于成本增长 = 毛利率扩张。经济学含义：成本传导能力。

### `self_gro` — 自身增长率

**公式**: `(a_t - a_{t-1}) / a_{t-1}`

同 `gro`，但用不同参数接口实现。用于计算单变量自身的百分比变化，量纲一致。

**示例**: 毛利增长率 `g(gp_ttm) = (gp_t - gp_{t-1}) / gp_{t-1}`

### 其他模式（需查阅代码确认）

pairfactorclass_ 还支持以下模式，但本文编写时具体参数需求未完整记录：

- `growth` — 增长类模式
- `delta_gap` — 变化量差
- `ratio_gap` — 比值差

> 使用未在本文列出的模式时，建议先测试 `__init__` 参数能不能跑通 `getfac_()`，再写完整 codex。

## 模式选择指南

| 你要表达什么 | 选什么模式 | 示例 |
|-------------|-----------|------|
| 一个比率（A/B） | `divide` | 营业利润率 op/totopinc |
| 一个变量的自身增长率 | `self_gro` 或 `gro` | 毛利增长率 g(gp) |
| 利润表变量的增长率差 | `gro_gap` | g(rev)-g(cost) |
| 变化量/水平值的比值 | `delta_ratio` | Δgp/totopinc（⚠️ 混合量纲） |
| 利润表变量的逐期变化量 | `delta` | Δgp = gp_t - gp_{t-1} |

## 已知模式的实际轮次参考

| 模式 | 轮次/因子 | 公式 | 数据组 | 结果 |
|------|----------|------|-------|------|
| `delta_ratio` | R22 gross_profit_qoq_gap | Δ(gp_ttm)/totopinc_ttm | profit/income | IC=0.0337, IR=2.196 |
| `gro_gap` | R23 cogs_pass_through_gap | g(totopinc_sq)-g(totopcost_sq) | income/cost | IC=0.026, IR=2.129 |
| `gro_gap` | R23 quasi_fixed_cost_dilution | g(totopinc)-g(adminexp+rdexp) | income/expense | 数据覆盖失败 |
