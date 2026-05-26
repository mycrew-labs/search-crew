#!/usr/bin/env python3
"""首次安装：把 plugin 内置 defaults/ 拷贝到 ~/.config/search-crew/。

约束（T-SEED-001）：
- 默认 if-not-exists 守卫，绝不覆盖已有文件
- 用文件锁防并发
- 多次调用幂等

`--merge` 子模式（borrow-smart-search-web-reader change 引入）：plugin 升级后
defaults/ 多出来的 YAML 顶层段（如新增的 `ai_summary:` / `call_cap:`），active
中缺失这些段时自动补齐；用户已有段一字不动。
"""

from __future__ import annotations

import argparse
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


_TOP_LEVEL_KEY = __import__("re").compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:")


def _split_top_level_blocks(text: str) -> dict[str, str]:
    """把 YAML 文本按顶层 key 切块，返回 {key: 文本块（含尾部空行）}。

    顶层 key 定义为「行首无缩进且包含冒号」的行。每个 block 含该行 + 所有缩进续行
    + 之后的纯空行 / 注释行（直到下一个顶层 key）。

    极简实现，足够 routing.yaml / limits.yaml / pricing.yaml 这类扁平 + 一层嵌套
    的配置文件。
    """
    lines = text.splitlines(keepends=True)
    blocks: dict[str, str] = {}
    current_key: str | None = None
    current_buf: list[str] = []
    for line in lines:
        is_top = bool(_TOP_LEVEL_KEY.match(line)) and line[0] not in (" ", "\t")
        if is_top:
            if current_key is not None:
                blocks[current_key] = "".join(current_buf)
            m = _TOP_LEVEL_KEY.match(line)
            assert m is not None
            current_key = m.group(1)
            current_buf = [line]
        else:
            # 续行（缩进 / 空行 / 顶层注释）归到当前 block
            if current_key is None:
                # 文件开头的注释 / 空行 / metadata（如 last_updated）；用特殊 key "__preamble__"
                blocks.setdefault("__preamble__", "")
                blocks["__preamble__"] += line
            else:
                current_buf.append(line)
    if current_key is not None:
        blocks[current_key] = "".join(current_buf)
    return blocks


def _merge_yaml_file(src_path: pathlib.Path, dst_path: pathlib.Path) -> list[str]:
    """把 src 里 dst 缺失的顶层 key 块追加到 dst 末尾。

    返回追加的 key 列表（用于日志）。dst 中已有的 key 一字不动；preamble（顶部
    注释 / metadata）一字不动。
    """
    if not dst_path.exists():
        return []  # 完全缺失走普通 copy，不算 merge
    src_text = src_path.read_text(encoding="utf-8")
    dst_text = dst_path.read_text(encoding="utf-8")
    src_blocks = _split_top_level_blocks(src_text)
    dst_blocks = _split_top_level_blocks(dst_text)

    appended: list[str] = []
    suffix_chunks: list[str] = []
    for key in src_blocks:
        if key == "__preamble__":
            continue
        if key in dst_blocks:
            continue
        appended.append(key)
        suffix_chunks.append(src_blocks[key])

    if appended:
        new_text = dst_text
        if not new_text.endswith("\n"):
            new_text += "\n"
        new_text += "\n# ---- 以下段由 seed_user_config.py --merge 从 plugin defaults 补齐 ----\n"
        new_text += "".join(suffix_chunks)
        dst_path.write_text(new_text, encoding="utf-8")
    return appended


def _do_merge() -> int:
    """扫 defaults/*.yaml，对每个 active 已存在的同名文件做顶层 key merge。"""
    src_dir = _defaults_dir()
    dst_dir = config.active_dir()
    if not dst_dir.exists():
        print(f"[seed --merge] active 不存在 {dst_dir}，请先跑普通 seed", file=sys.stderr)
        return 1
    any_change = False
    for src in src_dir.glob("*.yaml"):
        dst = dst_dir / src.name
        added = _merge_yaml_file(src, dst)
        if added:
            any_change = True
            print(f"[seed --merge] {dst.name} 补齐 {len(added)} 段：{', '.join(added)}", file=sys.stderr)
        else:
            print(f"[seed --merge] {dst.name} 无需补齐", file=sys.stderr)
    if not any_change:
        print("[seed --merge] 所有 active YAML 已与 defaults 同步", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Search Crew seed_user_config")
    ap.add_argument(
        "--merge",
        action="store_true",
        help="为已存在的 active YAML 补齐 defaults 中新增的顶层段（用户已有段一字不动）",
    )
    args = ap.parse_args()

    if args.merge:
        return _do_merge()

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
