"""运行时上下文（run-id / run-root / session-id）。

I-DATA-001：run 产物落在 `/tmp/search-crew/<run_id>/`。
**run_id 是"一次派发"的隔离单位**，口径：`SEARCH_CREW_RUN_ID（非空）> CLAUDE_CODE_SESSION_ID
> 时间戳兜底`。派发方（主 agent / lead）每次 `/search-*` 生成一个唯一 id 经 `SEARCH_CREW_RUN_ID`
传给 subagent，并沿派发链下传，使一次派发的 lead + 所有 worker 共享一个 run_root；
usage 打点、call-cap、产物目录都用这个口径，三者一致。未显式给 id 时回落会话级（向后兼容）。
subagent **不要**自己编 id——未拿到 target_dir 时调 `run_paths.py --subagent <name>` 取规范目录。
"""

from __future__ import annotations

import os
import pathlib
import secrets
import sys
import time


def run_id() -> str:
    """一次派发的 run 标识 = run_root 的目录名。

    与 `_http._run_id` / `usage.record` / `run_paths` 共用同一口径（都从 `_run_root_path()`
    取目录名），保证 cost / call-cap / 产物目录三者一致。
    """
    return _run_root_path().name


def _run_root_path() -> pathlib.Path:
    """本次 run 的根目录（不 mkdir）。

    口径：`SEARCH_CREW_RUN_ROOT（目录路径，主用）> /tmp/search-crew/<SEARCH_CREW_RUN_ID>
    > /tmp/search-crew/<会话 id>`。派发方每次 `/search-*` 用 `run_paths.py --new` 造好目录、
    把**目录路径**经 `SEARCH_CREW_RUN_ROOT` 传给 subagent，沿派发链下传——产物、usage.jsonl、
    usage-summary 全落这一个目录，subagent 无需自己拼会话 id。
    """
    root_env = os.environ.get("SEARCH_CREW_RUN_ROOT", "").strip()
    if root_env:
        return pathlib.Path(root_env)
    rid = os.environ.get("SEARCH_CREW_RUN_ID", "").strip() or get_session_id()
    return pathlib.Path("/tmp/search-crew") / rid


def new_run_id() -> str:
    """生成一个新的 per-dispatch run id：`<UTCYYYYMMDDThhmmss>-<6hex>`（形态区别于会话 uuid）。"""
    ts = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    return f"{ts}-{secrets.token_hex(3)}"


def get_session_id() -> str:
    """按 T-SESSION-001 的优先级返回 session-id。"""
    # 1. Claude Code 注入的环境变量
    for var in ("CLAUDE_SESSION_ID", "CLAUDE_CODE_SESSION_ID"):
        v = os.environ.get(var, "").strip()
        if v:
            return v

    # 2. 文件 marker（plugin 可能放在 $CLAUDE_PLUGIN_ROOT/.session-marker）
    root = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    if root:
        marker = pathlib.Path(root) / ".session-marker"
        if marker.exists():
            try:
                v = marker.read_text(encoding="utf-8").strip()
                if v:
                    return v
            except OSError:
                pass

    # 3. 时间戳 + 短随机串兜底
    fallback = f"{int(time.time())}-{secrets.token_hex(4)}"
    print(
        f"[runtime] 未拿到 CLAUDE_SESSION_ID，使用时间戳兜底: {fallback}",
        file=sys.stderr,
    )
    return fallback


def run_root(rid: str | None = None) -> pathlib.Path:
    """返回本 run 的根目录并 mkdir。

    给了 `rid` → `/tmp/search-crew/<rid>/`；否则按 `_run_root_path()` 口径
    （SEARCH_CREW_RUN_ROOT > SEARCH_CREW_RUN_ID > 会话 id）。
    """
    p = (pathlib.Path("/tmp/search-crew") / rid) if rid else _run_root_path()
    p.mkdir(parents=True, exist_ok=True)
    return p


def current_subagent() -> str:
    """从环境变量推断当前 subagent 名（用于打点）。

    Claude Code 未明确暴露此变量时返回 'unknown'；agent 在调脚本时可显式传
    `SEARCH_CREW_SUBAGENT` 环境变量覆盖。
    """
    for var in ("SEARCH_CREW_SUBAGENT", "CLAUDE_SUBAGENT_NAME"):
        v = os.environ.get(var, "").strip()
        if v:
            return v
    return "unknown"
