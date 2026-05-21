"""YAML 配置驱动的通用站点适配器（用户态零代码扩展）。

用户在 `~/.config/search-crew/adapters/<site>.yaml` 写：

```yaml
site: example.com
search_url: "https://example.com/search?q={query}"
result_selector:
  list: ".result-item"
  title: "h3 a"
  url: "h3 a@href"
  snippet: ".excerpt"
```

本模块用 `html.parser` 解析返回页（不引第三方），按 selector 抽取结果。

注：CSS selector 支持的子集很有限（class / tag / 简单组合 + 属性提取 `@href`）。
复杂站点请用代码型适配器。
"""

from __future__ import annotations

import html.parser
from typing import Any

from .. import _yaml, normalize_result
from .. import _http

BACKEND = "yaml-adapter"


class _Tag:
    def __init__(self, tag: str, attrs: dict[str, str]):
        self.tag = tag
        self.attrs = attrs
        self.children: list["_Tag | str"] = []

    def text(self) -> str:
        parts: list[str] = []
        for c in self.children:
            if isinstance(c, str):
                parts.append(c)
            else:
                parts.append(c.text())
        return "".join(parts).strip()

    def find_all(self, sel: str) -> list["_Tag"]:
        """支持 `.class` / `tag` / `tag.class` 的极简 selector。"""
        results: list["_Tag"] = []
        self._walk(sel, results)
        return results

    def _walk(self, sel: str, out: list["_Tag"]) -> None:
        if self._match(sel):
            out.append(self)
        for c in self.children:
            if isinstance(c, _Tag):
                c._walk(sel, out)

    def _match(self, sel: str) -> bool:
        tag = ""
        cls = ""
        if "." in sel:
            tag, _, cls = sel.partition(".")
        else:
            tag = sel
        if tag and tag != self.tag:
            return False
        if cls:
            classes = (self.attrs.get("class") or "").split()
            if cls not in classes:
                return False
        return True


class _HTMLBuilder(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.root = _Tag("root", {})
        self.stack: list[_Tag] = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Tag(tag, {k: v or "" for k, v in attrs})
        self.stack[-1].children.append(node)
        if tag not in ("br", "hr", "img", "input", "meta", "link"):  # 自闭合白名单
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack = self.stack[:i]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def _extract(node: _Tag, sel: str) -> str:
    """sel 支持 `.class h3 a` 这种空格嵌套；末尾 `@attr` 取属性。"""
    parts = sel.split()
    attr = None
    if parts and "@" in parts[-1]:
        parts[-1], _, attr = parts[-1].partition("@")
    cur = [node]
    for p in parts:
        nxt: list[_Tag] = []
        for c in cur:
            nxt.extend(c.find_all(p))
        cur = nxt
        if not cur:
            return ""
    target = cur[0]
    if attr:
        return target.attrs.get(attr, "")
    return target.text()


def search_from_yaml(yaml_path, query: str, *, max_results: int = 10) -> list[dict[str, Any]]:
    cfg = _yaml.load_file(yaml_path) or {}
    search_url = cfg.get("search_url", "").replace("{query}", query)
    sel = cfg.get("result_selector") or {}
    site = cfg.get("site", "unknown")

    if not search_url or not sel.get("list"):
        return []

    html_text = _http.request_text(
        "GET",
        search_url,
        backend=BACKEND,
        endpoint=f"yaml:{site}",
    )
    builder = _HTMLBuilder()
    builder.feed(html_text)

    items = builder.root.find_all(sel["list"])
    results: list[dict[str, Any]] = []
    for it in items[:max_results]:
        title = _extract(it, sel.get("title", "")) if sel.get("title") else ""
        url = _extract(it, sel.get("url", "")) if sel.get("url") else ""
        snippet = _extract(it, sel.get("snippet", "")) if sel.get("snippet") else ""
        results.append(
            normalize_result(
                title=title,
                url=url,
                snippet=snippet,
                source=f"yaml:{site}",
            )
        )
    return results
