# Deep Search

跨多轮深度调研。派 fast-search / site-search 干活，自抓深挖允许，最终消化压缩成 HTML + Markdown 双格式报告。

## Purpose

把"调研一个领域 / verify 一个说法 / 全面对比"这类需要循环判断的复杂任务从主对话隔离出去；deep-search 自己规划、综合、判断、跟进。
## Requirements
### Requirement: deep-search 派活优先，自抓允许，不重新实现 backend
deep-search MUST NOT 自己拼 Jina / Serper 等 backend 请求。所有通用搜索 MUST 通过派 fast-search 完成，所有官方站精确搜索 MUST 通过派 site-search 完成。但 deep-search **被允许**直接用 `fetch.py` 抓已知 URL，或沿页面链接深挖。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 派 fast-search 做通用调研
- **WHEN** deep-search 第一轮需要广度调研某子主题
- **THEN** 派出 fast-search subagent，不自己调 `search.py`

#### Scenario: 自抓已知 URL
- **WHEN** deep-search 在第二轮拿到一个具体 URL 想深挖
- **THEN** 允许直接调 `fetch.py <url>`，无需多派一个 subagent

#### Scenario: 禁止自拼 backend 请求
- **WHEN** deep-search 想做一次通用搜索
- **THEN** MUST 派 fast-search；不允许自己直接 HTTP 调 Jina / Serper

### Requirement: deep-search 第一轮产出 plan.md
deep-search 第一轮 MUST 先把 topic 拆成研究计划：角度 + 子任务清单 + 每子任务的完成判据，写入 `<run_root>/deep-search/plan.md`。后续每轮基于 plan 推进；每轮末尾对 plan 中的子任务自评 done / not-done。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 第一轮规划
- **WHEN** deep-search 收到 topic
- **THEN** 第一轮产出 `plan.md`，含至少一个角度 + 子任务清单 + 每子任务的完成判据

#### Scenario: 每轮自评
- **WHEN** deep-search 完成第 N 轮
- **THEN** 写 `round-N.md`，含本轮派发了什么、收回什么、对 plan 中每子任务的 done / not-done 自评

### Requirement: deep-search 同 turn 并行派发
deep-search 在一轮内派多个 subagent 时 MUST 在同一 message 内一次性发起多个 Task 工具调用（并行），不是串行。派发前 MUST 先调 `TaskCreate` 注册任务。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 一轮派 3 个 fast-search
- **WHEN** deep-search 第一轮要并行调研 3 个子主题
- **THEN** 3 个 Task 工具调用在同一 message 内发起；TaskCreate 已先注册 3 个任务

### Requirement: deep-search 派 subagent 时传 target 目录
deep-search 派下级 subagent 时 MUST 把目标目录传给下级（如 `<run_root>/deep-search/traces/fast-search-<sid>/`），让下级在该目录内工作。这避免「一次 deep-search 的产物散落在多个 session-id 目录」。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: traces 子目录归集
- **WHEN** deep-search 派 fast-search
- **THEN** 调用参数包含 `target_dir=<run_root>/deep-search/traces/fast-search-<sid>/`；下级产物落在该目录而非自己的 session-id 目录

### Requirement: deep-search 主交付物 = report.html + report.md 双格式
deep-search 综合阶段 MUST 同时产出 `<run_root>/deep-search/report.html`（给用户，LLM 自由生成的可视化形态）+ `<run_root>/deep-search/report.md`（给主模型，纯 markdown）。两份文件 MUST 语义等价——不允许 HTML 多结论 / 少结论。HTML 中的循证链接 MUST 可点击，链接对象为外部 URL 或本地 markdown 路径。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 综合阶段产出双格式
- **WHEN** deep-search 完成所有子任务，进入综合阶段
- **THEN** 产物目录下同时存在 `report.html` 与 `report.md`，两者陈述的结论 / 引用相同

#### Scenario: 用户优先看 HTML，主模型优先看 markdown
- **WHEN** 主 agent 收到 deep-search 返回
- **THEN** 主 agent Read `report.md`（不读 HTML，效率太低）；告知用户用 `open report.html` 直观查看

### Requirement: deep-search 保留可追溯的底层产物
deep-search 综合阶段 MUST 丢弃绝大部分原始内容、给报告，但 MUST 保留可追溯的底层产物子目录（`<run_root>/deep-search/traces/`），让上级或用户想验证时可以下钻。报告中的引用 anchor 指向 traces 内的具体 markdown 段落。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: traces 保留
- **WHEN** deep-search 完成综合
- **THEN** `<run_root>/deep-search/traces/` 下保留所有派出的 fast-search / site-search 的完整产物

#### Scenario: 报告引用回 traces
- **WHEN** `report.md` 中陈述一个结论
- **THEN** 结论后跟 `见 [fast-search-003 §<slug>](traces/fast-search-<sid>/fast-search-003.md#<slug>)` 风格的引用

### Requirement: deep-search max_rounds 硬上限
deep-search MUST 受 `~/.config/search-crew/limits.yaml` 的 `deep_search.max_rounds` 限制（默认 5）。即便子任务未完成，达到上限 MUST 进入综合阶段并在报告中显式标注未完成项。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 达到 max_rounds
- **WHEN** deep-search 跑到第 5 轮仍有未完成子任务
- **THEN** 进入综合阶段；report 中显式标注哪些子任务未完成、为什么未完成

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

