# -*- coding: utf-8 -*-
"""第四层 sigconstructperiods_ 直接使用的公式工具箱。

设计原则
--------
- 输入默认是 date x Stkcd 的宽表 pivot。
- 输出尽量保持同形状宽表，便于在 sigconstructperiods_ 里链式拼公式。
- 不走 factor_loader；这里只保留公式层与 pivot/periods 工具。
- 优先吸收 util/expr_ops.py 与 util/rawsigs/_codex_utils/growth_ops.py 的稳定逻辑，
 但在本文件内直接提供可调用函数，避免在第四层重复拼底层细节。
"""

import numpy as np
import pandas as pd
import warnings

from database.code.windsql.ashareeodderivativeindicator import ashareeodderivativeindicator_
from database.code.windsql.ashareeodprices import ashareeodprices_
from util.WindTradingDay import WindTradingDay_
from util.utilfun import tdatesshift_


# -------------------------
# periods / long-wide 工具
# -------------------------

def extend_periods_(periods_list, extra=24):
    """按月初交易日向前扩展若干期，用于支持回看窗口。"""
    if not periods_list:
        return []

    first_dt = periods_list[0]
    last_dt = periods_list[-1]
    all_mf = WindTradingDay_(
        fromdt='20000101',
        todt=last_dt,
        IfMonthFirst=True,
    )['date'].tolist()

    try:
        first_idx = all_mf.index(first_dt)
    except ValueError:
        return periods_list

    start_idx = max(0, first_idx - extra)
    return all_mf[start_idx:]


def pivot_vals_(rawdata, value_col):
    """长表转为 date x Stkcd 宽表。"""
    pivot = rawdata.pivot_table(index='date', columns='Stkcd', values=value_col)
    pivot.sort_index(inplace=True)
    return pivot


def pivot_to_long_(pivot, value_name='sig', dropna=False):
    """宽表转长表。"""
    try:
        long_df = pivot.stack(future_stack=True).reset_index()
    except TypeError:
        long_df = pivot.stack(dropna=False).reset_index()
    long_df.columns = ['date', 'Stkcd', value_name]
    if dropna:
        long_df.dropna(subset=[value_name], inplace=True)
    return long_df


def pivot_and_ffill_(factor_long, target_set):
    """长表 -> pivot -> ffill -> 对齐目标 periods -> 返回标准 sig 长表。"""
    if factor_long is None or factor_long.empty:
        return pd.DataFrame(columns=['date', 'Stkcd', 'sig'])

    g_pivot = factor_long.pivot_table(index='date', columns='Stkcd', values='sig')
    g_pivot.sort_index(inplace=True)
    g_pivot.ffill(inplace=True)
    g_pivot = g_pivot.reindex(sorted(target_set))
    g_pivot.ffill(inplace=True)
    g_pivot = g_pivot.loc[g_pivot.index.isin(target_set)]

    factorfinal = g_pivot.stack().reset_index()
    factorfinal.columns = ['date', 'Stkcd', 'sig']
    factorfinal.dropna(subset=['sig'], inplace=True)
    return factorfinal


# -------------------------
# 单因子时序变形
# -------------------------

def lag_(pivot, n=1):
    return pivot.shift(n)


def diff_(pivot, n=1):
    return pivot.diff(n)


def abs_(pivot):
    return pivot.abs()


def neg_(pivot):
    return -pivot


def sign_(pivot):
    return np.sign(pivot)


def sqrt_abs_(pivot):
    return np.sqrt(pivot.abs())


def log_abs1p_(pivot):
    return np.log1p(pivot.abs())


def rolling_mean_(pivot, window, min_periods=1):
    return pivot.rolling(window, min_periods=min_periods).mean()


def rolling_std_(pivot, window, ddof=1, min_periods=1):
    return pivot.rolling(window, min_periods=min_periods).std(ddof=ddof)


def rolling_skew_(pivot, window, min_periods=3):
    return pivot.rolling(window, min_periods=min_periods).skew()


def rolling_kurt_(pivot, window=60, min_periods=4):
    return pivot.rolling(window, min_periods=min_periods).kurt()


def rowwise_moments_(data, value_cols, mean_col='row_mean', std_col='row_std', ddof=1):
    """对指定列集合逐行计算均值与标准差。"""
    out = data.copy()
    out[mean_col] = out[value_cols].mean(axis=1)
    out[std_col] = out[value_cols].std(axis=1, ddof=ddof)
    return out


def rolling_sum_(pivot, window, min_periods=1):
    return pivot.rolling(window, min_periods=min_periods).sum()


def log_price_(pivot):
    """对正价格取对数，非正值置空。"""
    return np.log(pivot.where(pivot > 0))


def price_path_efficiency_(price_pivot, skip_days, lookback_days, min_obs=None):
    """价格路径效率 = 跳过近端后的净对数位移 / 同窗口绝对对数收益路径长度。"""
    if min_obs is None:
        min_obs = max(3, int(np.floor(lookback_days * 2 / 3)))

    log_price = log_price_(price_pivot)
    log_ret = diff_(log_price, n=1)
    net_disp = sub_(lag_(log_price, n=skip_days), lag_(log_price, n=skip_days + lookback_days))
    path_len = rolling_sum_(abs_(lag_(log_ret, n=skip_days)), window=lookback_days, min_periods=min_obs)
    path_len = path_len.where(path_len > 1e-12)
    return div_(net_disp, path_len)


def rolling_min_(pivot, window, min_periods=1):
    return pivot.rolling(window, min_periods=min_periods).min()


def rolling_max_(pivot, window, min_periods=1):
    return pivot.rolling(window, min_periods=min_periods).max()


def rolling_median_(pivot, window, min_periods=1):
    return pivot.rolling(window, min_periods=min_periods).median()


