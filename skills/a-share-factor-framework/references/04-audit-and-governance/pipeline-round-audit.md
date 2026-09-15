# Pipeline 逐轮审计规程

## 触发条件

当需要审查历史所有轮次的因子挖掘结论时，使用本规程。

## 审计步骤

### 1. 收集 handoff 文档

```bash
ls ${PROJECT_ROOT}/docs/session_handoffs/
```

读取所有 `evaluator_review_rounds*.md` 汇总文件 + 各单轮 handoff。注意文件名可能有不同命名规范（`roundX_*`、`RXX_*`、`2026-07-XX_t_*`）。

### 2. 整理轮次状态表

从每个 evaluator 审查文档中提取：
- 轮次号、方向、审查结论（通过/有条件通过/不通过/关闭）
- 最佳变体名称和指标（ICmean / IR / lsret）
- 核心失败原因（多因子组合/信号弱/方向重复/等）
- evaluator 下一轮方向建议

### 3. 交叉验证 review_queue/

```bash
ls ${PROJECT_ROOT}/factor_replicate_outputs/review_queue/
```

每个有效轮次应在 review_queue/ 下有对应目录。缺失目录表示轮次可能未进入算子空间或产物已被清理。

### 4. 检查 evaluator_passed/ 滞留

```bash
ls -la ${PROJECT_ROOT}/factor_replicate_outputs/evaluator_passed/
```

- 记录每个通过因子的等待天数
- 如果 R22/R23 级别的 3/3 达标因子已等待多轮，标记为「候选项卡阻塞」
- 用户需要人工终审后才能决定入库或回流

### 5. 找出缺口和重复

审计时特别关注以下模式：
- **方向重复**：同一经济学方向被不同公式外壳反复尝试（如 R17→R29）
- **同源重复**：同一组原子信号被多次变换表达式（如 R7-R11→R16）
- **重复调度**：同一候选项被多个 evaluator task 审查
- **文档缺失**：某轮次在 session_handoffs/ 没有对应 handoff 文件
- **代码提前入库**：dvcoder 在 evaluator 通过前将文件写入 util/rawsigs/

### 6. 输出审计报告

输出结构：
- 已通过等待终审的因子列表（含指标）
- 各轮次状态汇总表
- 发现的问题清单（优先级排序）
- 建议的修复动作
