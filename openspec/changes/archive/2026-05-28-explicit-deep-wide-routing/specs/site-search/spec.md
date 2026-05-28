## MODIFIED Requirements

### Requirement: 新适配器实现前先查现成代码
实现一个新站点适配器或调整查询方式时，site-search MUST 先去 GitHub / 搜索引擎查现成抓取实现，参照他人代码而不是闭门造车。参照他人代码 MUST 在 adapter 文件顶部注释里写明来源链接与改写程度。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-28

#### Scenario: 接触新站点
- **WHEN** site-search 发现 `--list-adapters` 不包含目标站点
- **THEN** 先派 evidence-search 搜 `<site> api / scraper / wrapper` 找现成实现；将发现写到 `~/.config/search-crew/pending/adapters/<timestamp>-<site>.yaml`；本次任务用浏览器 MCP 兜底完成

### Requirement: site-search 产出 ranking + 摘要 + 关键词
site-search MUST 跟 evidence-search 同样的产物组织约定：ranking + 推荐等级 + 关键词 + INDEX wiki 大纲。文件前缀 `site-search`。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-28

#### Scenario: 落盘格式
- **WHEN** site-search 抓回结果
- **THEN** `<run_root>/site-search/site-search-NNN.md`（带 front-matter）+ `<run_root>/site-search/INDEX.md`（wiki 大纲）

### Requirement: site-search 触发反例（不应派 site-search 的场景）
site-search agent description 中 MUST 包含「不要因以下情况派 site-search」反例清单。反例 MUST 至少覆盖：无明确目标站点（应走 `/search-fast` 快答或 evidence-search）、跨多站点综述（应走 `/search-deep`）、读取已知 URL（应直接 fetch）、模糊关键词探索（应走 `/search-fast`）。

#### Scenario: 主 agent 看到反例后不误派
- **WHEN** 用户说「帮我综述下当下主流的开源 LLM 推理框架」
- **THEN** 主 agent 根据反例「跨多站点综述」判断，不派 site-search，提示 `/search-deep`（或先给 /search-fast 快答）

#### Scenario: agent description 含反例段
- **WHEN** 读取 `agents/site-search.md`
- **THEN** 文件存在标题为「## 不要触发本 agent 的场景」的反例清单段
