"""通用 Algolia DocSearch 客户端。

很多主流文档站都用 Algolia DocSearch 作为搜索后端，可以直接复用本客户端，
传入对应的 `app_id` / `api_key` / `index_name` 即可（这些 key 是站点公开的，
可在浏览器开发者工具中抓到）。

API：https://www.algolia.com/doc/rest-api/search/
"""

from __future__ import annotations

from typing import Any

from .. import normalize_result
from .. import _http

BACKEND = "algolia"


def search(
    query: str,
    *,
    app_id: str,
    api_key: str,
    index_name: str,
    site: str,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    url = f"https://{app_id.lower()}-dsn.algolia.net/1/indexes/{index_name}/query"
    headers = {
        "X-Algolia-Application-Id": app_id,
        "X-Algolia-API-Key": api_key,
    }
    body = {"query": query, "hitsPerPage": max_results}
    data = _http.request_json(
        "POST",
        url,
        backend=BACKEND,
        endpoint=f"algolia:{site}",
        headers=headers,
        json_body=body,
    )
    hits = (data or {}).get("hits") or []
    results = []
    for it in hits[:max_results]:
        # DocSearch 索引项通常带 hierarchy.lvl0~lvl6 + content + url
        hierarchy = it.get("hierarchy") or {}
        title_parts = [hierarchy.get(f"lvl{i}") for i in range(7)]
        title = " · ".join([p for p in title_parts if p])
        results.append(
            normalize_result(
                title=title or it.get("title", ""),
                url=it.get("url", ""),
                snippet=(it.get("content") or "")[:280],
                source=f"algolia:{site}",
                hierarchy=hierarchy,
            )
        )
    return results
