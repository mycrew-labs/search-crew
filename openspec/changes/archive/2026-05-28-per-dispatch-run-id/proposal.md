## Why

当前 run 模型是**会话级**（0.5.1 起）：run_root = `/tmp/search-crew/<CLAUDE_CODE_SESSION_ID>/`，整个会话所有 `/search-*` 派发共享一个 run_root + usage.jsonl + call-cap 计数。当时为「改动小」选了它，但实测暴露三个反复出现的问题：

1. **deep/wide 的 cost 无法干净归集**：lead + 它派的 worker 各按自己的 subagent 名打点，按单一 subagent 切片会漏算 worker；按整 run 又混进同会话其它派发。
2. **call-cap 串会话**：`_http` 的调用上限按 run_id 计，会话级 run_id 让上限在整个会话累计，跨多次搜索互相干扰。
3. **cost 行累计虚高**：`/search-fast` 的 cost 行会把整个会话的历史调用都算进来（曾显示「118 次调用 · 77 次触发上限」，其实本次只十几次）。0.5.4 用 `--subagent` 切片只能缓解 fast-search（叶子），治不了 deep/wide。

根因：「一次 run」被定义成「一次会话」，而真正想要的隔离单位是「一次显式搜索派发」。本 change 把 run 模型改为 **per-dispatch task id**：每次 `/search-*` 生成一个唯一 id，本次派发全过程（含其派出的 worker）的 cost / call-cap / 产物都归到这个 id，subagent 互调时把 id 传下去。

## What Changes

- **每次 `/search-*` 派发造一个唯一 run 目录**：主 agent 在派 subagent 前用 `run_paths.py --new` 造目录 `/tmp/search-crew/<utc-时间>-<随机>/`，把**目录路径**作为 `SEARCH_CREW_RUN_ROOT` 传给被派的 subagent（传目录而非 id，subagent 不用再拼路径）。
- **目录沿派发链向下传递**：lead（deep/wide）派 worker（fast/site）时，把收到的 `SEARCH_CREW_RUN_ROOT` 原样传给 worker（与现在传 `SEARCH_CREW_SUBAGENT` 同一套路）。于是一次派发的 lead + 所有 worker 的产物 / cost 全落同一目录。
- **run_root / 打点 / call-cap 统一口径**：`runtime`、`lib/usage.py`、`_http` 统一从 `SEARCH_CREW_RUN_ROOT（目录路径）> /tmp/search-crew/<SEARCH_CREW_RUN_ID> > 会话 id` 取目录；run_id（打点字段 / call-cap 键）取该目录名。未显式给时回落会话级（向后兼容直接跑脚本）。
- **finalize 即本次派发**：`finalize_usage.py <run_root>` 在 per-dispatch 目录上跑 = 这一次派发的精确 cost，deep/wide 也准（worker 落同一目录）。0.5.4 的 `--subagent` 切片对 fast-search 不再必需（保留无害）。
- **命令更新**：`/search-fast`、`/search-deep`、`/search-wide` 在派发前造目录并传 `SEARCH_CREW_RUN_ROOT`；各 subagent prompt 增加「收到 `SEARCH_CREW_RUN_ROOT` 就在所有脚本调用前带上它、产物写该目录，并在派下级时传下去」。

## Capabilities

### Modified Capabilities

- `usage-tracking`：ADD「每次显式搜索派发使用独立 run id，本次派发（含其 worker）的 cost/call-cap/产物归到该 id」。现有 locked 需求（`<run_root>/usage.jsonl`、finalize、permanent calls.jsonl、call-cap）行为不变，只是 run_root 的粒度从会话级变为派发级。
- `orchestration`：ADD「主 agent 派 search subagent 前生成 task run id 并经环境变量传入；subagent 互调时传递」。
- `config-lifecycle` / charter `I-DATA-001`：产物目录从 `/tmp/search-crew/<session_id>/` 改为 `/tmp/search-crew/<run_id>/`（run_id 缺省回落 session_id）。`I-DATA-001` 是 charter 不变量（用户所有），措辞需 MODIFY，归档前确认。

## Impact

- **代码/产物**：新增"生成 run id"的脚本入口（`run_paths.py --new` 或新脚本）；`lib/runtime.py` 加 `run_id()` 口径、`lib/usage.py` 改用它；`commands/search-{fast,deep,wide}.md` 派发前生成+传 id；四个 agent prompt 增加「带 `SEARCH_CREW_RUN_ID` + 向下传」。
- **反转 0.5.1 的会话级模型**：run_paths/runtime 的「会话共用一个 run_root」注释与行为改为「优先 per-dispatch id」。`I-DATA-001` charter 措辞 MODIFY（用户确认）。
- **向后兼容**：未显式给 `SEARCH_CREW_RUN_ID` 时回落会话级 / 时间戳兜底，直接跑脚本仍工作；usage locked 需求行为不变。
- **call-cap**：从会话级回到派发级——更符合「防一次调研内反复追打同一源」的原意，且不再跨派发互相干扰。
- **风险**：id 传递靠 prompt 纪律（LLM 须在每次脚本调用带 env、派下级时传）；漏传则该次回落会话级（退化不致命）。与现有 `SEARCH_CREW_SUBAGENT` 同一脆弱面。
