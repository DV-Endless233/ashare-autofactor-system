# growth operator 方法学与实现边界

## 目标

把 growth 家族相关的历史 note 收敛成一份可复用的 canonical 入口，只保留：

- 方法学来源如何吸收
- operator 怎么分层
- 哪些差异属于输入差异，哪些属于算子差异
- 在当前三层框架里应该落到哪里

不保留任何未经当前框架复核的经验排序结论。

## 总原则

**只学方法，不套结论。**

外部 research note 可以提供：

- operator 名称
- 公式定义
- 参数候选
- 对 level / ratio / yoy / qoq / residual 的适用性

但不能直接继承：

- 哪个 operator 在样本里最好
- 哪个窗口必胜
- 哪个财务域天然优于别的财务域

这些都必须回到本框架重新验证。

## growth operator 的最小拆法

### 一阶：增长幅度

常见包括：

- 百分比增速
- 复合增速
- 百分位排名增速
- 预期外增速
- 稳健增速
- 复合稳健增速

### 二阶：增长加速度

常见包括：

- 加速度
- 复合加速度

## 三层落地边界

### 原子层：`util/rawsigs/`

负责：

- 选择输入字段
- 财报口径整理
- 生成底层原子序列

### 共享工具层：`func.py` + `util/` 非 rawsig 模块

负责：

- operator 公式
- 通用窗口处理
- 共享变换
- 跨因子可复用的 growth 计算逻辑

### 叶子层：`*_codex.py`

负责：

- 组装输入
- 选择 operator / 参数
- 调用共享函数
- 管缓存与最小 `__main__`

## 选择 operator 前先判断什么

1. 输入是 level、ratio、yoy、qoq 还是 residual。
2. 是否需要长窗口；短窗口是否会让分母或标准差不稳定。
3. 当前 operator 和已有 operator 是否只是同义改写。
4. 经济学含义是“增长幅度”、"增长相对位次"，还是“增长斜率/加速度”。
5. 因子家族扩展时，差异应体现在：
   - 输入原子
   - 参数
   - shared operator
   而不是每个叶子各写一套主流程。

## 不要再做的事

- 不要把 growth 家族重新包成 `_codex_utils` 第四层。
- 不要为了统一风格先造一棵父类森林。
- 不要把不同 operator 的差异塞进叶子文件里分支爆炸。
- 不要把 TTM / SQ、profit / income / cashflow 的输入差异，误写成 operator 差异。

## 实现顺序建议

1. 先明确原子输入与财报频率。
2. 再确认 operator 公式与参数。
3. 先产出最小可运行叶子。
4. 回测后再判断是否需要扩同家族 operator 对照。
5. 若发现共享逻辑重复，再上提到共享工具层。

## 关联 references

- `compound-growth-implementation.md`
- `compound-growth-acceleration-implementation.md`
- `unexpected-growth-implementation.md`
- `yoy-robust-growth-implementation.md`
- `percentile-rank-growth-implementation.md`
- `divide-regdivide-architecture.md`
- `fullparam-technical-extension.md`
