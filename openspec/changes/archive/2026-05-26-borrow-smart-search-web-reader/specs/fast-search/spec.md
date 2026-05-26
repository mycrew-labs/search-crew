## ADDED Requirements

### Requirement: fast-search 触发反例（不应派 fast-search 的场景）
fast-search agent description 中 MUST 包含「不要因以下情况派 fast-search」反例清单，供主 agent 在路由前判断。反例 MUST 至少覆盖：单条事实查询、已有具体 URL 只需 fetch、需要站内精确搜索（应派 site-search）、需要多轮跨主题挖掘（应派 deep-search）、需要权威源复核（应派 site-search）。

#### Scenario: 主 agent 看到反例后不误派
- **WHEN** 用户说「帮我打开 react.dev 看下 Suspense 这页」
- **THEN** 主 agent 根据反例「已有具体 URL 只需 fetch」判断，不派 fast-search，改为直接 fetch

#### Scenario: agent description 含反例段
- **WHEN** 读取 `agents/fast-search.md`
- **THEN** 文件存在标题为「## 不要触发本 agent 的场景」（或等义中文）的反例清单段

### Requirement: fast-search 可选用 AI 综述 backend
fast-search 在 query 未命中 ROUTING 硬规则、且 `~/.config/search-crew/routing.yaml` 中 `ai_summary.enabled` 为 true 时 SHALL 优先使用 AI 综述 backend（grok / gemini / doubao 之一）作为第一跳，再决定是否补充 jina / serper / 站点搜索。具体三家如何选 MUST 按语言 / 语境判断（中文热点偏 doubao，英文舆论偏 grok，全球综述偏 gemini）。所用 model 由 `ai_summary.models.<backend>.<tier>` 决定（fast-search 用 fast 档）。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-26

#### Scenario: 中文热点选 doubao
- **WHEN** fast-search 收到 query「最近抖音上爆火的 AI 应用」、`DOUBAO_API_KEY` 已配
- **THEN** fast-search 第一跳调用 doubao backend（火山方舟），用 `ai_summary.models.doubao.fast` 指定的 model，返回 `{summary, citations[]}`

#### Scenario: 英文舆论选 grok
- **WHEN** fast-search 收到 query「what people on X say about Sora 2」、`GROK_API_KEY` 已配
- **THEN** fast-search 第一跳调用 grok backend

#### Scenario: 命中硬规则跳过 AI 综述层
- **WHEN** fast-search 收到 query「pembrolizumab 三期临床试验结果」（命中临床研究硬规则）
- **THEN** fast-search 不调用任何 AI backend，直接信号上级派 site-search 到 clinicaltrials.gov / pubmed

#### Scenario: 全部 AI key 缺失回落 jina/serper
- **WHEN** `GROK_API_KEY` / `GEMINI_API_KEY` / `DOUBAO_API_KEY` 均未配置
- **THEN** fast-search 跳过 AI 综述层，直接按现有 jina/serper 路径执行；不报错

### Requirement: fast-search 查询词构造遵循「主题 + 目标 + 限定条件」
fast-search 在用 AI 综述 backend 或调 search.py 之前 SHALL 把 query 构造成至少含「主题 + 目标 + 限定条件」三要素的形态。MUST NOT 只丢一个单名词到 backend。限定条件 MUST 覆盖至少一项：语言、地区、时间范围、平台范围、输出形式。

#### Scenario: 主题过短时主动补限定条件
- **WHEN** 主 agent 传入 query 仅为「vLLM」
- **THEN** fast-search 在 prompt 内部把 query 扩成「vLLM 在 2025 年的性能基准对比 + 英文官方源」再传给 backend

#### Scenario: 已含限定条件直接透传
- **WHEN** 主 agent 传入 query 已含时间 + 地区限定（如「2026 年北京适合学生的咖啡店」）
- **THEN** fast-search 直接透传，不再补充
