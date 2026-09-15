# manual benchmark 与 raw generation 不一致排查

## 适用场景
手工 benchmark 结果与 raw generation 结果不一致时，用于缩小问题范围。

## 排查顺序
1. 原始字段读取是否一致。
2. 对齐日期与股票代码。
3. 手工算式与程序算式是否完全等价。
4. `ffill`、merge、去极值、中性化是否多做或少做。
5. 回测收益口径是否一致。

## 原则
- 先对 raw 截面，再对 neutralized 截面，再对回测指标。
- 每一步都保存中间产物，避免只比最终结果。
