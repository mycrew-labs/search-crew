"""TC-FALLBACK-001：零 key 时 search.py 应输出 WEBSEARCH_FALLBACK。"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "skills" / "search-toolkit" / "scripts"


class TestSearchFallback(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        # 隔离 config / state，避免污染
        os.environ["XDG_CONFIG_HOME"] = self.tmp.name
        os.environ["XDG_STATE_HOME"] = self.tmp.name + "-state"
        # 清掉 key
        for k in ("JINA_API_KEY", "SERPER_API_KEY"):
            os.environ.pop(k, None)

    def tearDown(self) -> None:
        os.environ.pop("XDG_CONFIG_HOME", None)
        os.environ.pop("XDG_STATE_HOME", None)
        self.tmp.cleanup()

    def test_zero_key_emits_fallback(self) -> None:
        r = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "search.py"),
                "--query",
                "test",
                "--max-results",
                "3",
            ],
            capture_output=True,
            text=True,
            env={**os.environ},
            check=True,
        )
        payload = json.loads(r.stdout)
        self.assertIsNone(payload["backend"])
        self.assertEqual(payload["fallback"], "WEBSEARCH_FALLBACK")
        self.assertEqual(payload["results"], [])


if __name__ == "__main__":
    unittest.main()
