## Why

split-fast-and-evidence（0.8.0）把 `/search-fast` 改为 AI 综述快答、原 worker 改名 evidence-search，但**没扫净** `fast-search` 的零散旧引用——orchestration 的语义自动派发、wide 自动路由、deep-search / site-search 的若干 scenario / 反例仍写 `fast-search`，造成 spec 漂移（同名指两义）。

同时用户拍板了路由语义：**casual「查一下 X」自动到 `/search-fast`（AI 快答）；deep-search / wide-search 一律显式调用**（`/search-deep` `/search-wide`），不再做语义自动派发。本 change 把这两件事一起收口：定路由 + 扫漂移。

## What Changes

- **MODIFY orchestration 自动派发语义**（locked）：无显式命令时——通用 casual 查询 → `/search-fast`（AI 综述快答）；定向官方站 / 权威敏感主题 → site-search；**deep / wide MUST 仅由 `/search-deep` `/search-wide` 显式触发**，不做语义自动派发。
- **REMOVE「批量对比 N 个对象 → 自动派 wide-search」**需求：wide 改为显式专属。
- **扫净残留 `fast-search` 引用**（worker 语义 → `evidence-search`；通用搜索语义 → `/search-fast`）：
  - deep-search：能力描述行、「派 subagent 传 target」locked 的 trace 路径与 scenario、「一轮派 N 个 worker」scenario。
  - site-search：「新适配器先查现成代码」「产出 ranking 同 worker 约定」「触发反例」三处的 fast-search → evidence-search / /search-fast。
- **agent / 命令文档**：deep-search、wide-search 的 description 明确「显式触发」，不写"自动派发"暗示；主 agent 路由心智按上述更新。

## Capabilities

### Modified Capabilities

- `orchestration`：MODIFY「对话语义触发」locked（fast-search → /search-fast 快答 + deep/wide 显式专属）；REMOVE「路由 N 个对象到 wide-search」（wide 显式专属）；扫 scenario 残留。
- `deep-search`：MODIFY「派 subagent 传 target 目录」locked 的 fast-search 引用 → evidence-search；描述行 / scenario 同步。
- `site-search`：MODIFY 三条含 fast-search 的需求（反例 / ranking 约定 / 新适配器查现成）→ evidence-search / /search-fast。

## Impact

- **locked 影响**：orchestration「对话语义触发」+ deep-search「派 subagent 传 target」是 user-confirmed 锁，MODIFY 需用户确认；wide 自动路由需求未锁，REMOVE。
- **行为变化**：deep/wide 不再被对话语义自动触发（只认显式命令）；casual 通用查询从"派 fast-search 结构化采集"变为"/search-fast 一口 AI 答案"——更快、更省，但不给结构化证据（要证据显式 /search-deep）。
- **纯文档/路由**：不改任何脚本代码（A/B/C 已把脚本与 agent 改完）；本 change 是 spec + agent description + 路由心智的收口。
- **向后兼容**：显式命令 /search-deep /search-wide /search-fast 不变；只是去掉了 deep/wide 的隐式自动触发。
