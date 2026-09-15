# codex 三层迁移清单

## 用途
把旧 thin-shell `*_codex.py`、旧 helper 依赖、旧父类封装迁到当前三层结构。

## 迁移顺序
1. 确认原始输入属于 rawsig 层。
2. 把通用算子迁到 `func.py` 或 util 公共层。
3. 让叶子层显式声明 `initdataclass_` 与 `sigconstructperiods_`。
4. 补齐标准 `__main__` 尾部。

## 验收
- 数学定义不变。
- 共用逻辑不再藏在旧 helper。
- 文件职责清楚，能单独审阅。
