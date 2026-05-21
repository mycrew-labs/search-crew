"""npm registry 搜索。

API：https://registry.npmjs.org/-/v1/search?text=<query>
公开 API，无需 key。
"""

from __future__ import annotations

from typing import Any

from .. import normalize_result
from .. import _http

BACKEND = "npm"
SITE = "npmjs.com"
API = "https://registry.npmjs.org/-/v1/search"


def search(query: str, *, max_results: int = 10, **_: Any) -> list[dict[str, Any]]:
    params = {"text": query, "size": max_results}
    data = _http.request_json(
        "GET",
        API,
        backend=BACKEND,
        endpoint="search",
        params=params,
    )
    objects = (data or {}).get("objects") or []
    results = []
    for it in objects[:max_results]:
        pkg = it.get("package") or {}
        results.append(
            normalize_result(
                title=pkg.get("name", ""),
                url=(pkg.get("links") or {}).get("npm")
                or f"https://www.npmjs.com/package/{pkg.get('name', '')}",
                snippet=pkg.get("description", ""),
                source="npm",
                version=pkg.get("version"),
                keywords=pkg.get("keywords"),
                score=(it.get("score") or {}).get("final"),
            )
        )
    return results
