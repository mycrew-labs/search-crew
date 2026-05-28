## 1. 运行时口径统一（lib）

- [x] 1.1 `lib/runtime.py`：`_run_root_path()`=`SEARCH_CREW_RUN_ROOT > /tmp/search-crew/<RUN_ID> > 会话 id`；`run_root()` 走它；`run_id()`=目录名；更新文件头注释
- [x] 1.2 `lib/usage.py` `record()` 把 `runtime.get_session_id()` 改为 `runtime.run_id()`
- [x] 1.3 `lib/_http.py` `_run_id()` 复用 `runtime.run_id()`（去重，同口径）

## 2. 造 run 目录的入口

- [x] 2.1 `run_paths.py` 加 `--new`：造目录并打印**路径**（不是 id）
- [x] 2.2 `run_paths.py`（无 --new）按 `run_root()` 打印 run_root / `--subagent` 子目录

## 3. 命令 + agent prompt 传递 run 目录

- [x] 3.1 `commands/search-fast.md`：派发前 `run_paths.py --new` 拿目录，Task 派发传 `SEARCH_CREW_RUN_ROOT=<目录>`；finalize 用本次 run_root（去掉 `--subagent`）
- [x] 3.2 `commands/search-deep.md`、`commands/search-wide.md`：同上，派发前造目录并传入
- [x] 3.3 `agents/fast-search.md`、`site-search.md`：收到 `SEARCH_CREW_RUN_ROOT` 在所有脚本调用前带上、产物写该目录
- [x] 3.4 `agents/deep-search.md`、`wide-search.md`：收到后带上，且**派下级 worker 时把同一 `SEARCH_CREW_RUN_ROOT` 传下去**

## 4. charter / 文档

- [x] 4.1 改 `openspec/USER_DESIGN.md` 的 `I-DATA-001`：`/tmp/search-crew/<session_id>/` → `/tmp/search-crew/<run_id>/`（缺省回落 session_id）——**MUST 先经用户确认**
- [x] 4.2 README / SKILL.md：补 run id 模型说明（每次派发独立 run_root）；更新 0.5.1 会话级的旧表述
- [x] 4.3 `tests/MANUAL.md` 补：一次 /search-deep 的 lead+worker 落同一 run_root；两次 /search-fast 互不累计 cost

## 5. 测试

- [x] 5.1 `lib/runtime.run_id()` 单测：env 优先级（SEARCH_CREW_RUN_ID > session > 兜底）
- [x] 5.2 `--new` 输出格式 + 每次唯一
- [x] 5.3 usage.record 用 run_id：设 SEARCH_CREW_RUN_ID 后打点落对应 run_root（回归 0.5.1 那个分叉 bug 的反向验证）
- [x] 5.4 全量 `unittest discover` 通过

## 6. 归档前：锁确认 gate

- [x] 6.1 `openspec validate per-dispatch-run-id --strict` 通过
- [x] 6.2 完工简报：MODIFY charter `I-DATA-001`（user-owned）；usage-tracking / orchestration 新需求拟落 user-confirmed 锁；逐条确认；声明反转 0.5.1 会话级模型
- [x] 6.3 用户确认 → 落锁 + 改 charter → bump version → `openspec archive` → commit → push
- [ ] 6.4 **manual** · reload 后实测：/search-fast 跑两次看 cost 各自独立不累计；/search-deep 看 lead+worker 同 run_root + cost 含 worker
