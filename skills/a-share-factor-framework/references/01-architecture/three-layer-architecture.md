# Codex 三层架构约定（用户修正版）

适用场景：用户要求重构 A 股因子代码结构，强调把“原始因子、基础公式、codex 叶子文件”严格分层。

## 三层定义

### 第一层：原始因子层
- 文件形态：如 `income.py`、`profit.py`
- 责任边界：只放最原始的因子原值/底层数据加工逻辑
- 不要混入：组合公式、codex 叶子回测流程、共享表达式工具堆叠

### 第二层：基础公式层
- 新文件：`func.py`
- 责任边界：只保留 `sigconstructperiods_` 可直接调用的“最基本函数”
- 内容类型：lag / diff / rolling / add / sub / mul / div / rank / zscore / 其他最小原子公式
- 不要混入：loader、facname 组织、回测流程、股票池、标准化、中性化

### 第三层：codex 叶子文件层
文件命名：`*_codex.py`

推荐结构顺序：
1. 顶部先 `from database.code.windsql import ...` 与 `feather` 等依赖
2. `class Xxx_codex(...)`
3. `def __init__(...)`
4. `def initdataclass_(...)`
5. `def sigconstructperiods_(...)`
   - 此处调用 `func.py`
   - 负责把需要的类别因子公式组装出来
6. `if __name__ == '__main__':`
   - 再做运行期 import
   - `periods = ...`
   - `self = ...`
   - `self.getfac_()`
   - `getstkpool`
   - merge / ffill
   - 标准化
   - `neutfactorclas_`
   - `Stkfactorbacktest_`

## 执行原则
- 先把“公式层”收敛到 `func.py`，再让各 `*_codex.py` 调用
- `*_codex.py` 是叶子层：组织调用链，不重复发明基础公式
- 不要把三层边界打散；尤其不要把 loader/回测流程塞进 `func.py`

## 用户明确偏好
- 这是用户主动提出的结构修正，后续生成或重构因子代码时默认按此架构执行
- 若现有代码与此约定冲突，优先解释差异，并在改造时朝此结构收敛
