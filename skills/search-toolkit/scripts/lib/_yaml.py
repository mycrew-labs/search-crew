"""极简 YAML subset 解析器（零依赖）。

支持的子集（足够本 plugin 的 routing.yaml / pricing.yaml / limits.yaml）：
- 缩进表示嵌套（2 空格固定缩进）
- `key: value` map
- `- value` list
- 字符串、整数、浮点、布尔（true/false）、null
- `# 注释`（行尾或独立行）
- 双引号 / 单引号字符串（保留内部空格）
- 跨行用 `|` / `>` 折叠字符串（基础支持，不处理 chomp 修饰符）

**不支持**的高级特性：anchors、merge keys、多文档分隔（`---`）、复杂标签、流式 `[1,2,3]` / `{a:1}`。
本 plugin 的配置文件刻意只用受支持子集；遇到不识别语法 → 抛 `YamlSubsetError` 明确提示。
"""

from __future__ import annotations

import re
from typing import Any


class YamlSubsetError(Exception):
    pass


_QUOTED = re.compile(r"""^(['"])(.*)\1$""")
_INT = re.compile(r"^-?\d+$")
_FLOAT = re.compile(r"^-?\d+\.\d+([eE][-+]?\d+)?$")


def _scalar(token: str) -> Any:
    s = token.strip()
    if s == "" or s == "~" or s.lower() == "null":
        return None
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if (m := _QUOTED.match(s)) is not None:
        return m.group(2)
    if _INT.match(s):
        return int(s)
    if _FLOAT.match(s):
        return float(s)
    # 行内空 list / 空 map 短记号
    if s == "[]":
        return []
    if s == "{}":
        return {}
    return s  # 裸字符串


def _indent_of(line: str) -> int:
    n = 0
    for c in line:
        if c == " ":
            n += 1
        else:
            break
    return n


def _strip_comment(line: str) -> str:
    """剥行尾 `#` 注释（不在引号内时）。"""
    in_single = False
    in_double = False
    for i, c in enumerate(line):
        if c == "'" and not in_double:
            in_single = not in_single
        elif c == '"' and not in_single:
            in_double = not in_double
        elif c == "#" and not in_single and not in_double:
            return line[:i].rstrip()
    return line.rstrip()


def loads(text: str) -> Any:
    """解析 YAML subset 文本为 Python 对象。"""
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        stripped = _strip_comment(raw)
        if not stripped.strip():
            continue
        lines.append((_indent_of(stripped), stripped))

    if not lines:
        return None

    pos = [0]

    def parse_block(min_indent: int) -> Any:
        if pos[0] >= len(lines):
            return None

        indent, line = lines[pos[0]]
        if indent < min_indent:
            return None

        content = line[indent:]

        # List 块
        if content.startswith("- "):
            items: list[Any] = []
            while pos[0] < len(lines):
                cur_indent, cur_line = lines[pos[0]]
                if cur_indent != indent:
                    break
                cur_content = cur_line[cur_indent:]
                if not cur_content.startswith("- "):
                    break
                item_text = cur_content[2:].strip()
                pos[0] += 1
                if not item_text:
                    # 后续缩进块作为 item
                    items.append(parse_block(indent + 2))
                    continue
                if ":" in item_text and not _QUOTED.match(item_text):
                    # 内联 map 起点：`- key: value`
                    # 回退处理：把当前行视为 map 块的第一行
                    key, _, value = item_text.partition(":")
                    value = value.strip()
                    item_map: dict[str, Any] = {}
                    if value:
                        item_map[key.strip()] = _scalar(value)
                    else:
                        item_map[key.strip()] = parse_block(indent + 4)
                    # 继续读后续同 indent+2 的 map 字段
                    while pos[0] < len(lines):
                        ni, nl = lines[pos[0]]
                        if ni != indent + 2:
                            break
                        nc = nl[ni:]
                        if nc.startswith("- "):
                            break
                        if ":" not in nc:
                            raise YamlSubsetError(f"无法解析: {nl!r}")
                        k, _, v = nc.partition(":")
                        v = v.strip()
                        pos[0] += 1
                        if v:
                            item_map[k.strip()] = _scalar(v)
                        else:
                            item_map[k.strip()] = parse_block(indent + 4)
                    items.append(item_map)
                else:
                    items.append(_scalar(item_text))
            return items

        # Map 块
        if ":" in content:
            result: dict[str, Any] = {}
            while pos[0] < len(lines):
                cur_indent, cur_line = lines[pos[0]]
                if cur_indent != indent:
                    break
                cur_content = cur_line[cur_indent:]
                if cur_content.startswith("- "):
                    break
                if ":" not in cur_content:
                    raise YamlSubsetError(f"无法解析: {cur_line!r}")
                key, _, value = cur_content.partition(":")
                value = value.strip()
                pos[0] += 1
                if not value:
                    result[key.strip()] = parse_block(indent + 2)
                elif value == "|" or value == ">":
                    # 折叠字符串块
                    chunks: list[str] = []
                    while pos[0] < len(lines):
                        ni, nl = lines[pos[0]]
                        if ni <= indent:
                            break
                        chunks.append(nl[indent + 2 :] if ni >= indent + 2 else nl[ni:])
                        pos[0] += 1
                    sep = "\n" if value == "|" else " "
                    result[key.strip()] = sep.join(chunks)
                else:
                    result[key.strip()] = _scalar(value)
            return result

        raise YamlSubsetError(f"无法解析: {line!r}")

    root = parse_block(0)
    return root


def load_file(path: str | Any) -> Any:
    """从文件路径读取并解析。"""
    with open(path, "r", encoding="utf-8") as f:
        return loads(f.read())
