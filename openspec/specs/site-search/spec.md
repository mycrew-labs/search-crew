# Site Search

在指定官方站点内的精确搜索。API 适配器优先，URL 模式次之，Chrome DevTools MCP 兜底。承担循证四步中的「先在起点搜」与「回官方源复核」职责。

## Purpose

把通用搜索引擎搞不定的事情按官方源头精确拿——避免版本错乱、过时结论、被 SEO 干扰的二手信息。

## Requirements

### Requirement: site-search 按三级优先级降级
site-search SHALL 按以下优先级处理：(1) 用站点专属 API 适配器；(2) fetch 站点固定搜索 URL（如 `https://<site>/search?q=...`）解析静态 HTML；(3) 启用 Chrome DevTools MCP 控制浏览器。**MUST NOT** 跳过前两级直接用 MCP。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: github.com 走 API 适配器
- **WHEN** site-search 收到 site=github.com、query="claude code"
- **THEN** 调 `site_search.py --site github.com --query "claude code"`，走 GitHub API 适配器返回结构化结果

#### Scenario: 无适配器时尝试固定 URL 模式
- **WHEN** site-search 收到一个 `list-adapters` 中没有的站
- **THEN** 先用 `fetch.py` 抓 `https://<site>/search?q=<query>` 并解析

#### Scenario: SPA / 异步加载才用 MCP
- **WHEN** 目标站点是 SPA、搜索结果靠 JS 异步加载，URL 不可 deep link
- **THEN** site-search 启用 `mcp__chrome-devtools__*` 工具完成搜索

### Requirement: site-search 支持复核模式（verify）
site-search 收到 `verify=true` + 待复核结论时 MUST 在官方站搜该结论的关键词 / 数字，并在返回结果中明确标注 verified / not-in-official-source 状态。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 官方源找到记录
- **WHEN** site-search 复核某结论，官方源命中
- **THEN** 返回结果带 `verification: verified` 标签

#### Scenario: 官方源未找到
- **WHEN** site-search 复核某结论，官方源未找到
- **THEN** 返回结果带 `verification: not-in-official-source` 标签，调用方 MUST 在最终回复中显式标注

### Requirement: 新适配器实现前先查现成代码
实现一个新站点适配器或调整查询方式时，site-search MUST 先去 GitHub / 搜索引擎查现成抓取实现，参照他人代码而不是闭门造车。参照他人代码 MUST 在 adapter 文件顶部注释里写明来源链接与改写程度。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 接触新站点
- **WHEN** site-search 发现 `--list-adapters` 不包含目标站点
- **THEN** 先派 fast-search 搜 `<site> api / scraper / wrapper` 找现成实现；将发现写到 `~/.config/search-crew/pending/adapters/<timestamp>-<site>.yaml`；本次任务用浏览器 MCP 兜底完成

### Requirement: site-search 遵守 robots.txt 与速率限制
site-search MUST 遵守目标站点的 robots.txt 与速率限制；MUST NOT 对单一站点高频请求；MUST NOT 打开有敏感数据的页面；MUST NOT 尝试登录用户未授权的站点；浏览器实例使用完 MUST 关闭释放资源。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 浏览器任务结束
- **WHEN** site-search 用 MCP 完成抓取
- **THEN** 调 close 工具释放浏览器实例，不留挂起进程

### Requirement: site-search 产出 ranking + 摘要 + 关键词
site-search MUST 跟 fast-search 同样的产物组织约定：ranking + 推荐等级 + 关键词 + INDEX wiki 大纲。文件前缀 `site-search`。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 落盘格式
- **WHEN** site-search 抓回结果
- **THEN** `<run_root>/site-search/site-search-NNN.md`（带 front-matter）+ `<run_root>/site-search/INDEX.md`（wiki 大纲）
