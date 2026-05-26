"""TC-USAGE-SUMMARY-001: finalize_usage.py 的「搜索摘要」段 + --one-line 输出。

验证：
- usage-summary.md 末尾追加 `## 搜索摘要` 段
- 含「网站 | 查询词 | 次数」行
- 被站点调用上限拦下的 `status: call_cap_exceeded` 渲染成「已跳过」行
- --one-line 输出含 N 次调用 · M 个源 · K 次触发站点调用上限
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "search-toolkit" / "scripts"


class TestUsageSummarySearchSection(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.run_root = pathlib.Path(self.tmp.name) / "run-summary"
        self.run_root.mkdir()
        self.state = pathlib.Path(self.tmp.name) / "state"
        self.state.mkdir()
        os.environ["XDG_STATE_HOME"] = str(self.state)
        os.environ["XDG_CONFIG_HOME"] = self.tmp.name

    def tearDown(self) -> None:
        os.environ.pop("XDG_STATE_HOME", None)
        os.environ.pop("XDG_CONFIG_HOME", None)
        self.tmp.cleanup()

    def _write_usage(self, records: list[dict]) -> None:
        with open(self.run_root / "usage.jsonl", "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "finalize_usage.py"), *args],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ},
        )

    def test_search_summary_section_rendered(self) -> None:
        self._write_usage([
            {"ts": "2026-05-22T10:00:00Z", "run_id": "run-summary", "subagent": "fast-search",
             "backend": "jina", "endpoint": "search", "status": 200, "latency_ms": 100,
             "cost_estimate_usd": 0.0015, "pricing_source": "active",
             "query": "vLLM benchmark 2026"},
            {"ts": "2026-05-22T10:00:01Z", "run_id": "run-summary", "subagent": "site-search",
             "backend": "github", "endpoint": "search", "status": 200, "latency_ms": 200,
             "cost_estimate_usd": 0.0, "pricing_source": "zero",
             "query": "vLLM repo issues"},
            {"ts": "2026-05-22T10:00:02Z", "run_id": "run-summary", "subagent": "site-search",
             "backend": "github", "endpoint": "search", "status": 200, "latency_ms": 200,
             "cost_estimate_usd": 0.0, "pricing_source": "zero",
             "query": "TensorRT-LLM repo"},
        ])
        self._run(str(self.run_root))
        text = (self.run_root / "usage-summary.md").read_text(encoding="utf-8")
        self.assertIn("## 搜索摘要", text)
        self.assertIn("网站：jina | 查询词：vLLM benchmark 2026 | 次数：1", text)
        # github 两个不同 query 用 "；" 拼接
        self.assertIn("网站：github | 查询词：vLLM repo issues；TensorRT-LLM repo | 次数：2", text)

    def test_skipped_record_rendered(self) -> None:
        self._write_usage([
            {"ts": "2026-05-22T10:00:00Z", "run_id": "run-summary", "subagent": "fast-search",
             "backend": "grok", "endpoint": "chat/completions", "status": 200, "latency_ms": 100,
             "cost_estimate_usd": None, "pricing_source": "unknown",
             "query": "first grok query"},
            {"ts": "2026-05-22T10:00:01Z", "run_id": "run-summary", "subagent": "fast-search",
             "backend": "grok", "endpoint": "call_cap_exceeded", "status": "call_cap_exceeded",
             "latency_ms": 0, "cost_estimate_usd": None, "pricing_source": "unknown",
             "query": "second attempted grok query"},
        ])
        self._run(str(self.run_root))
        text = (self.run_root / "usage-summary.md").read_text(encoding="utf-8")
        self.assertIn("## 搜索摘要", text)
        self.assertIn("已跳过：grok", text)
        self.assertIn("触发站点调用上限", text)
        self.assertIn("second attempted grok query", text)
        # 真实调用 grok 1 次（不含被跳过的）
        self.assertIn("网站：grok | 查询词：first grok query | 次数：1", text)

    def test_one_line_output(self) -> None:
        self._write_usage([
            {"ts": "2026-05-22T10:00:00Z", "run_id": "run-summary", "subagent": "fast-search",
             "backend": "jina", "endpoint": "search", "status": 200, "latency_ms": 100,
             "cost_estimate_usd": 0.0015, "pricing_source": "active",
             "query": "q1"},
            {"ts": "2026-05-22T10:00:01Z", "run_id": "run-summary", "subagent": "fast-search",
             "backend": "serper", "endpoint": "search", "status": 200, "latency_ms": 150,
             "cost_estimate_usd": 0.001, "pricing_source": "active",
             "query": "q2"},
        ])
        result = self._run("--one-line", str(self.run_root))
        out = result.stdout.strip()
        self.assertIn("2 次调用", out)
        self.assertIn("2 个源", out)
        # 无 call_cap_exceeded 记录 → 不出现「触发」段
        self.assertNotIn("触发", out)
        # 单行无换行符
        self.assertNotIn("\n", out)

    def test_one_line_with_call_cap(self) -> None:
        self._write_usage([
            {"ts": "2026-05-22T10:00:00Z", "run_id": "run-summary", "subagent": "fast-search",
             "backend": "jina", "endpoint": "search", "status": 200, "latency_ms": 100,
             "cost_estimate_usd": 0.0015, "pricing_source": "active",
             "query": "q1"},
            {"ts": "2026-05-22T10:00:01Z", "run_id": "run-summary", "subagent": "fast-search",
             "backend": "grok", "endpoint": "call_cap_exceeded", "status": "call_cap_exceeded",
             "latency_ms": 0, "cost_estimate_usd": None, "pricing_source": "unknown",
             "query": "skipped"},
        ])
        result = self._run("--one-line", str(self.run_root))
        out = result.stdout.strip()
        self.assertIn("1 次调用", out)
        self.assertIn("1 个源", out)
        self.assertIn("1 次触发站点调用上限", out)


if __name__ == "__main__":
    unittest.main()
