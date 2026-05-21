"""TC-USAGE-003：单价表加载 + 覆盖 + 缺失策略。"""

from __future__ import annotations

import os
import pathlib
import tempfile
import unittest

from lib import pricing


class TestPricing(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.config_dir = pathlib.Path(self.tmp.name) / "search-crew"
        self.config_dir.mkdir(parents=True)
        os.environ["XDG_CONFIG_HOME"] = self.tmp.name
        pricing.reset_cache()

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("XDG_CONFIG_HOME", None)
        pricing.reset_cache()

    def _write_pricing(self, content: str) -> None:
        (self.config_dir / "pricing.yaml").write_text(content, encoding="utf-8")
        pricing.reset_cache()

    def test_active_hits(self) -> None:
        self._write_pricing("jina:\n  search: 0.999\n")
        cost, source = pricing.estimate("jina", "search", units=1)
        self.assertAlmostEqual(cost, 0.999, places=4)
        self.assertEqual(source, "active")

    def test_unknown_backend(self) -> None:
        self._write_pricing("jina:\n  search: 0.001\n")
        cost, source = pricing.estimate("brave", "search", units=1)
        self.assertIsNone(cost)
        self.assertEqual(source, "unknown")

    def test_unknown_endpoint(self) -> None:
        self._write_pricing("jina:\n  search: 0.001\n")
        cost, source = pricing.estimate("jina", "reader", units=1)
        self.assertIsNone(cost)
        self.assertEqual(source, "unknown")

    def test_zero_cost_list(self) -> None:
        self._write_pricing(
            "zero_cost:\n"
            "  - webfetch-fallback\n"
            "  - chrome-devtools-mcp\n"
        )
        cost, source = pricing.estimate("webfetch-fallback", "fetch", units=1)
        self.assertEqual(cost, 0.0)
        self.assertEqual(source, "zero")

    def test_units_multiplier(self) -> None:
        self._write_pricing("openai:\n  gpt-input: 0.001\n")
        cost, source = pricing.estimate("openai", "gpt-input", units=100)
        self.assertAlmostEqual(cost, 0.1, places=4)
        self.assertEqual(source, "active")


if __name__ == "__main__":
    unittest.main()
