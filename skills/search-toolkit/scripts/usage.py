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


def main() -> int:
    ap = argparse.ArgumentParser(description="Search Crew 跨 run 用量查询")
    ap.add_argument("--last", type=int, default=None, help="列最近 N 次 run（默认 10）")
    ap.add_argument("--by-day", action="store_true")
    ap.add_argument("--by-week", action="store_true")
    ap.add_argument("--by-month", action="store_true")
    ap.add_argument("--by-backend", action="store_true")
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

    cmd_last(runs, args.last or 10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
