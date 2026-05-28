#!/usr/bin/env python3
"""打印本次 run 的规范目录，供 subagent 在「未被上级指定 target_dir」时取用。

用法：
    run_paths.py --new            # 造一个新的 per-dispatch run 目录并打印其路径（派发方派 subagent 前用）
    run_paths.py                  # 打印当前 run_root（按 SEARCH_CREW_RUN_ROOT > RUN_ID > 会话 id）
    run_paths.py --subagent fast-search
                                  # 打印 <run_root>/fast-search/

派发方（主 agent / lead）每次 `/search-*` 跑 `--new` 造目录，把**目录路径**经
`SEARCH_CREW_RUN_ROOT` 传给 subagent 并沿派发链下传——一次派发的 lead + 所有 worker
产物 / usage 打点 / summary 全落同一目录。subagent 不用自己拼 id（避免与打点分叉致
cost 读不到的老 bug）。
"""

from __future__ import annotations

import argparse
import sys

from lib import runtime


def main() -> int:
    ap = argparse.ArgumentParser(description="打印本次 run 的规范目录 / 生成新 run id")
    ap.add_argument("--subagent", default=None, help="子 agent 名；给了就打印 run_root/<subagent>/")
    ap.add_argument("--new", action="store_true",
                    help="造一个新的 per-dispatch run 目录并打印其路径（派发方派 subagent 前用，"
                         "把该路径经 SEARCH_CREW_RUN_ROOT 传给 subagent 并沿派发链下传）")
    args = ap.parse_args()

    if args.new:
        # 造目录、打印路径（不是 id）——subagent 直接拿目录用，无需自己拼
        print(str(runtime.run_root(runtime.new_run_id())))
        return 0

    root = runtime.run_root()
    if args.subagent:
        target = root / args.subagent
        target.mkdir(parents=True, exist_ok=True)
        print(str(target))
    else:
        print(str(root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