def rolling_zscore_(pivot, window, ddof=1, min_periods=2):
    mean_ = rolling_mean_(pivot, window=window, min_periods=min_periods)
    std_ = rolling_std_(pivot, window=window, ddof=ddof, min_periods=min_periods)
    std_ = std_.where(std_.abs() > 1e-12)
    return (pivot - mean_) / std_


def load_daily_stock_ret_and_market_ret_(fromdt, todt, weight_var='s_dq_mv'):
    """加载个股日收益与按滞后流通市值加权的全市场日收益。

    Notes
    -----
    - 个股收益来自 `ashareeodprices.ret`（百分比口径，函数内转小数）。
    - 默认权重 `s_dq_mv` 来自 `ashareeodderivativeindicator`，对应日度流通市值。
    - 市场收益使用 `t-1` 日权重聚合 `t` 日个股收益，避免未来函数。
    """
    priceclass = ashareeodprices_()
    derclass = ashareeodderivativeindicator_()

    ret_df = priceclass.getdata_(varnames=['ret'], fromdt=fromdt, todt=todt)
    ret_df = ret_df[['date', 'Stkcd', 'ret']].copy()
    ret_df['ret'] = pd.to_numeric(ret_df['ret'], errors='coerce') / 100.0

    if weight_var == 's_dq_mv':
        mv_df = derclass.getdata_(varnames=['s_dq_mv'], fromdt=fromdt, todt=todt)
        mv_df = mv_df[['date', 'Stkcd', 's_dq_mv']].copy()
        mv_df['mv'] = pd.to_numeric(mv_df['s_dq_mv'], errors='coerce')
    elif weight_var in {'float_a_shr_today', 'free_shares_today', 'tot_shr_today'}:
        mv_df = derclass.getdata_(varnames=[weight_var, 's_dq_close_today'], fromdt=fromdt, todt=todt)
        mv_df = mv_df[['date', 'Stkcd', weight_var, 's_dq_close_today']].copy()
        mv_df['mv'] = pd.to_numeric(mv_df[weight_var], errors='coerce') * 10000.0 * pd.to_numeric(mv_df['s_dq_close_today'], errors='coerce')
    else:
        raise ValueError(f'unsupported market weight var: {weight_var}')

    daily_df = pd.merge(ret_df, mv_df[['date', 'Stkcd', 'mv']], on=['date', 'Stkcd'], how='inner')
    daily_df = daily_df.sort_values(['Stkcd', 'date']).reset_index(drop=True)
    daily_df['lag_mv'] = daily_df.groupby('Stkcd')['mv'].shift(1)
    daily_df = daily_df.replace([np.inf, -np.inf], np.nan)
    daily_df = daily_df.dropna(subset=['ret', 'lag_mv'])
    daily_df = daily_df[daily_df['lag_mv'] > 0].copy()

    market_ret = daily_df.groupby('date').apply(
        lambda df: np.average(df['ret'].to_numpy(), weights=df['lag_mv'].to_numpy())
    )
    market_ret.name = 'market_ret'
    market_ret.index = market_ret.index.astype(str)
    market_ret = market_ret.sort_index()

    ret_pivot = ret_df.pivot_table(index='date', columns='Stkcd', values='ret')
    ret_pivot.sort_index(inplace=True)
    ret_pivot = ret_pivot.loc[ret_pivot.index.isin(market_ret.index)]
    market_ret = market_ret.reindex(ret_pivot.index)
    return ret_pivot, market_ret


def rolling_capm_resid_std_(ret_pivot, market_ret, window=60, min_periods=None, ddof=1):
    """CAPM rolling residual std.

    OLS with intercept under simple CAPM satisfies:
        std(resid) = std(y) * sqrt(1 - corr(y, x)^2)
    where y is stock return and x is market return in the same rolling window.
    This matches `fit.resid.std(ddof=1)` exactly while avoiding per-stock rolling regressions.
    """
    if min_periods is None:
        min_periods = window
    if ret_pivot is None or ret_pivot.empty or market_ret is None or len(market_ret) == 0:
        return pd.DataFrame(index=getattr(ret_pivot, 'index', None), columns=getattr(ret_pivot, 'columns', None))

    market_ret = pd.Series(market_ret).reindex(ret_pivot.index)
    stock_std = ret_pivot.rolling(window=window, min_periods=min_periods).std(ddof=ddof)
    corr = ret_pivot.rolling(window=window, min_periods=min_periods).corr(market_ret)
    corr = corr.clip(lower=-1.0, upper=1.0)
    resid_std = stock_std * np.sqrt((1.0 - corr ** 2).clip(lower=0.0))
    return resid_std


def daily_signal_pivot_to_periods_(signal_pivot, periods):
    """把日频 signal pivot 用 LTD 对齐到调仓 periods。"""
    periods = sorted(list(periods))
    if signal_pivot is None or signal_pivot.empty or not periods:
        return pd.DataFrame(columns=['date', 'Stkcd', 'sig'])

    date_ltd = tdatesshift_(periods, -1)
    date_ltd.columns = ['date', 'ltd']
    ltd_list = [d for d in date_ltd['ltd'].tolist() if d in signal_pivot.index]
    if not ltd_list:
        return pd.DataFrame(columns=['date', 'Stkcd', 'sig'])

    factormatperiods = signal_pivot.loc[ltd_list]
    factorfinal = factormatperiods.stack().reset_index()
    factorfinal.columns = ['ltd', 'Stkcd', 'sig']
    factorfinal = pd.merge(factorfinal, date_ltd, on=['ltd'], how='inner')
    factorfinal = factorfinal[['date', 'Stkcd', 'sig']].copy()
    factorfinal = factorfinal[factorfinal['date'].isin(periods)].reset_index(drop=True).copy()
    factorfinal = factorfinal.replace([np.inf, -np.inf], np.nan)
    factorfinal.dropna(subset=['sig'], inplace=True)
    return factorfinal


