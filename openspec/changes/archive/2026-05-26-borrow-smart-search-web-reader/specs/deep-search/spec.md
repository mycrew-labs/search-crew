## ADDED Requirements

### Requirement: deep-search 触发反例（不应派 deep-search 的场景）
deep-search agent description 中 MUST 包含「不要因以下情况派 deep-search」反例清单。反例 MUST 至少覆盖：单轮信息已够、单条事实查询、用户只问一句概念、明确指定唯一站点（应派 site-search）。

#### Scenario: 主 agent 看到反例后不误派
- **WHEN** 用户说「React 19 引入了什么新 hook」
- **THEN** 主 agent 根据反例「单条事实查询」判断，不派 deep-search，改派 fast-search 或 site-search

#### Scenario: agent description 含反例段
- **WHEN** 读取 `agents/deep-search.md`
- **THEN** 文件存在标题为「## 不要触发本 agent 的场景」的反例清单段

### Requirement: deep-search plan.md 中子任务查询词遵循「主题 + 目标 + 限定条件」
deep-search 在第一轮 plan.md 中写出每个子任务的预期查询词时 MUST 至少含「主题 + 目标 + 限定条件」三要素。MUST NOT 把子任务查询词写成单个名词。限定条件 MUST 覆盖至少一项：语言、地区、时间范围、平台范围、输出形式。

#### Scenario: plan.md 子任务查询词含三要素
- **WHEN** deep-search 第一轮写 `plan.md`，含三个子任务
- **THEN** 每个子任务的预期查询词字段都不只是单名词，至少含主题 + 目标 + 一项限定条件

#### Scenario: 派 fast-search 时透传完整查询词
- **WHEN** deep-search 派出 fast-search 跑某子任务
- **THEN** 传给 fast-search 的 query 与 plan.md 中记录的预期查询词一致（含三要素）
