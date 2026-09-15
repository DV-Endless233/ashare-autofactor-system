# 单因子拆解指南（"归零"技术）

当多轮迭代产生复杂的 multi-component 因子结构（如 `cash_z + quality_z + interaction - penalty`），且 evaluator 判定为多因子组合违规时，使用本拆解技术。

## 适用场景

- dvcoder 已迭代 3+ 轮但所有因子均为 multi-component 结构
- 因子表达式包含 2+ 个独立经济学含义的 zscore 分量线性叠加
- 无法用一个单一经济学名称概括因子

## 拆解步骤

### 第一步：识别所有原始比率

从复杂表达式中提取最底层的原始财务比率。每条比率是**除法运算**：

```
复杂结构: cash_z + 0.75*op_margin_z + 0.5*asset_turnover_z + interaction - penalty
拆解为:
  ① cash_margin      = cfo / revenue        (现金利润率)
  ② op_margin        = opprofit / revenue   (营业利润率)
  ③ asset_turnover   = revenue / asset      (资产周转率)
  ④ cash_opprofit    = cfo / opprofit       (现金/营业利润比率)
```

### 第二步：逐一独立回测

每个比率为一个独立的单因子 codex，不加门控/不加组合/不加 unexpected/zscore：
- 直接加载原始字段 → 做除法 → winsorize → 中性化 → 回测
- 口径统一：月频, 10组, lntotcap_ind_neut_

### 第三步：识别最强单因子

对比所有原始比率的 RankICmean / RankICIR / lsret，选出最强的一个：
- 如果某个单因子 ICmean>0.015 且 IR>1.5 → 以此为基础做单因子优化
- 如果都未达标 → 选 ICmean 最高的方向进一步探索

### 第四步：温和的二因子论证

如果单个比率都不达标，可尝试二因子组合，但必须：
- **论证权重**（如 `cash_margin + 0.5*asset_turnover` 的 0.5 必须有经济学理由，而非网格搜索最优值）
- **禁止 zscore 后线性加权**（那是多因子组合的典型表现）
- **禁止网格搜索权重**（那是过拟合）

## 典型输出

```
因子               ICmean       IR        lsret      结论
cash_margin       0.0148      1.90      0.059      ✅ 最强
op_margin         0.0092      0.67      0.034      ❌ 弱
asset_turnover    0.0065      0.49      0.022      ❌ 弱
cash_opprofit     0.0117      0.89      0.032      ⚠️ 中等
```

## 什么时候不做

- 如果原始比率本身就是经济学上无意义的（如 cfo × revenue / asset — 该结构既不是效率也不是利润率）
- 如果所有原始比率 IC 方向与经济含义矛盾且无法解释

## 参考

Evaluator 审查结论表明：**多因子组合是多轮迭代中最常见的否决原因**。dvcoder 构建新因子前应始终先问"这个因子我能用一个经济学名称概括吗？"
