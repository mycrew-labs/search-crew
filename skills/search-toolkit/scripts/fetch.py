#!/usr/bin/env python3
"""URL → markdown 抓取入口。

CLI: python3 fetch.py <url>

输出 JSON：
- 成功 → { "source": "jina-reader", "url": "...", "markdown": "..." }
- 无 Reader 可用 → { "source": null, "fallback": "WEBFETCH_FALLBACK" }
"""

from __future__ import annotations

import argparse
import sys

from lib import BackendError, emit, jina


def main() -> int:
    ap = argparse.ArgumentParser(description="Search Crew URL 抓取")
    ap.add_argument("url")
    args = ap.parse_args()

    try:
        data = jina.fetch(args.url)
        emit({"source": "jina-reader", **data, "fallback": None})
        return 0
    except BackendError as e:
        print(f"[fetch] jina-reader 失败：{e}", file=sys.stderr)
        emit({"source": None, "url": args.url, "markdown": None, "fallback": "WEBFETCH_FALLBACK"})
        return 0


if __name__ == "__main__":
    sys.exit(main())
