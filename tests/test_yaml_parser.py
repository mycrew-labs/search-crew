"""验证极简 YAML subset parser 能解析本 plugin 实际用到的所有 defaults/*.yaml。"""

from __future__ import annotations

import pathlib
import unittest

from lib import _yaml

DEFAULTS = pathlib.Path(__file__).resolve().parents[1] / "defaults"


class TestYamlParser(unittest.TestCase):
    def test_routing_yaml(self) -> None:
        data = _yaml.load_file(DEFAULTS / "routing.yaml")
        self.assertIsInstance(data, dict)
        topics = data.get("topics")
        self.assertIsInstance(topics, list)
        self.assertGreater(len(topics), 0)
        first = topics[0]
        self.assertIn("name", first)
        self.assertIn("sites", first)

    def test_pricing_yaml(self) -> None:
        data = _yaml.load_file(DEFAULTS / "pricing.yaml")
        self.assertIsInstance(data, dict)
        self.assertIn("jina", data)
        self.assertIsInstance(data["jina"]["search"], float)

    def test_limits_yaml(self) -> None:
        data = _yaml.load_file(DEFAULTS / "limits.yaml")
        self.assertIsInstance(data, dict)
        self.assertEqual(data["deep_search"]["max_rounds"], 5)

    def test_strings_quoted_and_unquoted(self) -> None:
        text = (
            "hello: world\n"
            'quoted: "with space"\n'
            "list:\n"
            "  - one\n"
            "  - two\n"
        )
        data = _yaml.loads(text)
        self.assertEqual(data["hello"], "world")
        self.assertEqual(data["quoted"], "with space")
        self.assertEqual(data["list"], ["one", "two"])

    def test_comments_ignored(self) -> None:
        data = _yaml.loads("# top comment\nkey: value  # trailing\n")
        self.assertEqual(data, {"key": "value"})

    def test_inline_empty_list(self) -> None:
        data = _yaml.loads("sites: []\n")
        self.assertEqual(data, {"sites": []})


if __name__ == "__main__":
    unittest.main()
