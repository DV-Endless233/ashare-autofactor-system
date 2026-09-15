# 中性化不一致排查

适用场景：
- raw 因子值已经和 textbook / benchmark 基本一致
- 但中性化后因子值、RankIC 或分组收益仍和原结果不一致

## 本次沉淀的排查顺序
1. **先锁定 raw 是否一致**
   - 不要直接看回测结果。
   - 先逐点比较 raw 因子值，确认数学定义、分母口径、滞后参数一致。
   - 对盈余质量，`cfo_sq_op_sq2totasset = (CFO_sq - OP_sq) / TotalAsset`，且是**正向因子**，不要再做 sign flip。

2. **再锁定中性化输入矩阵是否一致**
   - 比较的不只是 `factor` 本身，还包括：
     - 股票池
     - 行业分类
     - Size
     - BP
     - Growth
   - 如果这些暴露矩阵不同，`barra_ind_neut_` 残差必然不同，即使 raw 因子完全一致。

3. **优先检查 Growth 暴露口径**
   - 本项目里，benchmark 脚本
     `${PROJECT_ROOT}/factor_replicate_outputs/single_factor_missing_demo_weekly_ind_size_bp_growth/build_weekly_ind_size_bp_growth_backtest.py`
     的 `Growth` 不是直接来自 textbook `sgrobarra_5` / `egrobarra_5` 缓存。
   - 它使用自定义 `build_growth_raw_()`，基于 `op_ttm` / `nptopc_ttm` 的 lagged 文件重构 growth proxy。
   - 因此：
     - 若你拿 textbook `sgrobarra_5` / `egrobarra_5` 去做中性化，
     - 再和 benchmark 脚本结果比，
     - 即使方向一致、相关性很高，数值也可能系统性不同。

4. **股票池差异要量化，不要猜**
   - 先看每天缺多少只。
   - 如果只是少量差异（例如每天只差几只），通常不是主因；
   - 如果残差整体都不同，优先回到风格暴露口径，而不是先怀疑 RankIC_ 或 group_test_。

## 这次任务得到的判别经验
- `raw` 一致，不代表 `neutralized factor` 一致。
- `neutralized factor` 不一致，优先判定问题在：
  - 风格暴露构造口径
  - 股票池口径
  - 行业映射口径
- 不要过早把锅甩给 `RankIC_()` 或 `group_test_()`。

## 推荐输出
当用户问“问题在因子生成还是回测”时，按下面顺序给结论：
1. raw 因子是否一致
2. 中性化输入（pool / ind / Size / BP / Growth）是否一致
3. 中性化后因子值是否一致
4. 只有前三步都一致，才进一步查回测链路
