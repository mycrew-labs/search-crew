#!/usr/bin/env python3
"""跨 run 用量查询（vibe-usage 模式）。

设计意图（P-USAGE-004）：
- 用户用 `!` 前缀在 Claude Code 中执行；输出直出终端，不进任何 agent context
- 纯本地、无网络、不需要 API key
- 只读 ~/.local/state/search-crew/{calls,runs}.jsonl

CLI:
  python3 usage.py [--last N] [--by-day] [--by-week] [--by-month] [--by-backend] [--since YYYY-MM-DD] [--raw]

默认行为：--last 10
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import sys
from collections import defaultdict
from typing import Any

from lib import config


def _load_jsonl(p: pathlib.Path) -> list[dict[str, Any]]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _parse_iso(ts: str | None) -> _dt.datetime | None:
    if not ts:
        return None
    try:
        return _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _filter_since(records: list[dict[str, Any]], since: _dt.datetime | None) -> list[dict[str, Any]]:
    if not since:
        return records
    out = []
    for r in records:
        ts = _parse_iso(r.get("ts") or r.get("ended_at"))
        if ts and ts >= since:
            out.append(r)
    return out


def _print_table(headers: list[str], rows: list[list[Any]]) -> None:
    if not rows:
        print("（无数据）")
        return
    cols = [str(h) for h in headers]
    widths = [len(h) for h in cols]
    str_rows = [[str(c) for c in r] for r in rows]
    for r in str_rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(c))
    line = "  ".join(c.ljust(widths[i]) for i, c in enumerate(cols))
    print(line)
    print("  ".join("-" * widths[i] for i in range(len(cols))))
    for r in str_rows:
        print("  ".join(c.ljust(widths[i]) for i, c in enumerate(r)))


def cmd_last(runs: list[dict[str, Any]], n: int) -> None:
    sub = runs[-n:][::-1]
    rows = []
    total_cost = 0.0
    total_calls = 0
    for r in sub:
        totals = r.get("totals") or {}
        cost = totals.get("cost_estimate_usd") or 0.0
        calls = totals.get("calls") or 0
        total_cost += cost
        total_calls += calls
        rows.append([r.get("ended_at", "?"), r.get("run_id", "?")[:12] + "…", calls, f"${cost:.4f}"])
    _print_table(["结束时间", "run_id", "次数", "估算 cost"], rows)
    print(f"\n合计：{total_calls} 次调用 / ~${total_cost:.4f} USD")


def cmd_by_period(calls: list[dict[str, Any]], period: str) -> None:
    bucket: dict[str, dict[str, float]] = defaultdict(lambda: {"calls": 0, "cost": 0.0})
    for r in calls:
        ts = _parse_iso(r.get("ts"))
        if not ts:
            continue
        if period == "day":
            key = ts.strftime("%Y-%m-%d")
        elif period == "week":
            iso = ts.isocalendar()
            key = f"{iso[0]}-W{iso[1]:02d}"
        elif period == "month":
            key = ts.strftime("%Y-%m")
        else:
            key = "?"
        bucket[key]["calls"] += 1
        c = r.get("cost_estimate_usd")
        if isinstance(c, (int, float)):
            bucket[key]["cost"] += c
    rows = [[k, int(v["calls"]), f"${v['cost']:.4f}"] for k, v in sorted(bucket.items())]
    _print_table([period, "次数", "估算 cost"], rows)


def cmd_by_backend(calls: list[dict[str, Any]]) -> None:
    bucket: dict[str, dict[str, float]] = defaultdict(lambda: {"calls": 0, "cost": 0.0})
    for r in calls:
        b = r.get("backend", "unknown")
        bucket[b]["calls"] += 1
        c = r.get("cost_estimate_usd")
        if isinstance(c, (int, float)):
            bucket[b]["cost"] += c
    rows = [[b, int(v["calls"]), f"${v['cost']:.4f}"] for b, v in sorted(bucket.items(), key=lambda x: -x[1]["cost"])]
    _print_table(["backend", "次数", "估算 cost"], rows)


def cmd_show_queries(runs: list[dict[str, Any]], calls: list[dict[str, Any]], n: int) -> None:
    """列出最近 N 次 run 的「搜索摘要」段。直接从 calls.jsonl 按 run_id 分组渲染。"""
    sub_runs = runs[-n:][::-1]
    if not sub_runs:
        print("（无 run 记录）")
        return
    run_ids: set[str] = {str(r.get("run_id")) for r in sub_runs if r.get("run_id")}
    calls_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in calls:
        rid = c.get("run_id")
        if isinstance(rid, str) and rid in run_ids:
            calls_by_run[rid].append(c)

    for run in sub_runs:
        rid = run.get("run_id", "?")
        print(f"## run {rid[:12]}… · ended {run.get('ended_at', '?')}\n")
        run_calls = calls_by_run.get(rid, [])
        queries_by_backend: dict[str, list[str]] = defaultdict(list)
        skipped_by_backend: dict[str, list[str]] = defaultdict(list)
        backend_call_count: dict[str, int] = defaultdict(int)
        for c in run_calls:
            b = c.get("backend", "unknown")
            q = (c.get("query") or "").strip()
            if c.get("status") == "call_cap_exceeded":
                skipped_by_backend[b].append(q)
            else:
                backend_call_count[b] += 1
                if q:
                    queries_by_backend[b].append(q)

        if not queries_by_backend and not skipped_by_backend:
            print("（本次 run 无搜索类调用，或调用未携带 query 字段）\n")
            continue

        seen = set()
        for backend in sorted(queries_by_backend.keys()):
            qs = [q for q in queries_by_backend[backend] if not (q in seen or seen.add(q))]
            seen = set(queries_by_backend[backend])
            term_str = "；".join(qs) if qs else "（未记录）"
            print(f"- 网站：{backend} | 查询词：{term_str} | 次数：{backend_call_count[backend]}")
        for backend in sorted(skipped_by_backend.keys()):
            qs = [q for q in skipped_by_backend[backend] if q]
            term_str = "；".join(qs) if qs else "（未记录）"
            print(f"- 已跳过：{backend}，原因：触发站点调用上限（尝试查询词：{term_str}）")
        print()


def main() -> int:
    ap = argparse.ArgumentParser(description="Search Crew 跨 run 用量查询")
    ap.add_argument("--last", type=int, default=None, help="列最近 N 次 run（默认 10）")
    ap.add_argument("--by-day", action="store_true")
    ap.add_argument("--by-week", action="store_true")
    ap.add_argument("--by-month", action="store_true")
    ap.add_argument("--by-backend", action="store_true")
    ap.add_argument(
        "--show-queries",
        action="store_true",
        help="列最近 --last N 次 run 的「搜索摘要」段（网站 / 查询词 / 次数 / 已跳过）",
    )
    ap.add_argument("--since", default=None, help="YYYY-MM-DD")
    ap.add_argument("--raw", action="store_true", help="直接 cat calls.jsonl")
    args = ap.parse_args()

    state = config.state_dir()
    calls = _load_jsonl(state / "calls.jsonl")
    runs = _load_jsonl(state / "runs.jsonl")

    since = None
    if args.since:
        try:
            since = _dt.datetime.fromisoformat(args.since).replace(tzinfo=_dt.timezone.utc)
        except ValueError:
            print(f"--since 格式应为 YYYY-MM-DD：{args.since}", file=sys.stderr)
            return 2
    calls = _filter_since(calls, since)
    runs = _filter_since(runs, since) if since else runs

    if args.raw:
        for r in calls:
            print(json.dumps(r, ensure_ascii=False))
        return 0
    if args.by_day:
        cmd_by_period(calls, "day")
        return 0
    if args.by_week:
        cmd_by_period(calls, "week")
        return 0
    if args.by_month:
        cmd_by_period(calls, "month")
        return 0
    if args.by_backend:
        cmd_by_backend(calls)
        return 0
    if args.show_queries:
        cmd_show_queries(runs, calls, args.last or 10)
        return 0

    cmd_last(runs, args.last or 10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
