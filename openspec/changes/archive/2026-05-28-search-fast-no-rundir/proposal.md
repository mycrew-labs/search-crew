## Why

`/search-fast`（AI 综述快答）不产任何结构化产物文件——给它单独造一个 `/tmp/search-crew/<run_id>/` run 目录，最后里面只剩一个 usage.jsonl，再走一遍 `finalize_usage` 聚合，是多余开销。而每次 backend 调用本来就已写进**永久统一日志** `~/.local/state/search-crew/calls.jsonl`（`usage.py` 查历史读它），不丢任何东西。

per-dispatch run 目录是为「产结构化产物 + 需要隔离 usage-summary」的 subagent 设计的；对一次性、无产物、单次调用的快答，是 over-engineering。

## What Changes

- **`/search-fast` 不再造 run 目录**：命令去掉 `run_paths.py --new` 与 `finalize_usage` 两步，主 agent 直接跑 `ai_search.py`。
- **`ai_search.py` 自报 cost / 调用数**：输出里加 `cost_line`（形如 `📊 本次估算 ~$X USD（1 次调用 · <backend>）`），主 agent 直接拼到回复末尾，无需 finalize_usage。
- **打点照旧进永久统一日志**：ai_search 的 backend 调用经 `_http` → `usage.record` 仍写 `calls.jsonl`（统一日志，历史可查）；不再为快答单独落 per-run 目录。
- **MODIFY orchestration「造 run 目录」locked 需求**：去掉「/search-fast 也造 run 目录」的句子与 scenario——该需求只约束**派 subagent** 的场景（site/deep/wide/worker）；快答不派 subagent、不造目录。

## Capabilities

### Modified Capabilities

- `orchestration`：MODIFY「派 search subagent 前造 run 目录」locked——明确仅适用于派 subagent 的场景；`/search-fast` 直连 ai_search.py，不造 run 目录、cost 由 ai_search 自报、打点进永久 calls.jsonl。

## Impact

- **locked 影响**：MODIFY orchestration「造 run 目录」（user-confirmed），归档前确认。
- **行为变化**：`/search-fast` 不再在 `/tmp/search-crew/` 留 per-dispatch 目录；cost 一行由 ai_search 输出而非 finalize_usage。历史查询（`usage.py`）不受影响（仍读 calls.jsonl）。
- **代码**：`ai_search.py` 加 cost 计算 + `cost_line` 输出；`commands/search-fast.md` 简化为「跑 ai_search → 呈现综述 + 引用 + cost_line」。
- **不动**：deep/wide/site 仍造 run 目录（它们产结构化产物，需要）；evidence-search worker 不变。
