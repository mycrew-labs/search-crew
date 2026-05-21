"""TC-CONFIG-001：seed_user_config.py 拷贝 + 幂等 + 不覆盖。"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = PLUGIN_ROOT / "skills" / "search-toolkit" / "scripts" / "seed_user_config.py"


class TestSeed(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.config_root = pathlib.Path(self.tmp.name)
        os.environ["XDG_CONFIG_HOME"] = str(self.config_root)
        os.environ["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)

    def tearDown(self) -> None:
        os.environ.pop("XDG_CONFIG_HOME", None)
        os.environ.pop("CLAUDE_PLUGIN_ROOT", None)
        self.tmp.cleanup()

    def _run_seed(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SEED)],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ},
        )

    def test_first_seed_copies_files(self) -> None:
        self._run_seed()
        active = self.config_root / "search-crew"
        self.assertTrue((active / "routing.yaml").exists())
        self.assertTrue((active / "pricing.yaml").exists())
        self.assertTrue((active / "limits.yaml").exists())
        self.assertTrue((active / "adapters").is_dir())
        self.assertTrue((active / ".seeded").exists())

    def test_second_seed_no_overwrite(self) -> None:
        self._run_seed()
        # 篡改一个文件
        active = self.config_root / "search-crew"
        custom = "USER MODIFIED CONTENT"
        (active / "routing.yaml").write_text(custom, encoding="utf-8")
        # 再 seed
        self._run_seed()
        # 仍是用户内容
        self.assertEqual((active / "routing.yaml").read_text(encoding="utf-8"), custom)

    def test_seed_creates_new_files_after_upgrade(self) -> None:
        """模拟 plugin 升级新加文件：active 已存在但缺新文件 → seed 应补上"""
        self._run_seed()
        active = self.config_root / "search-crew"
        # 删一个文件模拟升级前不存在
        (active / "limits.yaml").unlink()
        self._run_seed()
        # 已被补回
        self.assertTrue((active / "limits.yaml").exists())


if __name__ == "__main__":
    unittest.main()
