#!/usr/bin/env python3
"""站点搜索入口。

CLI:
  python3 site_search.py --site <host> --query <q> [--max-results N]
  python3 site_search.py --list-adapters

输出 JSON：
- 命中 → { "adapter": "github", "results": [...] }
- 未命中 → { "adapter": null, "hint": "no-adapter，建议 fetch.py 或 chrome-devtools MCP", "results": [] }
"""

from __future__ import annotations

import argparse
import sys

from lib import BackendError, emit
from lib.sites import get_adapter, list_adapters


def main() -> int:
    ap = argparse.ArgumentParser(description="Search Crew 站点搜索")
    ap.add_argument("--site")
    ap.add_argument("--query")
    ap.add_argument("--max-results", type=int, default=10)
    ap.add_argument("--list-adapters", action="store_true")
    args = ap.parse_args()

    if args.list_adapters:
        emit({"adapters": list_adapters()})
        return 0

    if not args.site or not args.query:
        print("error: --site 和 --query 必填（或用 --list-adapters）", file=sys.stderr)
        return 2

    fn = get_adapter(args.site)
    if fn is None:
        emit(
            {
                "site": args.site,
                "adapter": None,
                "hint": "此站点无适配器；建议用 fetch.py 抓固定 URL，或降级到 chrome-devtools MCP",
                "results": [],
            }
        )
        return 0

    try:
        results = fn(args.query, max_results=args.max_results)
        emit({"site": args.site, "adapter": fn.__module__.split(".")[-1], "results": results})
        return 0
    except BackendError as e:
        print(f"[site_search] {args.site} 适配器失败：{e}", file=sys.stderr)
        emit(
            {
                "site": args.site,
                "adapter": None,
                "hint": f"adapter 报错，建议降级：{e}",
                "results": [],
                "error": str(e),
            }
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
