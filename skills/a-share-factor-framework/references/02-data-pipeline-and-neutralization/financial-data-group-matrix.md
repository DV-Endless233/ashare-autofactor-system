# Financial Data Group Mapping

When loading financial data via family func helpers, different groups require different functions:

## `_pivot_atomic` (from `reinvestment_quality_family_func`)

Supports: `cf`, `capexp`, `rdexp`, `asset`, `debt`, `findebt`, `expense`

```python
cfo      = _pivot_atomic('cfo', periods, group='cf',      signame='cfo',      fiscaltype='ttm', lagqnum=0)
capexp   = _pivot_atomic('capexp', periods, group='capexp', signame='capexp',   fiscaltype='ttm', lagqnum=0)
rdexp    = _pivot_atomic('rdexp', periods, group='rdexp',   signame='rdexp',    fiscaltype='ttm', lagqnum=0, ynum=0)
asset    = _pivot_atomic('asset', periods, group='asset',    signame='totasset', fiscaltype='bs',   lagqnum=0)
totdebt  = _pivot_atomic('totdebt', periods, group='debt',   signame='totdebt',  fiscaltype='bs',   lagqnum=0)
findebt  = _pivot_atomic('findebt', periods, group='findebt', signame='findebt',  fiscaltype='bs',   lagqnum=0)
finexp   = _pivot_atomic('finexp', periods, group='expense', signame='finexp',   fiscaltype='ttm',  lagqnum=0)
cff      = _pivot_atomic('cff', periods, group='cf',      signame='cff',      fiscaltype='ttm', lagqnum=0)
```

## `_pivot_cash_quality_atomic` (from `round7_cash_quality_family_func`)

Supports: `income`, `profit`

```python
revenue   = _pivot_cash_quality_atomic('revenue', periods, group='income', signame='opinc',   fiscaltype='ttm', lagqnum=0)
opprofit  = _pivot_cash_quality_atomic('opprofit', periods, group='profit', signame='op',      fiscaltype='ttm', lagqnum=0)
netprofit = _pivot_cash_quality_atomic('netprofit', periods, group='profit', signame='nptopc',  fiscaltype='ttm', lagqnum=0)
```

## Stock code format

All pivot data frames have stock codes as column names with `.SZ`/`.SH` suffix (e.g. `'000001.SZ'`). The stock pool (`getstkpool_`) also uses the same format. When merging, keep the string format with suffix — do NOT strip `.SZ`/`.SH` or cast to int.

## Common errors

- `ValueError: unsupported group: income` — using `_pivot_atomic` for income/profit data; use `_pivot_cash_quality_atomic` instead.
- `ValueError: invalid literal for int() with base 10: '000001.SZ'` — trying `.astype(int)` on stock codes with suffix. Keep as string.
