# 价格动量因子构造规则：剔除近期 ~20 交易日

## 核心规则

**价格动量因子在 t 时刻的取值，不得包含 t 到 t-20 的收盘价数据。** 即计算窗口必须跳过最近约 1 个月（20 个交易日）。

学术依据：Jegadeesh (1990) 指出短期价格收益率存在显著的反转效应。如果动量因子包含近期价格，信号会被短期反转污染，导致动量策略失效。

## 正确公式

```
MOM_{t} = Ret_{t-20, t-260}
```

即：用 t-20 日的收盘价到 t-260 日的收盘价计算累计收益，跳过 t 到 t-19 的 20 个交易日。

## 框架中的正确实现

`${PROJECT_ROOT}/util/func.py` 中的 `price_path_efficiency_()` 函数已内置 skip 机制：

```python
def price_path_efficiency_(price_pivot, skip_days, lookback_days, min_obs=None):
    log_price = log_price_(price_pivot)
    log_ret = diff_(log_price, n=1)
    # 净位移从 t-skip_days 到 t-skip_days-lookback_days
    net_disp = sub_(lag_(log_price, n=skip_days), lag_(log_price, n=skip_days + lookback_days))
    # 路径长度从 t-skip_days 回溯 lookback_days 期
    path_len = rolling_sum_(abs_(lag_(log_ret, n=skip_days)), window=lookback_days, min_periods=min_obs)
    return div_(net_disp, path_len)
```

- `skip_days`：跳过的交易日数（默认 20，即约 1 个月）
- `lookback_days`：回溯窗口长度（默认 240，即约 12 个月）

调用示例（R52 PPEM codex）：
```python
price_path_efficiency_(close_pivot, skip_days=20, lookback_days=240, min_obs=160)
```

计算结果：`[ln(P_{t-20}) - ln(P_{t-20-240})] / Σ|ln(P_i/P_{i-1})|`，完全跳过 t 到 t-19。

## 简单动量（ret20/ret60）的实现规则

如果后续需要实现标准价格动量因子（如过去 12 个月排除最近 1 个月的累计收益）：

```
ret_excl_recent = close_{t-20} / close_{t-260} - 1
```

**绝对不允许**：
```
ret_all = close_t / close_{t-240} - 1  # ❌ 包含近期价格
```

## 不适用的因子类型

本规则仅适用于**价格动量因子**——以股票收盘价/收益率为输入的因子。以下类型不受此规则限制：

- **财务基本面因子**（如毛利率、费用率、资产周转率等使用财务报表数据的因子）—— 信号时间戳已经是财务数据在 month-end 可用的时间点，天然与近期价格无关
- **财务比率动量**（如 Δ4Q monetarycap/curdebt）—— 不涉及价格数据，使用会计期间对齐

## 审查检查点

evaluator 在审查价格动量因子时，必须检查：

1. [ ] 因子公式是否显式跳过最近 ~20 个交易日
2. [ ] 若使用 `price_path_efficiency_`，`skip_days` 参数是否 >= 20
3. [ ] 若手动实现，是否确认了 t 时刻的值不包含 t 到 t-19 的收盘价

## 用户确认（R62 轮次经验）

用户于 2026-07-23 明确确认此规则，并指出：
- 这是动量因子的固有特征，不是可选优化
- R52 PPEM 的 `price_path_efficiency_(skip_days=20)` 已正确实现
- 后续所有价格动量因子必须沿用此规则
