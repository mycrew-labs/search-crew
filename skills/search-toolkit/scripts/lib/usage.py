"""调用打点（P-USAGE-001 / 002）。

每次 backend 调用打一条记录：
- `<run_root>/usage.jsonl`（临时，per-run）
- `~/.local/state/search-crew/calls.jsonl`（永久，跨 run）

由 `lib/_http.py` 出口统一调用，业务代码禁绕过。
"""

from __future__ import annotations

import datetime as _dt
import fcntl
import json
import sys
from typing import Any

from . import config, pricing, runtime


def _utc_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"


def _append_jsonl_atomic(path, record: dict[str, Any]) -> None:
    """带文件锁的原子追加。失败仅 stderr 警告，不抛。"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except OSError as e:
        print(f"[usage] 写打点失败 {path}: {e}", file=sys.stderr)


def record(
    *,
    backend: str,
    endpoint: str,
    status: int | str,
    latency_ms: int,
    tokens_or_units: int | None = 1,
    query: str | None = None,
) -> None:
    """统一打点入口（由 _http.py 调用，不要在业务代码里手调）。

    `query` 可选；当 backend 是搜索类（jina / serper / grok / gemini / doubao /
    site-search adapter）时建议传入，用于 finalize_usage.py 渲染「搜索摘要」段。
    """
    sid = runtime.get_session_id()
    subagent = runtime.current_subagent()
    cost, source = pricing.estimate(backend, endpoint, tokens_or_units)

    rec = {
        "ts": _utc_iso(),
        "run_id": sid,
        "subagent": subagent,
        "backend": backend,
        "endpoint": endpoint,
        "status": status,
        "latency_ms": latency_ms,
        "tokens_or_units": tokens_or_units,
        "cost_estimate_usd": cost,
        "pricing_source": source,
        "query": (query or "").strip() or None,
    }

    # 1. per-run 临时
    _append_jsonl_atomic(runtime.run_root(sid) / "usage.jsonl", rec)
    # 2. 永久持久化（vibe-usage 风）
    _append_jsonl_atomic(config.state_dir() / "calls.jsonl", rec)
