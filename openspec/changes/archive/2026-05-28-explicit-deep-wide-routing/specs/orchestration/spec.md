## REMOVED Requirements

### Requirement: 对话语义触发 fast-search 与 site-search
**Reason**: fast-search 已拆分；casual 通用查询改自动到 `/search-fast`（AI 综述快答），且 deep/wide 改为显式专属。由下方「对话语义只自动触发快答与 site-search」取代。
**Migration**: 通用 casual 查询 → /search-fast；定向官方站 → site-search；deep/wide 仅显式命令。

### Requirement: 主 agent 路由「批量对比/分析 N 个同类对象」到 wide-search
**Reason**: wide-search 改为**显式专属**（仅 `/search-wide` 触发），不再做语义自动派发。
**Migration**: 用户需批量对照时显式跑 `/search-wide`；主 agent 不再因"对比 N 个"语义自动派 wide。

## ADDED Requirements

### Requirement: 对话语义只自动触发快答与 site-search；deep/wide 显式专属
无显式 slash command 时，主 agent SHALL 按对话语义自动派发，且**仅限**两种：①通用 casual 查询（「查一下…」「找几个…」）→ **`/search-fast` 的 AI 综述快答路径**（主 agent 直连 `ai_search.py`，不派 subagent）；②定向官方站语气或命中权威性敏感主题（临床 / 专利 / 学术等）→ site-search。deep-search 与 wide-search MUST **仅**由 `/search-deep` / `/search-wide` 显式触发，**MUST NOT** 由对话语义自动派发。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-28

#### Scenario: 通用 casual 查询触发快答
- **WHEN** 用户说「查一下当前最流行的开源 LLM 推理框架」
- **THEN** 主 agent 直连 `ai_search.py` 出 AI 综述快答，不派 subagent、不要求用户跑 slash command

#### Scenario: 点名官方站触发 site-search
- **WHEN** 用户说「去 react.dev 查 Suspense 的最新用法」
- **THEN** 主 agent 派出 site-search subagent，目标站 react.dev

#### Scenario: 批量对比不自动派 wide，提示显式命令
- **WHEN** 用户说「对比这 10 个 Rust HTTP 框架的吞吐 / 生态」（未用 slash 命令）
- **THEN** 主 agent **不**自动派 wide-search；可一句话提示「批量对照请用 `/search-wide`」（或按需先给快答），不擅自启动 wide

#### Scenario: 深挖不自动派 deep
- **WHEN** 用户说「深入研究 vLLM 的调度器实现」（未用 slash 命令）
- **THEN** 主 agent 不自动派 deep-search；提示用 `/search-deep`，或先给 /search-fast 快答
