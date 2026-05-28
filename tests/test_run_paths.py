"""run_paths.py / runtime run 目录口径。

per-dispatch 模型：派发方造 run 目录、经 SEARCH_CREW_RUN_ROOT 传目录路径；
口径 = SEARCH_CREW_RUN_ROOT > /tmp/search-crew/<RUN_ID> > /tmp/search-crew/<会话 id>；
run_id = 目录名。回归老 bug：产物目录须与 usage 打点同根。
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN_ROOT / "skills" / "search-toolkit" / "scripts"
RUN_PATHS = SCRIPTS / "run_paths.py"


def _clean_env(**extra):
    env = {**os.environ}
    for k in ("SEARCH_CREW_RUN_ROOT", "SEARCH_CREW_RUN_ID"):
        env.pop(k, None)
    env.update(extra)
    return env


class TestRunPaths(unittest.TestCase):
    def _run(self, *args, env=None):
        r = subprocess.run([sys.executable, str(RUN_PATHS), *args],
                           capture_output=True, text=True, env=env, check=True)
        return r.stdout.strip()

    def test_session_fallback(self):
        env = _clean_env(CLAUDE_CODE_SESSION_ID="sess-1")
        self.assertEqual(self._run(env=env), "/tmp/search-crew/sess-1")

    def test_run_root_env_takes_precedence(self):
        with tempfile.TemporaryDirectory() as d:
            root = str(pathlib.Path(d) / "myrun")
            env = _clean_env(CLAUDE_CODE_SESSION_ID="sess-1", SEARCH_CREW_RUN_ROOT=root)
            self.assertEqual(self._run(env=env), root)
            # --subagent 落该目录下
            self.assertEqual(self._run("--subagent", "fast-search", env=env), str(pathlib.Path(root) / "fast-search"))

    def test_new_creates_dir_and_prints_path(self):
        env = _clean_env(CLAUDE_CODE_SESSION_ID="sess-1")
        out = self._run("--new", env=env)
        self.assertTrue(out.startswith("/tmp/search-crew/"))
        self.assertTrue(pathlib.Path(out).is_dir())  # 目录已造
        # 形如 <UTC时间>-<hex>
        self.assertRegex(pathlib.Path(out).name, r"^\d{8}T\d{6}-[0-9a-f]{6}$")

    def test_run_id_is_basename(self):
        with tempfile.TemporaryDirectory() as d:
            root = str(pathlib.Path(d) / "abc123")
            env = _clean_env(SEARCH_CREW_RUN_ROOT=root)
            out = subprocess.run(
                [sys.executable, "-c",
                 "import sys;sys.path.insert(0,r'%s');from lib import runtime;print(runtime.run_id())" % SCRIPTS],
                capture_output=True, text=True, env=env, check=True).stdout.strip()
            self.assertEqual(out, "abc123")

    def test_aligns_with_usage_record_root(self):
        """run_paths run_root 必须 == usage 打点用的 runtime.run_root()。"""
        env = _clean_env(SEARCH_CREW_RUN_ROOT="/tmp/search-crew/align-test")
        rp = self._run(env=env)
        usage_root = subprocess.run(
            [sys.executable, "-c",
             "import sys;sys.path.insert(0,r'%s');from lib import runtime;print(runtime.run_root())" % SCRIPTS],
            capture_output=True, text=True, env=env, check=True).stdout.strip()
        self.assertEqual(rp, usage_root)


if __name__ == "__main__":
    unittest.main()
