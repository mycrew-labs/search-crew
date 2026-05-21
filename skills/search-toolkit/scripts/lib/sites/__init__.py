"""站点适配器注册表 + 加载顺序。

加载顺序（T-ADAPTER-001）：
1. plugin 内置代码型适配器（本目录的 *.py，REGISTRY 显式注册）
2. 用户态代码型（`~/.config/search-crew/adapters/*.py`）
3. 用户态 YAML 配置型（`~/.config/search-crew/adapters/*.yaml`）

同 host 后者覆盖前者。
"""

from __future__ import annotations

import importlib.util
import pathlib
from typing import Any, Callable

from . import algolia, github, mdn, npm, pypi, readthedocs, _yaml_adapter
from .. import config

SearchFn = Callable[..., list]


# 1. plugin 内置代码型适配器
BUILTIN_REGISTRY: dict[str, SearchFn] = {
    github.SITE: github.search,
    mdn.SITE: mdn.search,
    pypi.SITE: pypi.search,
    npm.SITE: npm.search,
    "www.npmjs.com": npm.search,
    readthedocs.SITE: readthedocs.search,
    "readthedocs.org": readthedocs.search,
}


# Algolia DocSearch 已知索引：站点 → (app_id, api_key, index_name)
# 这些 key 是站点公开的搜索 key（从浏览器开发者工具可抓到）
ALGOLIA_INDEXES: dict[str, tuple[str, str, str]] = {
    "react.dev": ("1FCF9AYYAT", "5d8d92f3fe6a6a98cf0c7b8a4c0a4e98", "beta-react"),
    "tailwindcss.com": ("KNPXZI5B0M", "5fc87cef58bb80203d2207578309fab6", "tailwindcss"),
    "www.typescriptlang.org": ("BGCDYOIYZ5", "37ee06fa68db6aef451a490df6df7c60", "typescriptlang"),
    "vuejs.org": ("ML0LEBN7FQ", "f49cbd92a74532cc55cfbffa5e5a7d01", "vuejs-v3"),
    "vitejs.dev": ("7H67QR5P0A", "deaab78bcdfe96b599497d25acc6460e", "vitejs"),
}


def _normalize_host(site: str) -> str:
    return site.lower().replace("https://", "").replace("http://", "").split("/")[0]


def _load_user_python_adapters() -> dict[str, SearchFn]:
    """扫描用户态 *.py 适配器。每个模块必须定义 `SITE` 和 `search`。"""
    registry: dict[str, SearchFn] = {}
    for d in config.adapter_dirs():
        for py in d.glob("*.py"):
            if py.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(f"user_adapter_{py.stem}", py)
            if not spec or not spec.loader:
                continue
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                import sys

                print(f"[sites] 用户适配器 {py} 加载失败: {e}", file=sys.stderr)
                continue
            site = getattr(mod, "SITE", None)
            fn = getattr(mod, "search", None)
            if site and callable(fn):
                registry[_normalize_host(site)] = fn
    return registry


def _load_user_yaml_adapters() -> dict[str, SearchFn]:
    """扫描用户态 *.yaml 适配器。"""
    registry: dict[str, SearchFn] = {}
    for d in config.adapter_dirs():
        for yml in d.glob("*.yaml"):
            try:
                # 加载一次只为拿 site 字段
                from .. import _yaml as _y

                cfg = _y.load_file(yml) or {}
                site = cfg.get("site")
                if not site:
                    continue

                def _make(p: pathlib.Path) -> SearchFn:
                    def _fn(query: str, *, max_results: int = 10, **_: Any) -> list[dict[str, Any]]:
                        return _yaml_adapter.search_from_yaml(p, query, max_results=max_results)

                    return _fn

                registry[_normalize_host(site)] = _make(yml)
            except Exception as e:
                import sys

                print(f"[sites] 用户 YAML 适配器 {yml} 加载失败: {e}", file=sys.stderr)
    return registry


def get_adapter(site: str) -> SearchFn | None:
    """按 host 查询适配器。优先级：用户 YAML > 用户 Python > Algolia 兜底 > 内置 Python。"""
    host = _normalize_host(site)

    # 用户态优先（用户后写的覆盖内置）
    yaml_reg = _load_user_yaml_adapters()
    if host in yaml_reg:
        return yaml_reg[host]

    py_reg = _load_user_python_adapters()
    if host in py_reg:
        return py_reg[host]

    # 内置代码型
    if host in BUILTIN_REGISTRY:
        return BUILTIN_REGISTRY[host]

    # readthedocs 子域统一走 readthedocs
    if host.endswith(".readthedocs.io") or host.endswith(".readthedocs.org"):
        return readthedocs.search

    # Algolia 兜底
    if host in ALGOLIA_INDEXES:
        app_id, api_key, index = ALGOLIA_INDEXES[host]

        def _algolia_search(query: str, *, max_results: int = 10, **_: Any) -> list[dict[str, Any]]:
            return algolia.search(
                query,
                app_id=app_id,
                api_key=api_key,
                index_name=index,
                site=host,
                max_results=max_results,
            )

        return _algolia_search

    return None


def list_adapters() -> dict[str, Any]:
    return {
        "builtin": sorted(BUILTIN_REGISTRY.keys()),
        "algolia": sorted(ALGOLIA_INDEXES.keys()),
        "user_python": sorted(_load_user_python_adapters().keys()),
        "user_yaml": sorted(_load_user_yaml_adapters().keys()),
    }
