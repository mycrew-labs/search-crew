## ADDED Requirements

### Requirement: ROUTING 起点表新增 AI 综述层
`~/.config/search-crew/routing.yaml`（与 plugin `defaults/routing.yaml`）MUST 新增 `ai_summary:` 顶层段，描述「query 未命中任何硬规则时，优先派 AI 综述 backend 作为第一跳」的策略。该段 MUST 含：`enabled`（默认 true）、`selection_order`（默认 `[grok, doubao, gemini]`）、`fallback_on_no_key`（默认 `jina`）、`models`（每个 backend 的 `fast` / `deep` 档 model id）。AI backend 用品牌名 `grok` / `gemini` / `doubao`；API key 走 env（`GROK_API_KEY` / `GEMINI_API_KEY` / `DOUBAO_API_KEY`），model 选择只走 `ai_summary.models`，MUST NOT 在代码 hardcode 或用 env 配 model。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-26

#### Scenario: defaults/routing.yaml 含 ai_summary 段
- **WHEN** 读取 `defaults/routing.yaml`
- **THEN** 文件顶层存在 `ai_summary:` 段，含 `enabled`、`selection_order`、`fallback_on_no_key`、`models` 四个键；`models.<backend>` 下含 `fast` / `deep` 两档 model id

#### Scenario: 硬规则优先级高于 AI 综述
- **WHEN** query 命中临床研究 / 专利 / 官方文档等硬规则
- **THEN** ROUTING 起点表的 AI 综述层 MUST 被跳过，按硬规则派 site-search

#### Scenario: 用户禁用 AI 综述层
- **WHEN** 用户改 `~/.config/search-crew/routing.yaml` 中 `ai_summary.enabled: false`
- **THEN** 所有 subagent 都不调用 AI backend，回到原有 jina/serper 路径

### Requirement: 主 agent cost 总览一行扩展为「带覆盖面数字」格式
主 agent 在最终回复结尾的那一行 cost 总览 SHALL 扩展格式为 `📊 本次估算 ~$X.XXX USD（N 次调用 · M 个源 · K 次触发站点调用上限）`。其中 `M 个源` 为本次 run 实际调用过的 distinct backend / site 数，`K 次触发站点调用上限` 为被上限拦下的请求数（K=0 时该段省略）。该行 MUST 仍保持单行，MUST NOT 拆分成多行，MUST NOT 出现 `/tmp/search-crew/` 路径字符串。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-26

#### Scenario: 正常一次调研
- **WHEN** 主 agent 完成调研，本次 run 调用 12 次、4 个不同源、未触发上限
- **THEN** 回复末尾仅有一行：`📊 本次估算 ~$0.043 USD（12 次调用 · 4 个源）`

#### Scenario: 触发站点调用上限
- **WHEN** 本次 run 内有 2 次请求被站点调用上限拦下
- **THEN** 回复末尾的 cost 行含 `· 2 次触发站点调用上限`

#### Scenario: 未变成多行
- **WHEN** 主 agent 输出最终回复
- **THEN** cost 总览整体仍是一行字符串，不含换行符
