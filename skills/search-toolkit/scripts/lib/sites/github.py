"""GitHub Code / Repo / Issue 搜索。

API 文档：https://docs.github.com/en/rest/search
未提供 token 时走匿名访问（限流为每分钟 10 次）。
"""

from __future__ import annotations

from typing import Any

from .. import env, normalize_result
from .. import _http

BACKEND = "github"
API = "https://api.github.com"
SITE = "github.com"


def _headers() -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = env("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def search(query: str, *, max_results: int = 10, kind: str | None = None, **_: Any) -> list[dict[str, Any]]:
    """kind: repo | code | issue。未指定时按 query 含义猜测。"""
    kind = kind or _guess_kind(query)
    endpoint = {
        "repo": "/search/repositories",
        "code": "/search/code",
        "issue": "/search/issues",
    }.get(kind, "/search/repositories")

    params = {"q": query, "per_page": max_results}
    data = _http.request_json(
        "GET",
        API + endpoint,
        backend=BACKEND,
        endpoint=kind,
        headers=_headers(),
        params=params,
    )
    items = (data or {}).get("items") or []

    results = []
    for it in items[:max_results]:
        if kind == "repo":
            results.append(
                normalize_result(
                    title=it.get("full_name", ""),
                    url=it.get("html_url", ""),
                    snippet=it.get("description") or "",
                    source="github-repo",
                    stars=it.get("stargazers_count"),
                    language=it.get("language"),
                    updated=it.get("updated_at"),
                )
            )
        elif kind == "code":
            repo = (it.get("repository") or {}).get("full_name", "")
            results.append(
                normalize_result(
                    title=f"{repo}:{it.get('path', '')}",
                    url=it.get("html_url", ""),
                    snippet="",
                    source="github-code",
                    repo=repo,
                    path=it.get("path"),
                )
            )
        else:  # issue / PR
            results.append(
                normalize_result(
                    title=it.get("title", ""),
                    url=it.get("html_url", ""),
                    snippet=(it.get("body") or "")[:280],
                    source="github-issue",
                    state=it.get("state"),
                    is_pr=bool(it.get("pull_request")),
                    comments=it.get("comments"),
                )
            )
    return results


def _guess_kind(query: str) -> str:
    q = query.lower()
    if "in:file" in q or "language:" in q or "path:" in q:
        return "code"
    if "is:issue" in q or "is:pr" in q or "label:" in q:
        return "issue"
    return "repo"
