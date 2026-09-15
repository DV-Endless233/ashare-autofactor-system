# Prompt 与参考边界

本参考用于纠正 A 股量化任务启动时常见的上下文混淆。

## 结论

1. 不要默认把 `${PROJECT_ROOT}/SKILL.md` 当成当前主规范。
   - 它可能只是早期 bootstrap 文档。
   - 如果用户已明确说它过时、不能覆盖当前框架，就必须降级为历史参考，而不是主入口。

2. 回答“现在启动量化任务参考哪些 skill”时，要区分三层：
   - **量化实现 skill**：如 `a-share-factor-framework`、`strategy-replication-skill`
   - **协作/调度 skill**：如 `kanban-worker`，只管流程，不决定因子实现口径
   - **Hermes 架构/提示词层**：`SOUL.md`、memory、项目 context 文件；这不是量化方法 skill，但会强烈影响行为

3. 不要继续引用已删除的历史 skill。
   - 如果用户已明确 `factor-framework-skill` 已删除，就不能再把它列为“当前参考集合”或“迁移参考”。

4. 当用户讨论的是 agent 结构、workflow、system prompt，而不是因子公式或回测实现时：
   - 先切换到“架构盘点”语境
   - 先说明 `SOUL.md` / memory / project context / skills 的边界
   - 不要直接把讨论重新拉回因子代码实现

## 对后续整理 skill 的建议

- 主 `SKILL.md` 保持薄：只写触发条件、标准工作流、交付物、核心 pitfalls。
- 复杂历史说明、结构示例、旧路径兼容、长案例下沉到 `references/`。
- 如果项目级硬规则需要稳定自动注入，应优先考虑项目级 `HERMES.md` / `.hermes.md`，而不是只依赖 skill 文案里引用 `${PROJECT_ROOT}/SKILL.md`。
