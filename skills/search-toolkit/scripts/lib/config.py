"""用户态 active 配置加载（routing / pricing / limits / adapters）。

约束（P-CONFIG-001）：
- runtime 只读 `~/.config/search-crew/`
- 不存在则自动调 seed_user_config.py 一次（兜底）
- 永不读 plugin 内置 defaults/（除 seed 时）
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
from typing import Any

from . import _yaml


def _xdg_config_home() -> pathlib.Path:
    base = os.environ.get("XDG_CONFIG_HOME") or "~/.config"
    return pathlib.Path(base).expanduser()


def _xdg_state_home() -> pathlib.Path:
    base = os.environ.get("XDG_STATE_HOME") or "~/.local/state"
    return pathlib.Path(base).expanduser()


def active_dir() -> pathlib.Path:
    return _xdg_config_home() / "search-crew"


def state_dir() -> pathlib.Path:
    d = _xdg_state_home() / "search-crew"
    d.mkdir(parents=True, exist_ok=True)
    return d


def pending_dir() -> pathlib.Path:
    d = active_dir() / "pending"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ensure_seeded() -> None:
    """active 目录不存在时调 seed 脚本兜底拷贝。"""
    if active_dir().exists():
        return
    seed_script = pathlib.Path(__file__).parent.parent / "seed_user_config.py"
    if not seed_script.exists():
        print(
            f"[config] seed_user_config.py 缺失，无法兜底 seed；请手动创建 {active_dir()}",
            file=sys.stderr,
        )
        return
    try:
        subprocess.run([sys.executable, str(seed_script)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[config] seed 失败：{e}", file=sys.stderr)


def _load_yaml(name: str) -> dict[str, Any]:
    _ensure_seeded()
    path = active_dir() / name
    if not path.exists():
        return {}
    try:
        return _yaml.load_file(path) or {}
    except _yaml.YamlSubsetError as e:
        print(f"[config] {name} 解析失败：{e}", file=sys.stderr)
        return {}


def load_routing() -> dict[str, Any]:
    return _load_yaml("routing.yaml")


def load_pricing() -> dict[str, Any]:
    return _load_yaml("pricing.yaml")


def load_limits() -> dict[str, Any]:
    return _load_yaml("limits.yaml")


def load_pending() -> dict[str, list[pathlib.Path]]:
    """扫描 pending/ 下所有候选条目。"""
    result: dict[str, list[pathlib.Path]] = {"routing": [], "adapters": []}
    p = pending_dir()
    for kind in result:
        sub = p / kind
        if sub.exists():
            result[kind] = sorted(sub.glob("*.yaml"))
    return result


def adapter_dirs() -> list[pathlib.Path]:
    """用户态 adapters 目录（plugin 内置 sites/ 由 sites/__init__.py 独立处理）。"""
    _ensure_seeded()
    d = active_dir() / "adapters"
    return [d] if d.exists() else []
