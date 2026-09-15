# quality-gap 家族批量回测与保存规范

## 适用场景
同一家族因子一次落多个 `*_codex.py`，需要统一保存回测产物。

## 建议产物
- `RankIC.csv`
- `groupret.csv`
- `lsdf.csv`
- `metrics.json`
- `summary.csv`

## 规则
- 每个因子保留独立 facname 与参数记录。
- 批量脚本只负责调度与落盘，不要替代叶子文件的定义职责。
- 汇总表必须能回指到具体 `*_codex.py` 路径。
