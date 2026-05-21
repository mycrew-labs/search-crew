"""Read the Docs 搜索。

API：https://docs.readthedocs.io/en/stable/server-side-search/api.html
公开 API，无需 key。
"""

from __future__ import annotations

from typing import Any

from .. import normalize_result
from .. import _http

BACKEND = "readthedocs"
SITE = "readthedocs.io"
API = "https://readthedocs.org/api/v3/search/"


def search(query: str, *, max_results: int = 10, project: str | None = None, **_: Any) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"q": query}
    if project:
        params["project"] = project
    data = _http.request_json(
        "GET",
        API,
        backend=BACKEND,
        endpoint="search",
        params=params,
    )
    items = (data or {}).get("results") or []
    results = []
    for it in items[:max_results]:
        blocks = it.get("blocks") or []
        snippet = ""
        if blocks:
            snippet = (blocks[0].get("content") or "")[:280]
        results.append(
            normalize_result(
                title=it.get("title", ""),
                url=it.get("domain", "") + it.get("path", ""),
                snippet=snippet,
                source="readthedocs",
                project=it.get("project"),
                version=it.get("version"),
            )
        )
    return results