def daily_capm_ivol_factor_(periods, window=60, weight_var='s_dq_mv', lookback_buffer=40):
    """按月频 periods 生成 CAPM rolling residual std 因子长表。"""
    periods = sorted(list(periods))
    if not periods:
        return pd.DataFrame(columns=['date', 'Stkcd', 'sig'])

    trading_days = WindTradingDay_(fromdt=None, todt=min(periods))['date']
    start_idx = max(0, len(trading_days) - (int(window) + int(lookback_buffer)))
    startdt = trading_days.iloc[start_idx]
    enddt = WindTradingDay_(fromdt=None, todt=max(periods))['date'].iloc[-2]

    ret_pivot, market_ret = load_daily_stock_ret_and_market_ret_(
        fromdt=startdt,
        todt=enddt,
        weight_var=weight_var,
    )
    ivol_pivot = rolling_capm_resid_std_(
        ret_pivot=ret_pivot,
        market_ret=market_ret,
        window=int(window),
        min_periods=int(window),
        ddof=1,
    )
    return daily_signal_pivot_to_periods_(ivol_pivot, periods)


def seasonal_surprise_long_(rawdata, value_col='x', lag=4, lookback=8, min_periods=None, ddof=1):
    """季度口径 SUE：按每只股票的 rptdate 序列计算同季差分并用自身历史 surprise 波动率标准化。

    参数
    ----
    rawdata : DataFrame
        至少包含 ['date', 'rptdate', 'Stkcd', value_col]。
        `date` 是该季度值首次可见的交易期；`rptdate` 是财报期末日期。
    lag : int
        同季差分的季度滞后，标准 SUE 用 4。
    lookback : int
        对 seasonal delta 做 rolling std 的窗口，单位也是季度观测数。
    min_periods : int or None
        rolling std 的最小样本数；默认取 max(4, lookback // 2)。

    返回
    ----
    DataFrame: ['date', 'Stkcd', 'sig']
        信号落在每个 rptdate 首次进入样本的可交易期，再由叶子层对月频 periods 前向填充。
    """
    req_cols = {'date', 'rptdate', 'Stkcd', value_col}
    if rawdata is None or rawdata.empty or not req_cols.issubset(rawdata.columns):
        return pd.DataFrame(columns=['date', 'Stkcd', 'sig'])

    if min_periods is None:
        min_periods = max(4, lookback // 2)

    qdf = rawdata[['date', 'rptdate', 'Stkcd', value_col]].copy()
    qdf = qdf.dropna(subset=[value_col, 'rptdate'])
    if qdf.empty:
        return pd.DataFrame(columns=['date', 'Stkcd', 'sig'])

    qdf = qdf.sort_values(['Stkcd', 'rptdate', 'date']).drop_duplicates(['Stkcd', 'rptdate'], keep='first')
    qdf = qdf.sort_values(['Stkcd', 'rptdate', 'date']).reset_index(drop=True)

    qdf['seasonal_delta'] = qdf.groupby('Stkcd')[value_col].diff(lag)
    qdf['surprise_std'] = qdf.groupby('Stkcd')['seasonal_delta'].transform(
        lambda s: s.rolling(lookback, min_periods=min_periods).std(ddof=ddof)
    )
    qdf['surprise_std'] = qdf['surprise_std'].where(qdf['surprise_std'].abs() > 1e-12)
    qdf['sig'] = qdf['seasonal_delta'] / qdf['surprise_std']

    out = qdf[['date', 'Stkcd', 'sig']].dropna(subset=['sig']).copy()
    out.sort_values(['date', 'Stkcd'], inplace=True)
    out.reset_index(drop=True, inplace=True)
    return out


def yoy_abs_(pivot, lagqnum=4):
    lag_pivot = lag_(pivot, lagqnum)
    out = (pivot - lag_pivot) / lag_pivot.abs()
    return out.replace([np.inf, -np.inf], np.nan)


def yoy_raw_(pivot, lagqnum=4):
    lag_pivot = lag_(pivot, lagqnum)
    out = (pivot - lag_pivot) / lag_pivot
    return out.replace([np.inf, -np.inf], np.nan)


def rolling_ols_beta_(pivot, window, min_obs=None):
    """对每列滑动 OLS: x = beta * t + e，返回 beta 长表。"""
    if min_obs is None:
        min_obs = max(3, window // 2 + 1)

    date_index = pivot.index.tolist()
    n_dates = len(date_index)
    if n_dates < window:
        return pd.DataFrame(columns=['date', 'Stkcd', 'beta'])

    t_vec = np.arange(window, dtype=float)
    t_mean = np.mean(t_vec)
    denom = np.sum((t_vec - t_mean) ** 2)

    result = []
    for i in range(window - 1, n_dates):
        cur_date = date_index[i]
        window_vals = pivot.iloc[i - window + 1:i + 1].values
        obs_count = (~np.isnan(window_vals)).sum(axis=0)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=RuntimeWarning)
            x_mean = np.nanmean(window_vals, axis=0)
        x_demeaned = window_vals - x_mean[np.newaxis, :]
        t_demeaned = (t_vec - t_mean)[:, np.newaxis]
        beta = np.nansum(t_demeaned * x_demeaned, axis=0) / denom
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=RuntimeWarning)
            x_std = np.nanstd(window_vals, axis=0)

        valid = (
            (obs_count >= min_obs)
            & (~np.isnan(x_mean))
            & (~np.isnan(beta))
            & (~np.isnan(x_std))
            & (x_std > 1e-6)
        )
        beta[~valid] = np.nan
        result.append(
            pd.DataFrame({
                'date': cur_date,
                'Stkcd': pivot.columns.values,
                'beta': beta,
            })
        )

    return pd.concat(result, axis=0, ignore_index=True)


