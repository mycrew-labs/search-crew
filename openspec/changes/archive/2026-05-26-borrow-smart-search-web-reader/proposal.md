## Why

外部两个 skill（`~/Documents/Config/skills/smart-search` 与 `~/Documents/Config/skills/web-reader`）在「搜索摘要循证传递」、「触发边界反例」、「失败分类」三处的策略明显成熟，可以借鉴回 Search Crew。同时，smart-search 默认先用 AI 综述源建立假设的做法，揭示 Search Crew 当前 ROUTING 缺一层 AI 综述 backend——补齐 grok / doubao / gemini 三家后，循证链路的「先建立假设 → 再扩展专用源 → 最后回官方源复核」会更完整。

## What Changes

- **新增 AI 综述 backend**：在 `search-toolkit` 接入 grok（xAI Live Search）/ doubao（火山方舟联网搜索）/ gemini（Google Search Grounding）三家。统一封装到 `lib/backends/ai_*.py`，遵循现有 `lib/_http.py` 打点契约。返回结构含 `summary` + `citations[]`，与 jina/serper 的纯 `results[]` 并存。
- **ROUTING 增加「AI 综述层」**：新增「通用调研 / 概念入门 / 中文热点 / 英文舆论」四类分流到 grok/doubao/gemini，按语言与语境选一个；其他硬规则（临床研究、专利、官方文档等）保持「先官方源」不变。
- **cost summary 加「搜索摘要」段**：`finalize_usage.py` 输出末尾追加固定格式段：`网站 | 查询词 | 次数 | 已跳过原因`。不要求主 agent 把这段贴进回复（保留「仅一行 cost」的克制设计）；主 agent 那行 cost 扩成「带覆盖面数字」的形态（`N 次调用 · N 个源 · N 次触发站点调用上限`）。
- **site-search SKILL.md 显式声明「强制预检」步骤**：把 `--list-adapters` 写成启动 checklist 第一步；在 SKILL.md 顶部加一句「backend 是当前实现，不是身份」（为未来扩展留口）。
- **三个 subagent description 补反例**：在 `agents/fast-search.md` / `site-search.md` / `deep-search.md` 的 description / Triggers 段加「不要因...而触发」清单（参考 web-reader 的边界写法），减少误派。
- **browser-control 错误处理按失败点分类**：把现有「错误处理」段细化为「网络不可达 / 需要登录 / 内容在 iframe / 反爬拦截 / 权限不足 / 工具不可用」六类，每类给主 agent 的下一步建议。
- **`.env.example` + 部署 / 扩展文档同步**：补 `GROK_API_KEY` / `DOUBAO_API_KEY`（火山方舟）/ `GEMINI_API_KEY` 三个 API key（model 不进 env，进 routing.yaml）；`EXTENDING.md` 增加「AI 综述 backend」章节描述如何关掉 / 替换 / 加第四家。
- **运行时站点调用上限**（smart-search #1 等价物）：在 `lib/_http.py` 出口侧加一份 in-memory「同 run 站点调用计数」，AI 站点同题硬限 1 次，非 AI 同题硬限 2 次，达到上限直接返回 fallback marker，不再发请求。

## Capabilities

### New Capabilities

无。所有改动落到现有 capability 上。

### Modified Capabilities

- `fast-search`：新增 AI 综述 backend 路由分支；description 加反例；输出附「搜索摘要」段
- `site-search`：description 加反例；启动强制预检 checklist 写明；浏览器降级路径的失败分类细化
- `deep-search`：description 加反例；最终回复内嵌「搜索摘要」段；规划阶段查询词模板（主题 + 目标 + 限定条件）
- `orchestration`：主 agent 回复格式增加「搜索摘要」段；ROUTING 起点表新增 AI 综述层
- `usage-tracking`：`finalize_usage.py` 输出格式扩展；新增「同 run 站点调用频次硬限」requirement

## Impact

- **代码**：`skills/search-toolkit/scripts/lib/backends/`（新增 ai_grok.py / ai_doubao.py / ai_gemini.py）、`lib/_http.py`（频次台账 hook）、`scripts/finalize_usage.py`（输出格式）、`scripts/search.py`（backend 选项扩展）、`defaults/routing.yaml`（AI 综述层）
- **文档**：`README.md`、`EXTENDING.md`、`.env.example`、三个 agents/*.md、两个 skills/*/SKILL.md
- **依赖**：grok / doubao / gemini 三家 HTTP API 直连，零新增 Python 依赖（仍走 stdlib + `lib/_http.py`）
- **配置**：用户态 `~/.config/search-crew/routing.yaml` 不破坏兼容（plugin defaults 升级后用户手动 merge，已是现状）
- **向后兼容**：现有 jina / serper backend 不变；未配 AI key 时自动跳过 AI 综述层，回落到 jina/serper（与现有 fallback 一致）
