# `codex_utils` → textbook 标准链替换规则

## 适用场景
当旧实现依赖 `_codex_utils`、共享父类薄壳或一次性 helper，需要改回当前 textbook + 三层结构时使用。

## 替换原则
- 旧 helper 负责**算子**的，回收到 `func.py` 或 util 公共层。
- 旧 helper 负责**流程**的，直接展开回标准尾部：`getfac_ -> getstkpool_ -> 标准化 -> neutfactorclas_ -> Stkfactorbacktest_`。
- 旧 helper 负责**命名/缓存**的，保留在叶子层最小实现，不再抽象成黑盒。

## 不该继续保留的旧模式
- `dividefactorclass_` / `regdividefactorclass_` 薄壳包所有逻辑。
- 叶子文件只剩两三行继承声明，真实逻辑藏在不可见 helper。
- 在 helper 中偷偷做股票池、中性化、回测。

## 替换后检查
- 数学定义是否不变。
- `facnameuse` 是否稳定。
- `__main__` 是否完整可审阅。
- 共享逻辑是否真的回收到公共层，而不是复制到多个叶子文件。
