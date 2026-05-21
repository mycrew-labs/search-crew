"""产物落盘工具：附件 hash + INDEX.md 生成 + evidence anchor 模板。

P-OUTPUT-001：
- 文件命名前缀以 subagent 名开头
- 附件统一 `<run_root>/attachments/<sha256[:12]>.<ext>`，markdown 用相对路径引用
- INDEX.md 是 wiki 风格大纲（子文件简介、ranking、推荐与否、关键词清单）
- evidence anchor 用 `### anchor: <slug>` 标记原文片段
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any


def attachment_path(run_root: pathlib.Path, content: bytes, ext: str) -> pathlib.Path:
    """计算并 mkdir 附件落盘路径；已存在则跳过（天然去重）。"""
    h = hashlib.sha256(content).hexdigest()[:12]
    ext = ext.lstrip(".")
    p = run_root / "attachments" / f"{h}.{ext}"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_bytes(content)
    return p


def relative_to_subagent(attachment: pathlib.Path, _subagent_dir: pathlib.Path) -> str:
    """让 subagent_dir 中的 markdown 引用 run_root/attachments/ 时用相对路径。

    第二个参数当前未使用（保留以便未来支持多层嵌套如 deep-search/traces/）。
    """
    return f"../attachments/{attachment.name}"


def write_front_matter(keywords: list[str], **extra: Any) -> str:
    """生成 markdown YAML front-matter（手写避免 _yaml 双向序列化负担）。"""
    lines = ["---"]
    for k, v in extra.items():
        if isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        elif v is None:
            lines.append(f"{k}: null")
        else:
            lines.append(f"{k}: {json.dumps(str(v), ensure_ascii=False)}")
    if keywords:
        lines.append("keywords:")
        for kw in keywords:
            lines.append(f"  - {json.dumps(kw, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def evidence_anchor(slug: str) -> str:
    """生成 evidence anchor markdown。"""
    return f"\n### anchor: {slug}\n"


def render_index_md(
    *,
    subagent: str,
    run_id: str,
    inputs: dict[str, Any],
    files: list[dict[str, Any]],
    keywords: list[str],
    next_read: list[str],
) -> str:
    """生成 wiki 风格大纲 INDEX.md（P-OUTPUT-001 索引文件 schema）。"""
    out: list[str] = []
    out.append(f"# INDEX · {subagent} · {run_id}\n")

    out.append("## Input\n")
    for k, v in inputs.items():
        out.append(f"- {k}: {v}")
    out.append("")

    out.append("## Files（按 ranking 排序）\n")
    for f in sorted(files, key=lambda x: x.get("ranking", 0), reverse=True):
        ranking = f.get("ranking", 0)
        stars = "★" * max(0, min(5, round(ranking / 2)))
        out.append(f"### {stars}  {f['filename']}")
        if f.get("url"):
            out.append(f"- 来源: {f['url']}")
        out.append(f"- ranking: {ranking}/10")
        out.append(f"- 推荐: {f.get('recommended', 'should-read')}")
        if f.get("verification"):
            out.append(f"- 官方源验证: {f['verification']}")
        out.append(f"- 简介: {f.get('summary', '（无简介）')}")
        if f.get("keywords"):
            out.append(f"- 关键词: {', '.join(f['keywords'])}")
        out.append("")

    if keywords:
        out.append("## Keywords（全集）\n")
        out.append(", ".join(keywords))
        out.append("")

    if next_read:
        out.append("## Next-Read\n")
        for i, item in enumerate(next_read, 1):
            out.append(f"{i}. {item}")
        out.append("")

    return "\n".join(out)
