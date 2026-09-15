# Standalone Single-Factor Backtest Script Pattern ("归零轮" 脚本)

## When to use

Instead of building a full `*_codex.py` (stkfactor subclass + initdataclass + sigconstructperiods), write a standalone script when:

1. You need to quickly test multiple raw ratios as single factors
2. The factor is a simple ratio (no rolling transforms, no expected/unexpected, no gates)
3. You want a comparison table of multiple candidates

## Script pattern

```python
import sys, pandas as pd
from pathlib import Path

# Path setup
_PROJ = '${PROJECT_ROOT}'
if _PROJ not in sys.path:
    sys.path.insert(0, _PROJ)

# Data loading: inject family func paths
from reinvestment_quality_family_func import _pivot_atomic, _safe_div
from round7_cash_quality_family_func import _pivot_cash_quality_atomic

from util.WindTradingDay import WindTradingDay_
from util.getStkPool import getstkpool_
from util.utilfun import winsomadsort_
from util.neutfactorclass import neutfactorclas_
from util.stkfactorbacktest import Stkfactorbacktest_

# 1. Load data as pivot (wide format: index=date, columns=Stkcd)
cfo = _pivot_atomic('cfo', periods, group='cf', signame='cfo', fiscaltype='ttm', lagqnum=0)
revenue = _pivot_cash_quality_atomic('revenue', periods, group='income', signame='opinc', ...)

# 2. Compute ratio (still in pivot format)
ratio = _safe_div(cfo, revenue)

# 3. Convert to long format (date, Stkcd, sig) — KEEP .SZ/.SH suffix
long = ratio.reset_index().melt(id_vars=['date'], var_name='Stkcd', value_name='sig')
long['Stkcd'] = long['Stkcd'].astype(str)  # don't strip .SZ/.SH

# 4. Merge with stock pool
stkpool = getstkpool_(periods=periods, listtdays=240, noSTtdays=60)
sigdata = pd.merge(stkpool, sig_long, on=['date', 'Stkcd'], how='inner')

# 5. Winsorize
sigdata['sig'] = sigdata.groupby('date')['sig'].transform(
    lambda x: winsomadsort_(x, mad_n=5))

# 6. Neutralize
neuclass = neutfactorclas_()
neuclass.init_size_indclass_()
neusig = neuclass.lntotcap_ind_neut_(
    sigdata[['date', 'Stkcd', 'sig']], Ifsize=True, Ifind=True)

# 7. Backtest
btclass = Stkfactorbacktest_(
    stksig=neusig.dropna(), startdt='20100101', enddt='20260401',
    freq='m', groupnum=10)
RankIC, RankICmean, RankICIR = btclass.RankIC_()
groupret, lsret, sigret, stksig_group, lsdf = btclass.group_test_()
```

## Running

Use `terminal(background=True, notify_on_complete=True)` for backtests (delegate_task times out at 600s):

```bash
cd ${PROJECT_ROOT}/factor_replicate_outputs/review_queue/<round_dir> && \
PYTHONPATH=${PROJECT_ROOT} /Users/dv/.local/bin/python3.11 <script.py> 2>&1
```

## Contrast with codex pattern

| Aspect | Standalone script | Full codex |
|--------|------------------|------------|
| Speed | Fast, 1 file | Requires rawsig registration |
| Reusability | Low (one-off) | High (stkfactor subclasses) |
| When | Exploratory, "归零轮", comparison | Production, framework integration |
