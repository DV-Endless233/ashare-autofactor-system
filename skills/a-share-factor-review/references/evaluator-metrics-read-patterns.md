# Evaluator 读取回测指标时的 key 模式参考

## 背景

不同轮次的 dvcoder 在编写 codex 和生成 metrics.json 时使用了不一致的 key 命名约定。2026-07-28 的 evaluator_passed/ 扫表过程中发现以下变体：

## 常见 key 命名变体

| 语义 | 常见 key 名 | 示例轮次 |
|------|------------|---------|
| 均值 IC | `RankICmean`, `rankic_mean`, `RankICMean` | R110 用 `RankICmean`，R73 用 `rankic_mean` |
| IC IR | `RankICIR`, `rankic_ir` | R107 用 `RankICIR`，cf2fa 用 `rankic_ir` |
| 多空收益 | `lsret`, `ls_ret`, `LongShortRet` | 大部分用 `lsret` |
| 通过计数 | `pass_count`, `hit_count`, `threshold_hits` | R100 用 `hit_count`，cf2fa 用 `pass_count` |

## JSON 文件位置

不同因子的 metrics.json 可能出现在下列任意位置：

```
review_queue/<facname>/
├── backtest/metrics.json              ← R110 风格
├── backtest/<variant>_metrics.json    ← 多变体风格（round34/35）
├── backtest/<variant>_comparison.json ← 汇总比较文件（round34/35）
├── result/metrics.json                ← R103/R107/R113 风格
├── result/dvcoder_handoff.md          ← R93/R88 风格（dash 格式 "- RankICmean: 0.xxxx"）
└── result/summary_metrics.json        ← R73 风格
```

## evaluator_passed/ 迁移后遗留

迁移到 evaluator_passed/ 后，有些因子的 backtest 目录未复制（round34/35、R60、R73、R74、R71 的 op2ev/gp2ev），指标需到原始 review_queue/ 下查找。

## 推荐读取顺序

1. `evaluator_passed/<facname>/backtest/*metrics*.json`（若有）
2. `evaluator_passed/<facname>/result/metrics.json`
3. `evaluator_passed/<facname>/result/dvcoder_handoff.md`（dash 格式）
4. `review_queue/<facname>/backtest/*.json`
5. `review_queue/<facname>/result/metrics.json`
6. `review_queue/<facname>/result/summary_metrics.json`
