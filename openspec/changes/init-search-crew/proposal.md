# Proposal: 初始化 Search Crew Plugin

## 背景

调研类任务在 Claude Code 中频繁出现，但目前缺少分层能力：

- 简单查询（找一个工具、查一个事实）用 WebSearch 即可，但每次都在主 context 里展开
- 中度查询（在某官方站精确找一段说法）通用搜索引擎结果不够新、不够权威
- 深度调研（verify 一个领域、跨多源综合）需要循环判断和子主题分发，主 context 无法承担

需要一个 plugin，把三类工作流通过 subagent + 文件系统中介解开。

## 动机

- 通过 subagent 隔离 context，避免主对话被搜索结果污染
- 用 skill 沉淀通用搜索 / 抓取 / 站点 API 工具包，让 subagent 复用
- 把"按主题选 backend"的决策清单化（ROUTING.md），不依赖 LLM 临场判断
- 自带 chrome-devtools-mcp，让 site-search 在站点 API 不足时降级到真实浏览器

## 范围（In Scope）

1. 一个 plugin 包含三个 subagent：fast-search / site-search / deep-search
2. 一个 skill `search-toolkit`：通用搜索 backend（Jina/Serper）、抓取（Jina Reader）、站点 API 适配器（首版：GitHub / MDN / Algolia DocSearch / Read the Docs / PyPI / npm）、backend 路由清单
3. 一个 skill `browser-control`：chrome-devtools-mcp 使用最佳实践
4. 一个 MCP server 声明：chrome-devtools-mcp（通过 plugin.json 自动拉起）
5. 两个 slash command：`/search`（主入口，按 args 自动路由）、`/setup`（环境检查与引导）
6. API key 通过用户的 `~/.zshrc` 环境变量提供；未配置时 fallback 到 Claude Code 内置 WebSearch / WebFetch
7. 临时产物落在 `/tmp/search-crew/<run_id>/`

## 非目标（Non-Goals）

- **不实现**任何文档格式转 Markdown 的能力（见 Backlog B-001 / B-002 / B-003）
- **不实现**跨 run 结果复用 / 缓存
- **不实现**API key 的 keychain 或 secrets gateway 管理（保留 `~/.zshrc` 方案）
- **不实现**deep-search 的 token 预算硬控制
- **不在首版扩展**站点适配器到 arxiv / semantic-scholar / google-patents / clinicaltrials / pubmed / hackernews / 知乎（写进 EXTENDING.md 作为扩展指引）

## 影响面

- 新仓库初始化，无历史代码受影响
- 引入 npx 拉起的 MCP（chrome-devtools-mcp），用户首次使用 site-search 需要本地有 Chrome
- 引入可选环境变量 `JINA_API_KEY` / `SERPER_API_KEY` / `GITHUB_TOKEN`；未设时不报错，走 fallback

## 验证方式

见 `tasks.md` 的验证清单。
