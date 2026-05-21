"""MDN Web Docs 搜索。

接口：https://developer.mozilla.org/api/v1/search?q=<query>
公开接口，无需 key。
"""

from __future__ import annotations

from typing import Any

from .. import normalize_result
from .. import _http

BACKEND = "mdn"
SITE = "developer.mozilla.org"
API = "https://developer.mozilla.org/api/v1/search"


def search(query: str, *, max_results: int = 10, **_: Any) -> list[dict[str, Any]]:
    params = {"q": query, "locale": "en-US"}
    data = _http.request_json(
        "GET",
        API,
        backend=BACKEND,
        endpoint="search",
        params=params,
    )
    documents = (data or {}).get("documents") or []

    results = []
    for it in documents[:max_results]:
        results.append(
            normalize_result(
                title=it.get("title", ""),
                url=f"https://developer.mozilla.org{it.get('mdn_url', '')}",
                snippet=it.get("summary", ""),
                source="mdn",
                locale=it.get("locale"),
            )
        )
    return results
