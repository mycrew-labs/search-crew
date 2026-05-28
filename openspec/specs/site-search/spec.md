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
**Confirmed-At**: 2026-05-28

#### Scenario: 接触新站点
- **WHEN** site-search 发现 `--list-adapters` 不包含目标站点
- **THEN** 先派 evidence-search 搜 `<site> api / scraper / wrapper` 找现成实现；将发现写到 `~/.config/search-crew/pending/adapters/<timestamp>-<site>.yaml`；本次任务用浏览器 MCP 兜底完成

### Requirement: site-search 遵守 robots.txt 与速率限制
site-search MUST 遵守目标站点的 robots.txt 与速率限制；MUST NOT 对单一站点高频请求；MUST NOT 打开有敏感数据的页面；MUST NOT 尝试登录用户未授权的站点；浏览器实例使用完 MUST 关闭释放资源。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 浏览器任务结束
- **WHEN** site-search 用 MCP 完成抓取
- **THEN** 调 close 工具释放浏览器实例，不留挂起进程

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

### Requirement: site-search 启动前必跑强制预检 checklist
site-search 在每次接到任务后、调用任何 backend 或 MCP 之前 MUST 完成强制预检：(1) 运行 `python3 site_search.py --list-adapters` 查看当前实时适配器清单；(2) 确认目标站是否已有 adapter；(3) 若已有，再查该 adapter 的 status（`✅` / `⚠️ best-effort` / `降级`）。MUST NOT 跳过预检直接拼调用参数。

#### Scenario: 启动时跑预检
- **WHEN** site-search 收到 site=github.com、query=...
- **THEN** 主 prompt 的第一步动作日志包含 `--list-adapters` 输出快照（adapter 清单 + status）

#### Scenario: 无 adapter 时按降级路径
- **WHEN** 预检发现目标站不在 `--list-adapters` 清单
- **THEN** 进入「fetch 固定 URL → 浏览器 MCP」三级降级，与已 locked 的「site-search 按三级优先级降级」一致

### Requirement: site-search SKILL.md 明确「backend 是当前实现，不是身份」
`skills/search-toolkit/SKILL.md` 与 `skills/browser-control/SKILL.md` 顶部 MUST 包含一句声明：当前实现使用的 backend / MCP 工具集是当前选型，不是本 skill 的身份；未来可替换为其他实现，spec 行为不变。MUST NOT 在 SKILL.md 内硬编码假定某 backend 永远存在。

#### Scenario: 顶部声明存在
- **WHEN** 读取 `skills/search-toolkit/SKILL.md`
- **THEN** Purpose / 简介段之后存在「backend 是当前实现，不是身份」的等义声明（中文表达可调整）

### Requirement: browser-control 失败按六类分类并给主 agent 下一步建议
`skills/browser-control/SKILL.md` 的「错误处理」段 MUST 改成六类分类表，每类附主 agent 的下一步建议。六类为：网络不可达、需要登录、内容在 iframe、反爬拦截、权限不足（403）、工具不可用（MCP 断连）。

#### Scenario: 失败时返回分类标签
- **WHEN** site-search 用 MCP 控制浏览器抓某站，目标页要求登录
- **THEN** 返回结果 JSON 含 `failure_kind: "needs_login"` 字段；INDEX.md 标 `needs_login: true`

#### Scenario: SKILL.md 内含六分类表
- **WHEN** 读取 `skills/browser-control/SKILL.md`
- **THEN** 「错误处理」段为六行表（每行：失败点 → 下一步建议），不是扁平 bullet 列表

