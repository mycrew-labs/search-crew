## Context

三处「run 标识」现状：
- `_http._run_id()`：`SEARCH_CREW_RUN_ID > runtime.get_session_id() > PID`（call-cap 用）
- `lib/usage.py` 打点：直接 `runtime.get_session_id()`（= `CLAUDE_CODE_SESSION_ID`，会话级）
- `run_paths.py` / 产物目录：`runtime.run_root()` → `get_session_id()`（0.5.1 起会话级）

会话级让一次派发无法隔离。Claude Code 不给 subagent 独立 id，但**派发方（主 agent / lead）可以自己生成一个 id 并经环境变量传给被派的 subagent**——这就是 per-dispatch id 的落点。

## Goals / Non-Goals

**Goals:**
- 一次 `/search-*` 派发（含其派出的 worker）共享一个唯一 run id；cost / call-cap / 产物按它隔离。
- 三处 run 标识口径统一：`SEARCH_CREW_RUN_ID > CLAUDE_CODE_SESSION_ID > 时间戳兜底`。
- 未显式给 id 时回落会话级 / 兜底，直接跑脚本仍工作（向后兼容）。

**Non-Goals:**
- 不改 usage locked 需求的产物形态（usage.jsonl / usage-summary.md / calls.jsonl / 一行 cost）——只改 run_root 粒度。
- 不追求"跨工具进程的强一致 id 分发"——靠 prompt 纪律传递（与 `SEARCH_CREW_SUBAGENT` 同一脆弱面），漏传则退化为会话级，不致命。
- 不引入持久守护进程 / 全局状态。

## Decisions

### D1：run **目录**由派发方造好，传目录路径（不是 id）
- `run_paths.py --new`：造目录 `/tmp/search-crew/<UTCYYYYMMDDThhmmss>-<6hex>/` 并打印其**路径**（id 形态区别于会话 uuid，便于人眼识别"一次派发"）。
- 主 agent 在派 search subagent **前**跑它拿目录，在 Task prompt 里告知：「本次 `SEARCH_CREW_RUN_ROOT=<目录>`，所有脚本调用前带上它、产物写该目录；你再派下级时原样传下去」。
- lead（deep/wide）收到后，派 worker 的 Task prompt 里带同一个目录。
- **传目录而非 id 的好处**（用户提的简化）：subagent 不用再把 id 拼成路径；所有产物 + usage-summary 保证落同一目录，事后好查。

### D2：目录口径统一到 `runtime._run_root_path()`
- `lib/runtime.py`：`_run_root_path()` = `SEARCH_CREW_RUN_ROOT(目录) > /tmp/search-crew/<SEARCH_CREW_RUN_ID> > /tmp/search-crew/<会话 id>`；`run_root()` 走它（mkdir）；`run_id()` = `_run_root_path().name`（打点字段 / call-cap 键）。
- `lib/usage.py` 的 `record()` 把 `runtime.get_session_id()` 改为 `runtime.run_id()`——修「打点口径与 call-cap/产物不一致」的关键。
- `_http._run_id()` 改为复用 `runtime.run_id()`（同口径，去重）。
- `get_session_id()` 保留（作为目录口径的最末回落项）；`SEARCH_CREW_RUN_ID`（纯 id）保留为兼容回落。

### D3：run_paths 取目录走同口径
`run_paths.py --subagent X` 打印 `run_root()/X`。subagent 设了 `SEARCH_CREW_RUN_ROOT` 后，产物与打点自然同根。

### D4：向后兼容回落
- 不带 `SEARCH_CREW_RUN_ID` → `run_id()` 回落 `CLAUDE_CODE_SESSION_ID`（会话级，旧行为）→ 再无则时间戳兜底。
- 0.5.4 的 `finalize_usage --subagent` 切片保留（per-dispatch 下 fast-search run_root 内本就只这一个 subagent，切不切等价；deep/wide 用整 run_root 即本次派发，不要 `--subagent`）。

### D5：charter I-DATA-001 措辞
`/tmp/search-crew/<session_id>/` → `/tmp/search-crew/<run_id>/`（run_id 缺省回落 session_id）。属用户所有的 charter 不变量，归档前确认。

## Risks / Trade-offs

- **id 传递靠 prompt 纪律**：subagent 须在每次脚本调用带 `SEARCH_CREW_RUN_ID`、派下级时传下去。漏传 → 该次回落会话级（cost 又会累计，但不报错）。缓解：prompt 明确写、关键约束列一条；与已有 `SEARCH_CREW_SUBAGENT` 同款风险，可接受。
- **反转会话级**：0.5.1~0.5.4 的会话级 + `--subagent` 切片是过渡方案；本 change 取代它。`I-DATA-001` charter 要改（用户确认）。
- **多次派发产生多个 run_root 目录**：`/tmp/search-crew/` 下目录变多（每次派发一个）。`/tmp` 本就临时，可接受；如需可加清理脚本（非本期）。
