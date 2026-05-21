"""tests 包初始化：把 plugin scripts 目录加进 sys.path 让测试能 import lib。"""

from __future__ import annotations

import pathlib
import sys

_SCRIPTS = (
    pathlib.Path(__file__).resolve().parents[1]
    / "skills"
    / "search-toolkit"
    / "scripts"
)
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
