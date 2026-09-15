# auto factor round 治理规则

## 核心原则
自动 round 产生的是**候选研究资产**，不是最终因子库。

## 隔离要求
- round 目录单独保存 hypothesis、代码、因子值、回测结果。
- 未经 evaluator 与人工审查，不进入最终库。
- 失败因子也要留失败归因，但不要污染正式目录。

## 最小交付
- hypothesis 文档
- `*_codex.py`
- 因子值文件
- quick backtest 摘要
- 下一步动作
