# util/ 非 rawsig 共享算子分类参考

## 用途

当因子在语义空间构思阶段或算子空间表达升级阶段，需要知道当前框架提供了哪些「组合方式」时，按空间定位到本文件寻找对应函数。这不是完整 API 文档——只是快速定位表。

完整明细见：`${PROJECT_ROOT}/util非rawsigs代码空间分类表_v5_fun重写.xlsx`（296 行）
一句话说明见：`${PROJECT_ROOT}/util非rawsigs当前代码一句话说明_v8.xlsx`（40 个文件）

## 按空间分类

### 变量映射空间

| 文件 | 关键函数 | 用途 |
|---|---|---|
| `fiscalsigclass.py` | `fiscalsigclass_` | 财报原子信号加载，按 fiscaltype/lagqnum/ynum 取财务字段 |
| `industryclass.py` | `industryclass_` | 行业映射，按 citics/sw 等分类取股票行业归属 |
| `stkfactorclass.py` | `stkfactor` | 因子缓存父类，getfac_ / solvefac_ / sigconstruct_ 标准面板生成 |

### 算子空间：比值类

| 文件 | 关键函数 | 用途 |
|---|---|---|
| `fiscalsigfun.py` | `x2y_sig_` | 单期 x/y，无日期截面比值 |
| `fiscalsigfun.py` | `x2y_periodssig_` | 面板级 x/y，逐期比值 |
| `fiscalsigx2yclass.py` | `fiscalsigx2yclass_` | x/y 组合父类 |
| `fiscalsigx2avgyclass.py` | `fiscalsigx2avgyclass_` | x/avg(y) 均值分母比值 |

### 算子空间：差分类

| 文件 | 关键函数 | 用途 |
|---|---|---|
| `fiscalsigfun.py` | `xmy_periodssig_` | x-y 逐期差值 |
| `fiscalsigqmqclass.py` | `fiscalsigqmqclass_` | x-y 差分类父类 |

### 算子空间：增长类

| 文件 | 关键函数 | 用途 |
|---|---|---|
| `fiscalsigfun.py` | `gro_xmy_periodssig_` | (x-y)/\|y\| 增长率算子 |
| `gro_fiscalsigqmqclass.py` | `gro_fiscalsigqmqclass_` | (x-y)/\|y\| 增长率父类 |
| `utilfun.py` | `yearonyeargrowth` | 同比增速，映射回交易期面板 |
| `utilfun.py` | `yoymom_` | 同比动量：YoY 的环比变化率 |

### 算子空间：时序变换类

| 文件 | 关键函数 | 用途 |
|---|---|---|
| `gpfuncutil.py` | `delta_(x, n)` | numpy 矩阵级 n 期差分 |
| `gpfuncutil.py` | `cummax_` / `cummin_` | 累计极值 |
| `FinancialFun.py` | `jy_ttm` | 累计财报转 TTM |
| `FinancialFun.py` | `jy_quarter` | 累计财报拆单季 |
| `FinancialFun.py` | `lagity_jy_onlypdt` | N 年前同月报告期滞后 |
| `FinancialFun.py` | `lagitq_jy_onlypdt` | 上季度报告期滞后 |

### 算子空间：回归与优化类

| 文件 | 关键函数 | 用途 |
|---|---|---|
| `regfun.py` | `constrained_wls` | 带系数边界/和约束的 WLS |
| `portoptutil.py` | `optportclass_` | cvxpy 组合优化 |
| `utilfun.py` | `optimize_portfolio` | 个股上限+行业偏离约束优化 |

### 验证空间：截面变换类

| 文件 | 关键函数 | 用途 |
|---|---|---|
| `utilfun.py` | `winsomadsort_` | MAD 识别 + 有序压缩，保留尾部排序 |
| `utilfun.py` | `Zscore` | 最轻量截面标准化 |
| `utilfun.py` | `standardize_winsomadsort_` | MAD 压缩 + zscore |
| `utilfun.py` | `get_sigindrank_` | 行业内百分位排序 |
| `utilfun.py` | `SymOrth_` | 多列信号对称正交化 |
| `utilfun.py` | `sigfillna_` / `sigfillna_indg_` | 行业分位数补空值 |
| `utilfun.py` | `factor_fillna_indmedian_` | 行业中位数补空值 |
| `utilfun.py` | `mapdata_into_range_` | 按排名压回范围（非 clip） |
| `neutfactorclass.py` | `neutfactorclas_` | 市值+行业/BARRA 中性化 |

### 验证空间：回测类

| 文件 | 关键函数 | 用途 |
|---|---|---|
| `stkfactorbacktest.py` | `Stkfactorbacktest_` | RankIC / 分组收益 / 多空收益 |
| `utilfun.py` | `baskettest_` | 组合回测执行引擎 |
| `utilfun.py` | `backtest` | 完整策略回测（价格→净值→统计） |
| `utilfun.py` | `rptstat_` | 绩效统计表 |
| `utilfun.py` | `halflife_` | 指数衰减权重 |

## 选函数的原则

1. 先看空间归属：数据空间→语义空间→变量映射→算子空间→参数空间→验证空间，保证逻辑层对应。
2. 优先用已有父类（fiscalsigx2yclass_ 等），而非手动 inline。
3. 找不到合适算子时，才考虑扩展共享层。
4. 叶子层不承担公共逻辑——任何可能被多个因子复用的算子，都应下沉到 util/ 非 rawsig。
