# percentile-rank growth 实现口径

## 定义
先构造 growth，再转成 percentile / rank 形式，强调截面相对位置而不是原始幅度。

## 适用场景
- 原始 growth 极值很多。
- 不同财务口径量纲差异较大。
- 更关心排序稳定性而非数值大小。

## 风险
- rank 化后可能损失幅度信息。
- 若截面样本太小，percentile 不稳定。
- 与已做 zscore/rank 的后续步骤重复时要避免双重变换。
