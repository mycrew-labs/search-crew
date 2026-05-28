## ADDED Requirements

### Requirement: 派 search subagent 前造 run 目录并经环境变量下传
主 agent 在派出 search subagent（fast/site/deep/wide）**之前** MUST 用 `run_paths.py --new` 造一个唯一 run 目录，并在派发时通过 `SEARCH_CREW_RUN_ROOT` 环境变量把**目录路径**传给该 subagent。被派的 subagent MUST 在其所有脚本调用前带上该变量、产物写该目录下；lead（deep/wide）再派下级 worker 时 MUST 把同一 `SEARCH_CREW_RUN_ROOT` 原样传下去，使整条派发链的产物 / cost 全落同一目录。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-28

#### Scenario: 主 agent 派发带 run 目录
- **WHEN** 用户触发 `/search-fast <主题>`
- **THEN** 主 agent 先 `run_paths.py --new` 造目录，再派 fast-search 并告知其 `SEARCH_CREW_RUN_ROOT=<目录>`；fast-search 的 search.py / fetch.py / finalize_usage 调用都带该变量

#### Scenario: lead 向 worker 传递 run 目录
- **WHEN** deep-search 收到 `SEARCH_CREW_RUN_ROOT` 后派 fast-search worker
- **THEN** worker 的 Task 派发带同一 `SEARCH_CREW_RUN_ROOT`，worker 产物与打点落 lead 的同一目录
