"""Serper.dev（Google Search API）封装。"""

from __future__ import annotations

import re
from typing import Any

from . import BackendError, env, normalize_result
from . import _http

ENDPOINT = "https://google.serper.dev/search"
BACKEND = "serper"

_CJK_RE = re.compile(r"[一-鿿㐀-䶿]")


def is_available() -> bool:
    return env("SERPER_API_KEY") is not None


def _detect_locale(query: str, hint: str | None) -> tuple[str, str]:
    if hint:
        h = hint.lower()
        if h.startswith("zh"):
            return "cn", "zh-cn"
        if h in ("en", "en-us"):
            return "us", "en"
    if _CJK_RE.search(query):
        return "cn", "zh-cn"
    return "us", "en"


def search(query: str, *, max_results: int = 10, language: str | None = None) -> list[dict[str, Any]]:
    api_key = env("SERPER_API_KEY")
    if not api_key:
        raise BackendError(BACKEND, "缺少 SERPER_API_KEY")

    gl, hl = _detect_locale(query, language)
    body = {"q": query, "num": max(max_results, 10), "gl": gl, "hl": hl}
    headers = {"X-API-KEY": api_key}

    data = _http.request_json(
        "POST",
        ENDPOINT,
        backend=BACKEND,
        endpoint="search",
        headers=headers,
        json_body=body,
    )
    organic = (data or {}).get("organic") or []

    results = []
    for it in organic[:max_results]:
        results.append(
            normalize_result(
                title=it.get("title", ""),
                url=it.get("link", ""),
                snippet=it.get("snippet", ""),
                source="serper",
                position=it.get("position"),
                date=it.get("date"),
            )
        )
    return results
