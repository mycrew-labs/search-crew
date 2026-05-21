#!/usr/bin/env python3
"""首次安装：把 plugin 内置 defaults/ 拷贝到 ~/.config/search-crew/。

约束（T-SEED-001）：
- 用 if-not-exists 守卫，绝不覆盖已有文件
- 用文件锁防并发
- 多次调用幂等
"""

from __future__ import annotations

import fcntl
import os
import pathlib
import shutil
import sys

from lib import config


def _plugin_root() -> pathlib.Path:
    """从环境变量取 $CLAUDE_PLUGIN_ROOT；否则按本脚本路径推断。"""
    root = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    if root:
        return pathlib.Path(root)
    # 本脚本位于 plugin/skills/search-toolkit/scripts/seed_user_config.py
    # 向上数 4 层到 plugin root
    return pathlib.Path(__file__).resolve().parents[3]


def _defaults_dir() -> pathlib.Path:
    return _plugin_root() / "defaults"


def _copy_if_not_exists(src: pathlib.Path, dst: pathlib.Path) -> int:
    """返回新增的文件数。"""
    count = 0
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            count += _copy_if_not_exists(child, dst / child.name)
    else:
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            count += 1
    return count


def main() -> int:
    src = _defaults_dir()
    if not src.exists():
        print(f"[seed] defaults/ 不存在：{src}", file=sys.stderr)
        return 1

    dst = config.active_dir()
    dst.mkdir(parents=True, exist_ok=True)

    # 文件锁防并发
    lock_path = dst / ".seed.lock"
    with open(lock_path, "w", encoding="utf-8") as lock_f:
        try:
            fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
            new_count = _copy_if_not_exists(src, dst)
            print(f"[seed] 从 {src} → {dst}，新增 {new_count} 个文件", file=sys.stderr)
        finally:
            fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)

    # 标记完成
    (dst / ".seeded").touch()
    return 0


if __name__ == "__main__":
    sys.exit(main())
