"""Backend 单价加载与估算（P-USAGE-003）。

从 `~/.config/search-crew/pricing.yaml` 加载用户态单价。
"""

from __future__ import annotations

from typing import Any

from . import config


_cache: dict[str, Any] | None = None


def _table() -> dict[str, Any]:
    global _cache
    if _cache is None:
        _cache = config.load_pricing() or {}
    return _cache


def estimate(
    backend: str,
    endpoint: str,
    units: int | None = 1,
) -> tuple[float | None, str]:
    """返回 (cost_estimate_usd, pricing_source)。

    pricing_source:
        - "active"  ：用户态 pricing.yaml 命中
        - "zero"    ：在 zero_cost 列表里（fallback / 本地工具）
        - "unknown" ：未配置 → cost = None
    """
    t = _table()

    # zero_cost 列表
    zero = set((t.get("zero_cost") or []))
    if backend in zero or f"{backend}-{endpoint}" in zero:
        return 0.0, "zero"

    section = t.get(backend)
    if not isinstance(section, dict):
        return None, "unknown"

    unit_price = section.get(endpoint)
    if unit_price is None:
        return None, "unknown"

    try:
        return float(unit_price) * float(units or 1), "active"
    except (TypeError, ValueError):
        return None, "unknown"


def reset_cache() -> None:
    """测试 / 用户改完 pricing.yaml 后强制重读。"""
    global _cache
    _cache = None
