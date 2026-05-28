## MODIFIED Requirements

### Requirement: 派 search subagent 前造 run 目录并经环境变量下传
主 agent 在派出 search subagent（site/deep/wide，及内部 worker evidence-search）**之前** MUST 用 `run_paths.py --new` 造一个唯一 run 目录，并在派发时通过 `SEARCH_CREW_RUN_ROOT` 环境变量把**目录路径**传给该 subagent。被派的 subagent MUST 在其所有脚本调用前带上该变量、产物写该目录下；lead（deep/wide）再派下级 worker 时 MUST 把同一 `SEARCH_CREW_RUN_ROOT` 原样传下去，使整条派发链的产物 / cost 全落同一目录。本需求**仅约束派 subagent 的场景**；`/search-fast` 直连 `ai_search.py`、不派 subagent，**不造 run 目录**——其打点经 `_http` 照常进永久统一日志 `~/.local/state/search-crew/calls.jsonl`，cost 一行由 `ai_search.py` 自报。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-29

#### Scenario: 派 subagent 造 run 目录
- **WHEN** 用户触发 `/search-deep <主题>`
- **THEN** 主 agent 先 `run_paths.py --new` 造目录，再带 `SEARCH_CREW_RUN_ROOT=<目录>` 派 deep-search

#### Scenario: /search-fast 不造 run 目录
- **WHEN** 用户触发 `/search-fast <主题>`
- **THEN** 主 agent 直接跑 `ai_search.py`（不造 run 目录、不派 subagent）；调用经 `_http` 进永久 calls.jsonl，cost 一行取 ai_search 输出的 `cost_line`

#### Scenario: lead 向 worker 传递 run 目录
- **WHEN** deep-search 收到 `SEARCH_CREW_RUN_ROOT` 后派 evidence-search worker
- **THEN** worker 的 Task 派发带同一 `SEARCH_CREW_RUN_ROOT`，worker 产物与打点落 lead 的同一目录
