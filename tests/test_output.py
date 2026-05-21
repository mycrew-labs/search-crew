"""TC-OUTPUT-001：output.py 的附件 hash、front-matter、INDEX 渲染。"""

from __future__ import annotations

import pathlib
import tempfile
import unittest

from lib import output


class TestOutput(unittest.TestCase):
    def test_attachment_hash_dedup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            content = b"hello world"
            p1 = output.attachment_path(root, content, "txt")
            p2 = output.attachment_path(root, content, "txt")
            # 相同内容 → 同一文件，已存在不会重复写
            self.assertEqual(p1, p2)
            self.assertTrue(p1.exists())
            # 哈希前缀格式正确
            self.assertEqual(len(p1.stem), 12)
            self.assertTrue(p1.parent.name == "attachments")

    def test_front_matter_basic(self) -> None:
        out = output.write_front_matter(
            keywords=["react@19", "suspense"],
            url="https://example.com",
            ranking=8.5,
            recommended="must-read",
        )
        self.assertIn("---", out)
        self.assertIn("ranking: 8.5", out)
        self.assertIn("react@19", out)
        # 字符串通过 json.dumps → 带引号
        self.assertIn('"must-read"', out)

    def test_evidence_anchor(self) -> None:
        a = output.evidence_anchor("suspense-spec")
        self.assertIn("anchor: suspense-spec", a)

    def test_render_index_md(self) -> None:
        md = output.render_index_md(
            subagent="fast-search",
            run_id="sess-123",
            inputs={"query": "test", "起点路由": "通用搜索"},
            files=[
                {"filename": "fast-search-001.md", "url": "https://a", "ranking": 9.0, "recommended": "must-read", "summary": "讲了 A", "keywords": ["k1", "k2"]},
                {"filename": "fast-search-002.md", "url": "https://b", "ranking": 5.0, "recommended": "skip-able", "summary": "讲了 B", "keywords": ["k3"]},
            ],
            keywords=["k1", "k2", "k3"],
            next_read=["fast-search-001.md (must-read)"],
        )
        self.assertIn("# INDEX · fast-search · sess-123", md)
        self.assertIn("ranking: 9.0/10", md)
        # 按 ranking 排序：001（9.0）必须在 002（5.0）之前
        idx_001 = md.index("fast-search-001.md")
        idx_002 = md.index("fast-search-002.md")
        self.assertLess(idx_001, idx_002)
        # Keywords 段
        self.assertIn("k1, k2, k3", md)
        # Next-Read 段
        self.assertIn("Next-Read", md)

    def test_relative_attachment_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            sub = root / "fast-search"
            sub.mkdir()
            p = output.attachment_path(root, b"x", "png")
            ref = output.relative_to_subagent(p, sub)
            self.assertTrue(ref.startswith("../attachments/"))
            self.assertTrue(ref.endswith(".png"))


if __name__ == "__main__":
    unittest.main()