def ar1_coeff_rolling_(data, window=8, min_obs=4, value_cols=None, eps=1e-12):
    """对 trailing window 内的相邻滞后对做 AR(1) slope，返回逐行 beta。

    参数
    ----
    data : DataFrame / Series / ndarray
        若为 DataFrame，默认按列顺序读取 trailing values，要求从当前值到更老值排列；
        也可显式传 `value_cols`。例如 ['value_lag0', 'value_lag1', ..., 'value_lag7']。
    window : int
        使用前 `window` 个 trailing observations。窗口内共有 `window-1` 个 (y_t, y_{t-1}) 配对。
    min_obs : int
        最少有效配对数。小于该阈值返回 NaN。

    返回
    ----
    Series / float / ndarray
        与输入行对应的 AR(1) beta。若输入为 DataFrame 返回同 index 的 Series；
        输入为 Series 返回 float；输入为 ndarray 返回 1d ndarray。
    """
    if isinstance(data, pd.Series):
        values = data.to_numpy(dtype=float)
        series_name = data.name
        index = None
        return_scalar = True
    elif isinstance(data, pd.DataFrame):
        cols = list(value_cols) if value_cols is not None else list(data.columns)
        values = data[cols].to_numpy(dtype=float)
        index = data.index
        series_name = 'ar1_beta'
        return_scalar = False
    else:
        values = np.asarray(data, dtype=float)
        index = None
        series_name = 'ar1_beta'
        return_scalar = values.ndim == 1

    if values.ndim == 1:
        values = values[np.newaxis, :]
    if values.size == 0:
        beta = np.array([], dtype=float)
        if index is not None:
            return pd.Series(beta, index=index, name=series_name)
        return np.nan if return_scalar else beta

    window = int(window)
    min_obs = int(min_obs)
    if window <= 1:
        beta = np.full(values.shape[0], np.nan, dtype=float)
    else:
        values = values[:, :window]
        if values.shape[1] < 2:
            beta = np.full(values.shape[0], np.nan, dtype=float)
        else:
            y = values[:, :-1]
            x = values[:, 1:]
            valid = (~np.isnan(x)) & (~np.isnan(y))
            obs_count = valid.sum(axis=1)
            x = np.where(valid, x, np.nan)
            y = np.where(valid, y, np.nan)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                x_mean = np.nanmean(x, axis=1)
                y_mean = np.nanmean(y, axis=1)
            x_demeaned = x - x_mean[:, np.newaxis]
            y_demeaned = y - y_mean[:, np.newaxis]
            denom = np.nansum(x_demeaned ** 2, axis=1)
            numer = np.nansum(x_demeaned * y_demeaned, axis=1)
            beta = numer / denom
            invalid = (
                (obs_count < min_obs)
                | np.isnan(denom)
                | (denom <= eps)
                | np.isnan(beta)
            )
            beta[invalid] = np.nan

    if index is not None:
        return pd.Series(beta, index=index, name=series_name)
    if return_scalar:
        return float(beta[0]) if len(beta) else np.nan
    return beta


ar1_coeff_rolling = ar1_coeff_rolling_


# -------------------------
# 双因子组合
# -------------------------

def add_(pivot_a, pivot_b):
    return pivot_a + pivot_b


def sub_(pivot_a, pivot_b):
    return pivot_a - pivot_b


def net_working_capital_(curasset_pivot, curdebt_pivot):
    """净营运资金 = 流动资产 - 流动负债。"""
    return sub_(curasset_pivot, curdebt_pivot)


def operating_working_capital_(
    acctrcv_pivot,
    inventories_pivot,
    prepay_pivot,
    notesrcv_pivot,
    acctpayable_pivot,
    notespayable_pivot,
    advfromcust_pivot,
    taxpayable_pivot,
):
    """经营性营运资金近似 = 经营性流动资产 - 经营性流动负债。"""
    op_assets = add_(add_(add_(acctrcv_pivot, inventories_pivot), prepay_pivot), notesrcv_pivot)
    op_liab = add_(add_(add_(acctpayable_pivot, notespayable_pivot), advfromcust_pivot), taxpayable_pivot)
    return sub_(op_assets, op_liab)


def gross_profit_(revenue_pivot, cost_pivot):
    """毛利 = 营业收入 - 营业成本。"""
    return sub_(revenue_pivot, cost_pivot)


def mul_(pivot_a, pivot_b):
    out = pivot_a * pivot_b
    return out.replace([np.inf, -np.inf], np.nan)


def div_(pivot_a, pivot_b):
    out = pivot_a / pivot_b
    return out.replace([np.inf, -np.inf], np.nan)


def div_abs_(pivot_a, pivot_b):
    out = pivot_a / pivot_b.abs()
    return out.replace([np.inf, -np.inf], np.nan)


def cash_confirmed_earnings_to_assets_(cfo_pivot, parent_net_profit_pivot, asset_pivot):
    """现金确认盈利资产强度 = (经营现金流TTM - 归母净利润TTM) / 总资产。

    仅剔除总资产非正的会计无效样本；不加基于历史表现的门控或奖励。
    """
    numerator = sub_(cfo_pivot, parent_net_profit_pivot)
    denom = asset_pivot.where(asset_pivot > 0)
    return div_(numerator, denom)


def receivable_accrual_intensity_(receivable_now_pivot, receivable_lag_pivot, revenue_pivot):
    """应收应计强度 = -(应收账款_t - 应收账款_{t-lag}) / 营业总收入TTM。

    AR 增加代表收入现金确认不足，因此取负号使高值表示较低应收侵蚀。
    仅剔除营业收入非正的会计无效样本；不加门控或奖励。
    """
    delta_receivable = sub_(receivable_now_pivot, receivable_lag_pivot)
    denom = revenue_pivot.where(revenue_pivot > 0)
    return div_(neg_(delta_receivable), denom)


def per_employee_efficiency_(numerator_pivot, staff_number_pivot):
    """人均效率 = 业务规模或利润口径 / 员工总数。

    员工总数必须为正。该函数只处理分母有效性，不做历史表现门控。
    """
    denom = staff_number_pivot.where(staff_number_pivot > 0)
    return div_(numerator_pivot, denom)


