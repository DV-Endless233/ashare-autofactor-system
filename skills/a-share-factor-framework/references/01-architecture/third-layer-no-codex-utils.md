# 第三层重构：不再依赖 `codex_utils`

## 结论
当前第三层 `*_codex.py` 应该是**可直接阅读的叶子封装**，不再把主逻辑藏在 `codex_utils`。

## 第三层应保留的内容
- 输入 rawsig / 公共算子的选择。
- 参数声明与 `facnameuse`。
- `sigconstructperiods_` 里对共享算子的最小调用。
- 缓存与 `__main__` 标准尾部。

## 第三层不应承担
- 通用 rolling 算子定义。
- 通用 divide / regression / percentile / rank 工具。
- 通用股票池、中性化、回测黑盒。

## 重构顺序
1. 先把旧 helper 中的数学算子迁到共享层。
2. 再让叶子文件显式调用这些算子。
3. 最后删掉对 `codex_utils` 的依赖。
