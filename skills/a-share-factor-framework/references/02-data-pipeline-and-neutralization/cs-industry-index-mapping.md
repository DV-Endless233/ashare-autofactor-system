# 中证行业代码与 indexcontrastsector 映射口径

## 适用场景

当任务涉及：

- `asharecsindustriesclass.csv` 中的 `CS_IND_CODE` / `CS_IND4_CODE`
- `indexcontrastsector.h5` 中的 `idxcode` / `indcode`
- 试图把中证行业历史表补成“可直接对接指数代码”的字段

先参考本 note。

## 结论

**默认结论：不能直接映射，也不应靠名称兜底匹配。**

## 原因

1. `CS_IND_CODE` / `CS_IND4_CODE` 是中证行业旧 10 位代码。
2. `indexcontrastsector.h5` 的 `indcode` 为另一套更长编码，二者不能直接等值匹配。
3. 即使先通过 `ashareindustriescode.feather` 做旧码转新码，也不能稳定命中 `indexcontrastsector.indcode`。
4. `indexcontrastsector.h5` 混有多类行业/指数体系，`idxname` / `indname` 不是唯一键，名称匹配会把非目标体系混进来。

## 默认处理原则

- **不要**把 `CS_IND_CODE` / `CS_IND4_CODE` 直接 join 到 `indexcontrastsector.indcode`。
- **不要**通过行业中文名称做模糊或半手工回填。
- 若需求只是做行业中性化、行业 dummy、行业分组，优先使用当前框架里已经稳定的行业分类来源与调用链。
- 若需求确实要落“行业对应指数代码”，必须先说明该代码对应的**目标体系**与**唯一主键**，再设计单独映射表。

## 可接受的下一步

### A. 只是要行业分类

直接用当前框架已有的行业分类输入，不新增 `idxcode` 回填动作。

### B. 必须生成行业指数映射

先补齐下面 3 个问题：

1. 目标是中证行业指数、Wind 行业指数，还是别的体系。
2. 唯一主键是什么：旧码、新码、官方指数代码，还是单独维护的映射表。
3. 时间维度是否要保留历史变更；若要，必须做成时点映射，不是静态表。

## 检查清单

- 编码长度是否一致。
- 编码体系是否同源。
- 名称是否跨体系重名。
- 是否存在时点变更问题。
- 最终产物是否有可复核的唯一键，而不是“靠名字猜到大概对”。
