"""PyPI 包搜索。

PyPI 没有官方搜索 API（pypi.org/search 是 HTML 页面），改用 PyPI Simple JSON
+ 名称匹配的兜底方案，或者直接 fetch HTML 解析。这里走简单 fetch：让 fast-search
回头解析 HTML，或者 user 配置 PYPI_INDEX 改走自建索引。

首版实现：调 `https://pypi.org/search/?q=<query>` 拿 HTML，仅返回 URL 让上层
进一步抓 / 让用户在浏览器看；标记 source 让调用方知道这是 best-effort。
"""

from __future__ import annotations

from typing import Any

from .. import normalize_result
from .. import _http

BACKEND = "pypi"
SITE = "pypi.org"


def search(query: str, *, max_results: int = 10, **_: Any) -> list[dict[str, Any]]:
    # 直接给搜索 URL，让调用方决定是否 fetch 解析
    url = f"https://pypi.org/search/?q={query}"
    # 仍做一次轻量 fetch 校验 200 + 打点
    _http.request_text(
        "GET",
        url,
        backend=BACKEND,
        endpoint="search",
        timeout=15,
    )
    return [
        normalize_result(
            title=f"PyPI 搜索结果: {query}",
            url=url,
            snippet="PyPI 无官方搜索 API；本条为搜索页 URL，请用 fetch.py 抓取并解析 HTML 取列表",
            source="pypi-search-page",
            best_effort=True,
        )
    ][:max_results]
