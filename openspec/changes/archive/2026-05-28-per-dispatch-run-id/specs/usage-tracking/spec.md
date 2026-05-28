## ADDED Requirements

### Requirement: 每次显式搜索派发使用独立 run id 隔离用量
一次 `/search-*` 派发（lead 及其派出的所有 worker）MUST 共享一个**唯一 run 目录**，本次派发的 usage 打点、call-cap 计数、产物、usage-summary MUST 全部落在这一个目录下，与同会话的其它派发互不混淆。派发方用 `run_paths.py --new` 造好目录、把**目录路径**经 `SEARCH_CREW_RUN_ROOT` 环境变量传给 subagent 并沿派发链下传（subagent 不再自己拼会话 id）。run 目录的解析口径 MUST 统一为 `SEARCH_CREW_RUN_ROOT（目录路径，主用）> /tmp/search-crew/<SEARCH_CREW_RUN_ID> > /tmp/search-crew/<会话 id>`；run_id（打点字段 / call-cap 键）MUST 取该目录的名字；`lib/usage.py` 打点、`run_paths.py` 取目录、`_http` 的 call-cap MUST 都用这一口径。未显式提供时 MUST 回落会话级（向后兼容）。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-28

#### Scenario: 一次派发的 lead 与 worker 同 run_root
- **WHEN** 主 agent 造好 run 目录派出 deep-search，deep-search 把同一 `SEARCH_CREW_RUN_ROOT` 传给 fast-search worker
- **THEN** lead 与 worker 的 usage.jsonl / 产物落同一目录，`finalize_usage <run_root>` 得到的是本次派发（含 worker）的合计

#### Scenario: 打点口径与 call-cap / 产物一致
- **WHEN** 设置了 `SEARCH_CREW_RUN_ROOT=<目录>`
- **THEN** usage.jsonl 落该目录、usage.record 写入的 run_id = 该目录名、call-cap 计数键 = 该目录名，三者一致

#### Scenario: 未给 run 目录时回落会话级
- **WHEN** 直接跑脚本、未设 `SEARCH_CREW_RUN_ROOT` 也未设 `SEARCH_CREW_RUN_ID`
- **THEN** run 目录回落 `/tmp/search-crew/<CLAUDE_CODE_SESSION_ID>`（再无则时间戳兜底），脚本正常工作
