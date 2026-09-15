# rawsigs `getcalcuse_` 来源-导入列口径

## 触发场景
当需要审计 `${PROJECT_ROOT}/util/rawsigs` 中“从原始数据导出”的 textbook rawsig 类，并输出来源类、缓存文件、导入列清单时使用。

## 默认筛选口径
只保留同时满足以下条件的 `.py` 文件：
1. 文件名不含 `codex`
2. 源码包含 `def getcalcuse_`
3. 源码不包含 `def sigconstruct_`
4. 源码不包含 `def sigconstructperiods_`

这对应的是 textbook rawsig 原始数据映射层，而不是上层自定义组合层。

## 提取规则
### 1. 不按“一文件一个来源”压平
必须按 `getcalcuse_` 实际调用到的原始数据类展开多行，因为同一 rawsig 文件可能混合多个来源。

### 2. 导入列以真实调用为准
优先从这些调用提取列名：
- `self.xxx.getdata_(varnames=...)`
- `self.xxx.getdata_(varname=...)`
- `getexpressdata_(expressclass=..., varnamelist=...)`
- `compressexpress_notice_income_(...)`

不要只看：
- `initdataclass_()` 初始化了哪些类
- 文件名像哪个报表
- 某些分支里后赋值的 `varname`

### 3. 推荐输出列
- `代码目录`
- `代码文件`
- `代码类名`
- `原始数据类`
- `原始数据名`
- `原始数据缓存文件`
- `导入列`

## 复核顺序
1. 先批量提取候选文件、来源类、导入列
2. 检查是否存在空 `导入列`
3. 抽查混合来源文件，如 `asset.py`、`eq.py`、`profit.py`、`dividend.py`
4. 再核对缓存路径是否真实可解析
5. 若缓存路径为空，先判断是否源类缺失，不要先归咎提取脚本

## 典型坑点
- `dividend.py` 容易被误归到资产负债表；实际应来自分红数据类。
- `profit.py` 往往不是单一利润表来源，可能同时接 express / notice。
- 脚本输出空列不等于源码无列，需回到 `varname/varnamelist` 分支确认。
- 空缓存路径优先视为源类缺失或项目结构待确认。
