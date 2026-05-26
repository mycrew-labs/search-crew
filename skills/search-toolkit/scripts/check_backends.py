#!/usr/bin/env python3
"""检查 backend / Chrome / MCP / 用户配置目录状态，供 /setup 调用。

输出 JSON：
{
  "search_backends": { "jina": {...}, "serper": {...}, "webfetch_fallback": {...} },
  "fetch_backends": { ... },
  "browser": { "chrome": {...}, "mcp": {...} },
  "active_config": { "path": "~/.config/search-crew", "exists": true, "missing_files": [...] },
  "state_dir": { "path": "~/.local/state/search-crew", "exists": true },
  "adapters": { ... }
}
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys

from lib import emit, env
from lib import config
from lib.sites import list_adapters


def _check_jina() -> dict:
    if env("JINA_API_KEY"):
        return {"available": True, "note": "JINA_API_KEY 已配置"}
    return {
        "available": False,
        "note": "未配置 JINA_API_KEY（Reader 仍可匿名用，Search 会跳过）",
        "register": "https://jina.ai",
        "env_template": 'export JINA_API_KEY="..."  # 加到 ~/.zshrc',
    }


def _check_serper() -> dict:
    if env("SERPER_API_KEY"):
        return {"available": True}
    return {
        "available": False,
        "register": "https://serper.dev",
        "env_template": 'export SERPER_API_KEY="..."  # 加到 ~/.zshrc',
    }


def _check_github_token() -> dict:
    if env("GITHUB_TOKEN"):
        return {"available": True}
    return {
        "available": False,
        "note": "GitHub API 匿名访问限流为每分钟 10 次；建议配置 token 解开",
        "register": "https://github.com/settings/tokens（只需 public_repo 权限）",
        "env_template": 'export GITHUB_TOKEN="..."  # 加到 ~/.zshrc',
    }


def _check_ai_summary() -> dict:
    """AI 综述 backend 三家检查（任一可用即整层可用）。"""
    spec = [
        ("grok", "GROK_API_KEY", "https://console.x.ai", "偏英文舆论 / 实时讨论"),
        ("doubao", "DOUBAO_API_KEY", "https://www.volcengine.com/product/ark", "火山方舟（Doubao/DeepSeek 等），偏中文语境"),
        ("gemini", "GEMINI_API_KEY", "https://aistudio.google.com/app/apikey", "偏全球综述 / 英文资料"),
    ]
    result = {}
    available = 0
    missing_envs = []
    for name, var, register, note in spec:
        if env(var):
            result[name] = {"available": True, "note": note}
            available += 1
        else:
            result[name] = {
                "available": False,
                "note": note,
                "register": register,
                "env_template": f'export {var}="..."  # 加到 ~/.zshrc',
            }
            missing_envs.append(var)
    result["_summary"] = {
        "available_count": available,
        "total": len(spec),
        "fallback": "未配任何 AI key 时 search.py --prefer ai 自动回落到 jina",
        "missing_envs": missing_envs,
    }
    return result


def _check_chrome() -> dict:
    system = platform.system()
    if system == "Darwin":
        try:
            r = subprocess.run(
                ["mdfind", "kMDItemCFBundleIdentifier == com.google.Chrome"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.stdout.strip():
                return {"installed": True, "found_at": r.stdout.strip().splitlines()[:3]}
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
    elif system == "Linux":
        for binary in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
            path = shutil.which(binary)
            if path:
                return {"installed": True, "binary": binary, "found_at": path}
    return {
        "installed": False,
        "note": "未发现 Chrome；site-search 走浏览器路径时会失败",
        "install": "https://www.google.com/chrome/",
    }


def _check_mcp() -> dict:
    try:
        r = subprocess.run(
            ["npx", "-y", "chrome-devtools-mcp@latest", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0:
            return {"available": True, "version": r.stdout.strip()}
        return {"available": False, "stderr": r.stderr.strip()[:200]}
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        return {"available": False, "error": str(e)}


def _check_active_config() -> dict:
    p = config.active_dir()
    exists = p.exists()
    expected = ["routing.yaml", "pricing.yaml", "limits.yaml", "adapters"]
    missing = []
    if exists:
        for f in expected:
            if not (p / f).exists():
                missing.append(f)
    return {
        "path": str(p),
        "exists": exists,
        "missing_files": missing,
        "hint": (
            "首次运行 /setup 时会从 plugin defaults/ 拷贝；之后用户自由修改"
            if not exists
            else None
        ),
    }


def main() -> int:
    payload = {
        "search_backends": {
            "jina": _check_jina(),
            "serper": _check_serper(),
            "websearch_fallback": {"available": True, "note": "Claude Code 内置，零 key 状态可用"},
        },
        "fetch_backends": {
            "jina_reader": {
                "available": True,
                "note": ("有 JINA_API_KEY 走付费配额，无 key 匿名" if not env("JINA_API_KEY") else "已配置"),
            },
            "webfetch_fallback": {"available": True, "note": "Claude Code 内置"},
        },
        "ai_summary_backends": _check_ai_summary(),
        "github_token": _check_github_token(),
        "browser": {
            "chrome": _check_chrome(),
            "mcp": _check_mcp(),
        },
        "active_config": _check_active_config(),
        "state_dir": {"path": str(config.state_dir()), "exists": True},
        "adapters": list_adapters(),
    }
    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
