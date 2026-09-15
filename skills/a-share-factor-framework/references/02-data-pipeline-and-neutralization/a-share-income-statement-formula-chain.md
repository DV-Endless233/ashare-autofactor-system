# A 股利润表公式链（数据库验证版）

> 本文件使用 `ashareincome.feather` 中的真实数据验证了 A 股利润表各字段之间的会计关系。
> 数据路径：`${PROJECT_ROOT}/database/selfdata/data/windsqldata/ashareincome.feather`

## 字段映射

| signame（语义名） | 数据库字段 | 中文名称 | 所属组 |
|:---:|:---:|:---|:---:|
| opinc | `oper_rev` | 营业收入 | income |
| totopinc | `tot_oper_rev` | 营业总收入 | income |
| toptopcost | `tot_oper_cost` | 营业总成本 | cost |
| inctax | `inc_tax` | 所得税费用 | income |
| gp | `tot_oper_rev - tot_oper_cost` | 毛利（计算字段） | profit |
| op | `oper_profit` | 营业利润 | profit |
| totp | `tot_profit` | 利润总额 | profit |
| np | `net_profit_incl_min_int_inc` | 净利润(含少数) | profit |
| nptopc | `net_profit_excl_min_int_inc` | 归母净利润 | profit |
| rdexp | `rd_expense` | 研发费用 | expense |
| adminexp | `less_gerl_admin_exp` | 管理费用 | expense |
| sellingexp | `less_selling_dist_exp` | 销售费用 | expense |
| finexp | `less_fin_exp` | 财务费用 | expense |

## 公式链（用 600519.SH 2025年报验证）

```
营业收入(totopinc)               1,720.5亿    100%
- 营业成本(totopcost)              573.5亿     33.3%
= 毛利(gp)                       1,147.0亿     66.7%    ← gp = totopinc - totopcost ✓

毛利(gp)                         1,147.0亿     66.7%
- 销售费用(sellingexp)               72.5亿
- 管理费用(adminexp)                83.2亿
- 研发费用(rdexp)                    1.9亿
- 财务费用(finexp)                  -8.2亿(负=收入)
+ 投资收益/公允价值/其他             150.6亿
= 营业利润(op)                    1,148.1亿     66.7%

营业利润(op)                      1,148.1亿     66.7%
+ 营业外收入 - 营业外支出             -0.5亿
= 利润总额(totp)                  1,147.6亿     66.7%

利润总额(totp)                    1,147.6亿     66.7%
- 所得税(inctax)                    294.4亿     17.1%
= 净利润(np, 含少数)                853.1亿     49.6%

净利润(np)                         853.1亿     49.6%
- 少数股东损益                      30.0亿
= 归母净利润(nptopc)               823.2亿     47.8%
```

## 常见误解（用真实数据纠正）

### 误解 1：「净利润 ≈ 毛利 - 四项费用」
```
毛利(gp) - 四项费用 = 1,147.0 - 149.5 = 997.5亿
但营业利润(op) = 1,148.1亿
差额 = 150.6亿 = 投资收益 + 其他收益
```
→ 营业利润中还包含投资收益、公允价值变动损益、资产减值损失等，这些项目可能占比巨大（如比亚迪 2025 年，gp - 四项费用 = -805.8 亿，靠 1,207.6 亿其他收益拉正到 401.8 亿）

### 误解 2：totopinc（营业收入）= income（净利润）
```
totopinc = 1,720.5亿  
np = 853.1亿  
两者相差 867.4 亿，隔着 gp→op→totp→np 四层
```
→ totopinc 是营收（revenue），np 是净利（income），完全不是同一个东西

### 误解 3：totopinc = tot_oper_rev 与 opinc = oper_rev 可互换
```
贵州茅台 2025年报：
tot_oper_rev = 1,720.5亿（包含利息收入等其他经营收入）
oper_rev = 1,720.5亿（相同——茅台无非主营收入）
但某些公司（如银行、券商）两者可能差异较大
```
→ 大多数制造企业两者相等，但金融/混业公司可能不同。不确定时优先用 totopinc（tot_oper_rev）

## 获取真实数据的 Python 代码

```python
import pandas as pd

income = pd.read_feather("${PROJECT_ROOT}/database/selfdata/data/windsqldata/ashareincome.feather")
income['perEndDt'] = income['perEndDt'].astype(str)

# 选一家公司
df = income[income['Stkcd'] == '600519.SH'].sort_values('perEndDt', ascending=False)

# 关键字段
cols = ['Stkcd', 'perEndDt', 'tot_oper_rev', 'tot_oper_cost', 'oper_profit', 
        'tot_profit', 'inc_tax', 'net_profit_incl_min_int_inc', 
        'net_profit_excl_min_int_inc', 'less_selling_dist_exp',
        'less_gerl_admin_exp', 'rd_expense', 'less_fin_exp']
```

## 数据文件位置

| 文件 | 大小 | 内容 |
|:----|:---:|:-----|
| `ashareincome.feather` | 120MB | 利润表(685K行, 39列) |
| `asharebalancesheet.feather` | 176MB | 资产负债表 |
| `asharecashflow.feather` | 207MB | 现金流量表 |
