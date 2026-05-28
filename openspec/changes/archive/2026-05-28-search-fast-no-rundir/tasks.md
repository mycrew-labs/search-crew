## 1. 实现

- [x] 1.1 `ai_search.py`：调用后用 pricing.estimate(backend, endpoint, 1) 算 cost，输出加 `calls`、`cost_estimate_usd`、`cost_line`（`📊 本次估算 ~$X USD（1 次调用 · <backend>）`）；fallback 时 cost_line 标快答未出
- [x] 1.2 `commands/search-fast.md`：删 `run_paths.py --new` 与 `finalize_usage` 两步；直接跑 `ai_search.py`（不带 SEARCH_CREW_RUN_ROOT），回复用 summary+citations，cost 行取输出的 `cost_line`

## 2. 测试

- [x] 2.1 `ai_search.py` 单测补：输出含 cost_line + calls；fallback 分支
- [x] 2.2 全量 unittest 通过

## 3. 验证 + 归档

- [x] 3.1 `openspec validate search-fast-no-rundir --strict` 通过
- [x] 3.2 完工简报：MODIFY orchestration「造 run 目录」locked（去掉 /search-fast 造目录）；确认 → bump → archive → commit → push
- [ ] 3.3 **manual** reload 实测：/search-fast 跑完 `/tmp/search-crew/` 不留新目录；cost 一行正常；`usage.py --last` 仍能看到这次调用