def standard_rate_tax_saving_yield_(pretax_profit, income_tax, total_assets,
                                    standard_tax_rate=0.25,
                                    require_positive_pretax=True):
    """普通 25% 税率基准下的税收节约金额 / 总资产。

    公式：
        (standard_tax_rate * pretax_profit - income_tax) / total_assets

    这里的 standard_tax_rate 是普通企业所得税基准，不是公司级实际适用
    statutory rate。有效性处理来自经济含义：总资产必须为正；默认要求
    税前利润为正，否则"税收节约"会混入亏损抵扣/递延所得税口径。
    """
    normal_tax = standard_tax_rate * pretax_profit
    out = (normal_tax - income_tax) / total_assets
    valid = total_assets > 0
    if require_positive_pretax:
        valid = valid & (pretax_profit > 0)
    out = out.where(valid)
    return out.replace([np.inf, -np.inf], np.nan)


def avg_positive_(pivot_a, pivot_b):
    """两期正总资产均值；任一期资产非正时置空。

    用于资产负债表变化量缩放。这里只做会计分母有效性处理，
    不做基于历史表现的门控或奖励。
    """
    avg = (pivot_a + pivot_b) / 2.0
    return avg.where((pivot_a > 0) & (pivot_b > 0) & (avg > 0))


def scaled_delta_by_avg_assets_(value_now_pivot, value_lag_pivot,
                                asset_now_pivot, asset_lag_pivot):
    """同比变化量 / 两期平均总资产。

    公式：
        (X_t - X_{t-lag}) / ((TA_t + TA_{t-lag}) / 2)
    """
    delta_value = sub_(value_now_pivot, value_lag_pivot)
    avg_assets = avg_positive_(asset_now_pivot, asset_lag_pivot)
    return div_(delta_value, avg_assets)


def operating_working_capital_clean_(curasset_pivot, cash_pivot,
                                     curdebt_pivot, stborrow_pivot):
    """剔除现金和短债的经营性营运资本。

    OWC = (CurrentAssets - Cash) - (CurrentLiabilities - ShortTermBorrowings)
    """
    operating_current_assets = sub_(curasset_pivot, cash_pivot)
    operating_current_liabs = sub_(curdebt_pivot, stborrow_pivot)
    return sub_(operating_current_assets, operating_current_liabs)


def operating_working_capital_accrual_clean_(curasset_now_pivot, cash_now_pivot,
                                             curdebt_now_pivot, stborrow_now_pivot,
                                             asset_now_pivot,
                                             curasset_lag_pivot, cash_lag_pivot,
                                             curdebt_lag_pivot, stborrow_lag_pivot,
                                             asset_lag_pivot):
    """剔除现金和短债的经营性营运资本应计变化 / 平均总资产。"""
    owc_now = operating_working_capital_clean_(
        curasset_now_pivot, cash_now_pivot, curdebt_now_pivot, stborrow_now_pivot,
    )
    owc_lag = operating_working_capital_clean_(
        curasset_lag_pivot, cash_lag_pivot, curdebt_lag_pivot, stborrow_lag_pivot,
    )
    return scaled_delta_by_avg_assets_(owc_now, owc_lag, asset_now_pivot, asset_lag_pivot)


def working_capital_accruals_dd_(curasset_now_pivot, cash_now_pivot,
                                 curdebt_now_pivot, stborrow_now_pivot,
                                 dep_pivot,
                                 curasset_lag_pivot, cash_lag_pivot,
                                 curdebt_lag_pivot, stborrow_lag_pivot,
                                 asset_now_pivot=None, asset_lag_pivot=None,
                                 scale_by_avg_assets=True):
    """Dechow-Dichev 口径 working capital accruals。

    WCA_t = ΔCA_t - ΔCash_t - ΔCL_t + ΔSTD_t - Dep_t

    若提供两期总资产，则进一步除以两期平均总资产，提升跨股票可比性。
    """
    delta_curasset = sub_(curasset_now_pivot, curasset_lag_pivot)
    delta_cash = sub_(cash_now_pivot, cash_lag_pivot)
    delta_curdebt = sub_(curdebt_now_pivot, curdebt_lag_pivot)
    delta_stborrow = sub_(stborrow_now_pivot, stborrow_lag_pivot)

    wca = add_(
        sub_(sub_(delta_curasset, delta_cash), delta_curdebt),
        delta_stborrow,
    )
    wca = sub_(wca, dep_pivot)

    if scale_by_avg_assets:
        if asset_now_pivot is None or asset_lag_pivot is None:
            raise ValueError('asset_now_pivot and asset_lag_pivot are required when scale_by_avg_assets=True')
        avg_assets = avg_positive_(asset_now_pivot, asset_lag_pivot)
        wca = div_(wca, avg_assets)
    return wca.replace([np.inf, -np.inf], np.nan)


