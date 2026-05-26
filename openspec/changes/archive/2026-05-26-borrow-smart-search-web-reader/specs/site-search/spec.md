## ADDED Requirements

### Requirement: site-search 触发反例（不应派 site-search 的场景）
site-search agent description 中 MUST 包含「不要因以下情况派 site-search」反例清单。反例 MUST 至少覆盖：无明确目标站点（应派 fast-search）、跨多站点综述（应派 fast-search 或 deep-search）、读取已知 URL（应直接 fetch）、模糊关键词探索（应派 fast-search）。

#### Scenario: 主 agent 看到反例后不误派
- **WHEN** 用户说「帮我综述下当下主流的开源 LLM 推理框架」
- **THEN** 主 agent 根据反例「跨多站点综述」判断，不派 site-search，改派 fast-search 或 deep-search

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
