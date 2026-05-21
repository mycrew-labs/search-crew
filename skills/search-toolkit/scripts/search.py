#!/usr/bin/env python3
"""通用搜索入口。

CLI: python3 search.py --query <q> [--max-results N] [--language zh-cn] [--prefer jina|serper]

输出 JSON 到 stdout：
- 成功 → { "backend": "...", "results": [...], "fallback": null }
- 无可用 backend → { "results": [], "fallback": "WEBSEARCH_FALLBACK" }
"""

from __future__ import annotations

import argparse
import sys

from lib import BackendError, emit, jina, serper


def main() -> int:
    ap = argparse.ArgumentParser(description="Search Crew 通用搜索入口")
    ap.add_argument("--query", required=True)
    ap.add_argument("--max-results", type=int, default=10)
    ap.add_argument("--language", default=None, help="zh / zh-cn / en / en-us")
    ap.add_argument("--prefer", choices=["jina", "serper"], default=None)
    args = ap.parse_args()

    # 按 prefer 与可用性选 backend
    backends = []
    if args.prefer == "jina":
        backends = ["jina", "serper"]
    elif args.prefer == "serper":
        backends = ["serper", "jina"]
    else:
        # 默认 Jina 优先（语义更强）
        backends = ["jina", "serper"]

    for backend in backends:
        try:
            if backend == "jina" and jina.is_available_search():
                results = jina.search(args.query, max_results=args.max_results, language=args.language)
                emit({"backend": "jina", "results": results, "fallback": None})
                return 0
            if backend == "serper" and serper.is_available():
                results = serper.search(args.query, max_results=args.max_results, language=args.language)
                emit({"backend": "serper", "results": results, "fallback": None})
                return 0
        except BackendError as e:
            print(f"[search] {backend} 失败：{e}", file=sys.stderr)
            continue

    emit({"backend": None, "results": [], "fallback": "WEBSEARCH_FALLBACK"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
