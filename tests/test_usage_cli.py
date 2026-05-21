"""TC-USAGE-004：usage.py 跨 run 查询 CLI。"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "skills" / "search-toolkit" / "scripts"


class TestUsageCli(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.state = pathlib.Path(self.tmp.name) / "state" / "search-crew"
        self.state.mkdir(parents=True)
        os.environ["XDG_STATE_HOME"] = str(pathlib.Path(self.tmp.name) / "state")
        os.environ["XDG_CONFIG_HOME"] = self.tmp.name

        # 写一些模拟数据
        calls = [
            {"ts": "2026-05-15T10:00:00Z", "run_id": "r1", "subagent": "fast-search", "backend": "jina", "endpoint": "search", "cost_estimate_usd": 0.0015},
            {"ts": "2026-05-20T11:00:00Z", "run_id": "r2", "subagent": "deep-search", "backend": "serper", "endpoint": "search", "cost_estimate_usd": 0.001},
            {"ts": "2026-05-21T12:00:00Z", "run_id": "r3", "subagent": "fast-search", "backend": "jina", "endpoint": "reader", "cost_estimate_usd": 0.0007},
        ]
        with open(self.state / "calls.jsonl", "w", encoding="utf-8") as f:
            for c in calls:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        runs = [
            {"run_id": "r1", "ended_at": "2026-05-15T10:01:00Z", "totals": {"calls": 1, "cost_estimate_usd": 0.0015}},
            {"run_id": "r2", "ended_at": "2026-05-20T11:01:00Z", "totals": {"calls": 1, "cost_estimate_usd": 0.001}},
            {"run_id": "r3", "ended_at": "2026-05-21T12:01:00Z", "totals": {"calls": 1, "cost_estimate_usd": 0.0007}},
        ]
        with open(self.state / "runs.jsonl", "w", encoding="utf-8") as f:
            for r in runs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def tearDown(self) -> None:
        os.environ.pop("XDG_STATE_HOME", None)
        os.environ.pop("XDG_CONFIG_HOME", None)
        self.tmp.cleanup()

    def _run(self, *args: str) -> str:
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / "usage.py"), *args],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ},
        )
        return r.stdout

    def test_last_default(self) -> None:
        out = self._run()
        self.assertIn("r3", out)
        self.assertIn("r2", out)
        self.assertIn("r1", out)
        self.assertIn("合计", out)

    def test_by_backend(self) -> None:
        out = self._run("--by-backend")
        self.assertIn("jina", out)
        self.assertIn("serper", out)

    def test_by_day(self) -> None:
        out = self._run("--by-day")
        self.assertIn("2026-05-21", out)
        self.assertIn("2026-05-20", out)
        self.assertIn("2026-05-15", out)

    def test_since_filter(self) -> None:
        out = self._run("--since", "2026-05-20", "--by-day")
        self.assertIn("2026-05-21", out)
        self.assertIn("2026-05-20", out)
        self.assertNotIn("2026-05-15", out)

    def test_raw(self) -> None:
        out = self._run("--raw")
        # 三行 jsonl
        self.assertEqual(len([line for line in out.splitlines() if line.strip()]), 3)


if __name__ == "__main__":
    unittest.main()