def rolling_multivariate_residual_std_(y_pivot, x_pivots,
                                       reg_window=12, std_window=8,
                                       reg_min_obs=None, std_min_obs=None,
                                       include_intercept=True):
    """多元滚动时序回归残差及其滚动波动率。"""
    if not x_pivots:
        raise ValueError('x_pivots must not be empty')

    reg_window = int(reg_window)
    std_window = int(std_window)
    if reg_window < 2:
        raise ValueError('reg_window must be >= 2')
    if std_window < 2:
        raise ValueError('std_window must be >= 2')

    if reg_min_obs is None:
        reg_min_obs = max(len(x_pivots) + 2, reg_window // 2)
    if std_min_obs is None:
        std_min_obs = max(2, std_window // 2)

    residual_pivot = pd.DataFrame(index=y_pivot.index, columns=y_pivot.columns, dtype=float)

    for col in y_pivot.columns:
        y = y_pivot[col].to_numpy(dtype=float)
        x_cols = [xp[col].to_numpy(dtype=float) for xp in x_pivots]
        resid = np.full(y.shape, np.nan, dtype=float)

        for i in range(reg_window - 1, len(y)):
            y_win = y[i - reg_window + 1:i + 1]
            x_win = np.column_stack([x[i - reg_window + 1:i + 1] for x in x_cols])
            valid = (~np.isnan(y_win)) & (~np.isnan(x_win).any(axis=1))
            if int(valid.sum()) < reg_min_obs:
                continue

            y_reg = y_win[valid]
            x_reg = x_win[valid]
            X = np.column_stack([np.ones(len(y_reg)), x_reg]) if include_intercept else x_reg
            if np.linalg.matrix_rank(X) < X.shape[1]:
                continue

            y_cur = y[i]
            x_cur = np.array([x[i] for x in x_cols], dtype=float)
            if np.isnan(y_cur) or np.isnan(x_cur).any():
                continue

            beta, _, _, _ = np.linalg.lstsq(X, y_reg, rcond=None)
            pred = (np.concatenate([[1.0], x_cur]) @ beta) if include_intercept else (x_cur @ beta)
            resid[i] = y_cur - pred

        residual_pivot[col] = resid

    resid_std = residual_pivot.rolling(std_window, min_periods=std_min_obs).std(ddof=1)
    resid_std = resid_std.replace([np.inf, -np.inf], np.nan)
    return residual_pivot, resid_std


def delta_noa_to_assets_accrual_(noa_now_pivot, noa_lag_pivot,
                                 asset_now_pivot, asset_lag_pivot):
    """经营净资产变化 / 两期平均总资产。"""
    return scaled_delta_by_avg_assets_(noa_now_pivot, noa_lag_pivot, asset_now_pivot, asset_lag_pivot)


def parent_pretax_leakage_ratio_(pretax_profit_pivot, parent_profit_pivot,
                                  min_pretax_profit=0.0):
    """归母税前利润流失率 = (税前利润 - 归母净利润) / 税前利润。

    仅保留 pretax_profit > min_pretax_profit 的样本。税前利润非正时，
    从税前利润到归母净利润的“流失比例”会出现经济含义反转，故置空。
    """
    valid_pretax = pretax_profit_pivot.where(pretax_profit_pivot > min_pretax_profit)
    out = (valid_pretax - parent_profit_pivot) / valid_pretax
    return out.replace([np.inf, -np.inf], np.nan)


def operating_capital_fixwc_(fixasset_pivot, acctrcv_pivot, inventories_pivot,
                             acctpayable_pivot, advfromcust_pivot):
    """固定资产+经营营运资本口径。"""
    operating_assets = add_(add_(fixasset_pivot, acctrcv_pivot), inventories_pivot)
    operating_liabs = add_(acctpayable_pivot, advfromcust_pivot)
    return sub_(operating_assets, operating_liabs)


def operating_capital_noa_(totasset_pivot, monetarycap_pivot,
                           acctpayable_pivot, notespayable_pivot,
                           advfromcust_pivot, taxpayable_pivot,
                           curdebt_pivot=None):
    """NOA 口径：总资产 - 货币资金 - 无息流动负债。

    说明
    ----
    默认不减 curdebt；若上层明确要求把某个“流动负债总额/短债”口径并入口径，
    可通过 curdebt_pivot 显式传入。
    """
    non_interest_cur_liab = add_(
        add_(acctpayable_pivot, notespayable_pivot),
        add_(advfromcust_pivot, taxpayable_pivot),
    )
    if curdebt_pivot is not None:
        non_interest_cur_liab = add_(non_interest_cur_liab, curdebt_pivot)
    return sub_(sub_(totasset_pivot, monetarycap_pivot), non_interest_cur_liab)


def incremental_return_ratio_(profit_now_pivot, profit_lag_pivot,
                              capital_now_pivot, capital_lag_pivot):
    """边际回报率：Δ利润 / Δ资本。"""
    delta_profit = sub_(profit_now_pivot, profit_lag_pivot)
    delta_capital = sub_(capital_now_pivot, capital_lag_pivot)
    return div_(delta_profit, delta_capital)


def ratio_delta_(ratio_now_pivot, ratio_lag_pivot=None, lagqnum=4):
    """同一经济比率的差分：R_t - R_{t-lag}。"""
    if ratio_lag_pivot is None:
        ratio_lag_pivot = lag_(ratio_now_pivot, lagqnum)
    return sub_(ratio_now_pivot, ratio_lag_pivot).replace([np.inf, -np.inf], np.nan)


def positive_denominator_div_(pivot_a, pivot_b):
    """只在分母为正时计算 A/B；用于比率定义中分母非正即失去经济含义的场景。"""
    denom = pivot_b.where(pivot_b > 0)
    return div_(pivot_a, denom)


def positive_sum_denominator_ratio_(numerators, denominators):
    """sum(numerators) / sum(denominators)，且仅在合计分母为正时计算。

    用于费用率、收入占比等单一经济比率：分子/分母可由同一会计含义下
    的多条腿合计得到；这里仅处理非正分母的会计有效性，不做门控或奖励。
    输入可为同索引的 Series 或 DataFrame。
    """
    if numerators is None or len(numerators) == 0:
        raise ValueError('numerators must not be empty')
    if denominators is None or len(denominators) == 0:
        raise ValueError('denominators must not be empty')

    numerator_sum = numerators[0].copy()
    for numerator in numerators[1:]:
        numerator_sum = add_(numerator_sum, numerator)

    denominator_sum = denominators[0].copy()
    for denominator in denominators[1:]:
        denominator_sum = add_(denominator_sum, denominator)

    return positive_denominator_div_(numerator_sum, denominator_sum)


def positive_avg_denominator_div_(numerator, denominators, weights=None):
    """分子 / 多期平均正分母。

    用于同一经济分母的多期平滑：先对若干期分母取简单均值或预设权重均值，
    再仅在均值为正时计算比率。这里不做基于历史表现的门控或奖励。
    输入可为同索引的 Series 或 DataFrame。
    """
    if len(denominators) == 0:
        raise ValueError('denominators must not be empty')
    if weights is not None and len(weights) != len(denominators):
        raise ValueError('weights length must match denominators length')
    if len(denominators) == 1:
        return positive_denominator_div_(numerator, denominators[0])
    if weights is None:
        denom = sum(denominators) / float(len(denominators))
    else:
        weight_sum = float(sum(weights))
        if abs(weight_sum) < 1e-12:
            raise ValueError('weights sum must be non-zero')
        denom = sum(d * float(w) for d, w in zip(denominators, weights)) / weight_sum
    return positive_denominator_div_(numerator, denom)


def retention_plowback_ratio_(profit_pivot, dividend_pivot, min_abs_profit=1e-12):
    """盈利留存率：(profit - dividend) / abs(profit)。

    仅剔除 abs(profit) 近零的数值无效样本；不按 profit 正负做门控。
    """
    denom = profit_pivot.abs().where(profit_pivot.abs() > min_abs_profit)
    retained_profit = sub_(profit_pivot, dividend_pivot)
    return div_(retained_profit, denom)


def retention_plowback_change_(profit_pivot, dividend_pivot, lag_months=6, min_abs_profit=1e-12):
    """盈利留存率变化：R_t - R_{t-lag}，R=(profit-dividend)/abs(profit)。"""
    ratio_now = retention_plowback_ratio_(
        profit_pivot=profit_pivot,
        dividend_pivot=dividend_pivot,
        min_abs_profit=min_abs_profit,
    )
    return ratio_delta_(ratio_now, lagqnum=lag_months)


def retained_profit_asset_intensity_(profit_pivot, dividend_pivot, asset_pivot):
    """留存盈利资产强度：(profit - dividend) / total_assets。

    仅剔除 total_assets <= 0 的会计分母无效样本；不加收益门控或奖励。
    """
    retained_profit = sub_(profit_pivot, dividend_pivot)
    denom = asset_pivot.where(asset_pivot > 0)
    return div_(retained_profit, denom)


def retained_profit_asset_intensity_change_(profit_pivot, dividend_pivot, asset_pivot, lag_months=4):
    """留存盈利资产强度变化：R_t - R_{t-lag}，R=(profit-dividend)/total_assets。"""
    ratio_now = retained_profit_asset_intensity_(
        profit_pivot=profit_pivot,
        dividend_pivot=dividend_pivot,
        asset_pivot=asset_pivot,
    )
    return ratio_delta_(ratio_now, lagqnum=lag_months)


def max2_(pivot_a, pivot_b):
    return pd.DataFrame(
        np.fmax(pivot_a.values, pivot_b.values),
        index=pivot_a.index,
        columns=pivot_a.columns,
    )


def min2_(pivot_a, pivot_b):
    return pd.DataFrame(
        np.fmin(pivot_a.values, pivot_b.values),
        index=pivot_a.index,
        columns=pivot_a.columns,
    )


# -------------------------
# 截面变形
# -------------------------

def cs_rank_(pivot, pct=True):
    return pivot.rank(axis=1, pct=pct, na_option='keep')


def cs_pctrank_(pivot, min_count=30):
    """截面百分位，少于 min_count 个有效样本则整期置空。"""
    rank_pivot = cs_rank_(pivot, pct=False)
    valid_count = pivot.notna().sum(axis=1)
    denom = valid_count.sub(1).replace(0, np.nan)

    out = rank_pivot.sub(1).div(denom, axis=0)
    out = out.where(valid_count.ge(min_count), np.nan, axis=0)
    return out


def cs_rank_diff_(pivot_a, pivot_b, pct=True):
    return cs_rank_(pivot_a, pct=pct) - cs_rank_(pivot_b, pct=pct)


def cs_pctrank_vals_(vals, min_count=30):
    """一维截面向量转百分位，少于 min_count 个有效样本则全置空。"""
    vals = np.asarray(vals, dtype=float)
    out = np.full(vals.shape, np.nan, dtype=float)
    valid = ~np.isnan(vals)
    n_valid = int(valid.sum())
    if n_valid < max(2, min_count):
        return out

    series = pd.Series(vals)
    rank = series.rank(method='average', pct=False)
    out = ((rank - 1) / (n_valid - 1)).to_numpy(dtype=float)
    out[~valid] = np.nan
    return out


def cs_zscore_(pivot, ddof=1, fillna=None):
    row_mean = pivot.mean(axis=1)
    row_std = pivot.std(axis=1, ddof=ddof)
    out = pivot.sub(row_mean, axis=0).div(row_std.replace(0, np.nan), axis=0)
    if fillna is not None:
        out = out.fillna(fillna)
    return out


def _mad_bounds_(row, mad_n=3.0, K=1.483):
    vals = row.to_numpy(dtype=float)
    if np.all(np.isnan(vals)):
        return np.nan, np.nan, np.nan

    median_value = np.nanpercentile(vals, 50)
    mad = np.nanpercentile(np.abs(vals - median_value), 50)
    lower = median_value - mad_n * K * mad
    upper = median_value + mad_n * K * mad
    return mad, lower, upper


def cs_mad_clip_(pivot, mad_n=3.0, K=1.483):
    def _clip_row(row):
        mad, lower, upper = _mad_bounds_(row, mad_n=mad_n, K=K)
        if pd.isna(mad) or mad < 1e-12:
            return row
        return row.clip(lower=lower, upper=upper)

    return pivot.apply(_clip_row, axis=1)


def cs_winsor_mad_zscore_(pivot, mad_n=3.0, K=1.483, fillna=0):
    clipped = cs_mad_clip_(pivot, mad_n=mad_n, K=K)
    return cs_zscore_(clipped, fillna=fillna)


def rolling_window_vals_(pivot, window, include_current=True):
    """滑动窗口生成器：逐期返回 (cur_date, curr_vals, hist_vals)。"""
    if window <= 0:
        raise ValueError('window must be positive')

    date_index = pivot.index.tolist()
    n_dates = len(date_index)
    start = window - 1 if include_current else window
    for i in range(start, n_dates):
        cur_date = date_index[i]
        curr_vals = pivot.iloc[i].values
        if include_current:
            hist_vals = pivot.iloc[i - window + 1:i + 1].values
        else:
            hist_vals = pivot.iloc[i - window:i].values
        yield cur_date, curr_vals, hist_vals


def cross_section_rank_diff_(df, xcol, ycol, pct=True, method='average'):
    """长表版本的同日截面 rank(x) - rank(y)。"""
    out = []
    for date, g in df.groupby('date'):
        gg = g[['Stkcd', xcol, ycol]].dropna().copy()
        if gg.empty:
            continue
        gg['sig'] = (
            gg[xcol].rank(method=method, pct=pct)
            - gg[ycol].rank(method=method, pct=pct)
        )
        gg['date'] = date
        out.append(gg[['date', 'Stkcd', 'sig']])

    if not out:
        return pd.DataFrame(columns=['date', 'Stkcd', 'sig'])
    return pd.concat(out, axis=0, ignore_index=True)


def cross_section_reg_resid_(df, ycol, xcol, include_intercept=True, min_count=3):
    """长表版本的同日截面回归残差；xcol 可为单列或多列。"""
    xcols = [xcol] if isinstance(xcol, str) else list(xcol)
    out = []
    for date, g in df.groupby('date'):
        usecols = ['Stkcd', ycol] + xcols
        gg = g[usecols].dropna().copy()
        if gg.shape[0] < min_count:
            continue

        y = gg[ycol].to_numpy(dtype=float)
        x = gg[xcols].to_numpy(dtype=float)
        X = np.column_stack([np.ones(len(gg)), x]) if include_intercept else x
        beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        gg['sig'] = y - X @ beta
        gg['date'] = date
        out.append(gg[['date', 'Stkcd', 'sig']])

    if not out:
        return pd.DataFrame(columns=['date', 'Stkcd', 'sig'])
    return pd.concat(out, axis=0, ignore_index=True)


def make_industry_share_(base_df, value_col, industry_df, industry_col='indcode'):
    """长表版本：个股值 / 同日同行业求和。"""
    merged = pd.merge(
        base_df[['date', 'Stkcd', value_col]],
        industry_df[['date', 'Stkcd', industry_col]],
        on=['date', 'Stkcd'],
        how='inner',
    )
    merged = merged.dropna(subset=[value_col, industry_col]).copy()
    merged['industry_sum'] = merged.groupby(['date', industry_col])[value_col].transform('sum')
    merged.loc[merged['industry_sum'].abs() <= 1e-12, 'industry_sum'] = np.nan
    merged['sig'] = merged[value_col] / merged['industry_sum']
    return merged[['date', 'Stkcd', 'sig']].copy()


def row_zscore_(df, current_col, history_cols, ddof=1, min_obs=2):
    """行内标准化：用 history_cols 的均值/标准差标准化 current_col。"""
    out = df.copy()
    hist = out[history_cols]
    out['hist_mean'] = hist.mean(axis=1)
    out['hist_std'] = hist.std(axis=1, ddof=ddof)
    valid_obs = hist.notna().sum(axis=1)
    out.loc[valid_obs < min_obs, 'hist_std'] = np.nan
    out.loc[out['hist_std'].abs() <= 1e-12, 'hist_std'] = np.nan
    out['sig'] = (out[current_col] - out['hist_mean']) / out['hist_std']
    return out


yoy_abs_pivot_ = yoy_abs_
yoy_raw_pivot_ = yoy_raw_
cs_pctrank_pivot_ = cs_pctrank_
cross_section_pctrank_ = cs_pctrank_vals_


__all__ = [
    'extend_periods_', 'pivot_vals_', 'pivot_to_long_', 'pivot_and_ffill_',
    'lag_', 'diff_', 'abs_', 'neg_', 'sign_', 'sqrt_abs_', 'log_abs1p_',
    'rolling_mean_', 'rolling_std_', 'rolling_sum_', 'rolling_min_', 'rolling_max_', 'rolling_median_', 'rolling_zscore_',
    'yoy_abs_', 'yoy_raw_', 'rolling_ols_beta_',
    'add_', 'sub_', 'mul_', 'div_', 'div_abs_',
    'cash_confirmed_earnings_to_assets_', 'receivable_accrual_intensity_', 'per_employee_efficiency_',
    'avg_positive_', 'scaled_delta_by_avg_assets_',
    'operating_working_capital_clean_', 'operating_working_capital_accrual_clean_',
    'working_capital_accruals_dd_', 'rolling_multivariate_residual_std_',
    'delta_noa_to_assets_accrual_',
    'operating_capital_fixwc_', 'operating_capital_noa_', 'incremental_return_ratio_', 'ratio_delta_', 'positive_denominator_div_',
    'retention_plowback_ratio_', 'retention_plowback_change_',
    'max2_', 'min2_',
    'cs_rank_', 'cs_pctrank_', 'cs_rank_diff_', 'cs_pctrank_vals_', 'cs_zscore_', 'cs_mad_clip_', 'cs_winsor_mad_zscore_',
    'rolling_window_vals_',
    'cross_section_rank_diff_', 'cross_section_reg_resid_', 'make_industry_share_', 'row_zscore_',
    'yoy_abs_pivot_', 'yoy_raw_pivot_', 'cs_pctrank_pivot_', 'cross_section_pctrank_',
]
