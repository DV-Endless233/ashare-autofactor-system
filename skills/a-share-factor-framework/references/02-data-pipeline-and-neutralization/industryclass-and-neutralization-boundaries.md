# industryclass 调用边界与中性化责任归属

## 结论
- `util/industryclass.py` 的职责是生成股票-行业归属面板，核心输出为 `date, Stkcd, indcode, indname, indalias, idxcode`。
- `industryclass.py` **不做中性化回归**。
- 框架里真正把行业归属拿去做行业中性化的核心模块是 `util/neutfactorclass.py`。

## 核心调用链
1. 上层因子/回测/组合脚本初始化 `neutfactorclas_()`。
2. 调 `init_size_indclass_()`，内部绑定：
   - `mktcap_sig_(facnameuse='totcap')`
   - `industryclass_('citics_1')`
3. 在 `lntotcap_ind_neut_()` 或 `barra_ind_neut_()` 中：
   - `self.indclass.getfac_(periods)` 读取行业归属
   - 按 `indname` 展开行业哑变量
   - 与市值/Barra 暴露一起做横截面回归
   - 输出残差因子

## 关键源码位置
- `util/neutfactorclass.py`
  - `init_size_indclass_()`：行业源绑定在这里
  - `lntotcap_ind_neut_()`：市值+行业中性化
  - `barra_ind_neut_()`：Barra 风格 + 行业中性化
- `util/industryclass.py`
  - 只负责行业标签/映射面板，不包含收盘价、收益率、中性化回归逻辑

## 明确使用该链路做中性化的上层模块
- `util/wficbacktest.py`
  - `neutralize=True` 时调用 `barra_ind_neut_()`
- `util/mfe.py`
  - alpha 进入 `barra_ind_neut_()` 做风格+行业中性化
- `util/rawsigs/_codex_utils/weekly_textbook_standard.py`
  - 周频 textbook 标准路线调用 `barra_ind_neut_()`
- `util/rawsigs/*_codex.py`
  - 大量 codex 原子/复合因子通过 `lntotcap_ind_neut_()` 间接使用 `industryclass.py`

## 需要区分：使用 industryclass ≠ 做中性化
以下模块虽然调用 `industryclass.py`，但职责不是中性化回归：
- `util/nm4facs.py`：行业指数价格/相对行业构造
- `util/riskmodelthmsigsclass.py`：行业内清洗、缺失填补、风格处理
- `util/utilfun.py`：行业分布、行业内排序、行业分位填充
- `util/rawsigs/_codex_utils/generic_factor_ops.py`：行业映射、行业占比型辅助函数

## 易错点 / Pitfalls
- 不要把 `industryclass.py` 误判为“收益型因子构造器”或“中性化器”；它只是行业归属面板源。
- 真正的行业中性化责任应追到 `neutfactorclass.py`，不是追 `industryclass.py` 本体。
- 看到 `idxcode` 不代表这里已经进入行业收益计算；很多地方只是把 `idxcode` 当标签或后续 join 键。
- 排查错误 `idxcode` 映射链路污染范围时，要优先看：
  1. 谁调用了 `industryclass.py`
  2. 谁进一步拿输出的 `idxcode` 去连行业行情/收益
  3. 谁只是把 `indname/indcode` 当分类标签
