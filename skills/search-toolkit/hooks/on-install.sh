#!/usr/bin/env bash
# Plugin 安装后钩子。
#
# 1. 检查 Python 3.10+（脚本仅用 stdlib，零依赖）
# 2. 首次拷贝 defaults/ → ~/.config/search-crew/
# 3. 跑 check_backends.py 报告环境
# 4. 给用户一份清晰的下一步指引

set -u   # 不设 -e：允许个别检查失败仍继续

ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}"
SCRIPTS="$ROOT/skills/search-toolkit/scripts"

echo "================================================================"
echo "  Search Crew Plugin · 安装后检查"
echo "================================================================"
echo

# --- 1. Python ---
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ 未发现 python3。Search Crew 脚本需要 Python 3.10+。"
  echo "   mac:    brew install python"
  echo "   linux:  apt install python3 / dnf install python3"
  exit 1
fi
PY_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
echo "✅ python3 $PY_VERSION"

# --- 2. 拷贝 defaults → ~/.config/search-crew/ ---
echo
echo "→ 检查 ~/.config/search-crew/"
if python3 "$SCRIPTS/seed_user_config.py"; then
  echo "✅ active 配置目录就绪"
else
  echo "⚠️  seed 失败，请检查权限"
fi

# --- 3. backend / Chrome / MCP 检查 ---
echo
echo "→ 检查搜索 backend / Chrome / MCP"
python3 "$SCRIPTS/check_backends.py" || true

# --- 4. 后续指引 ---
echo
echo "================================================================"
echo "  下一步"
echo "================================================================"
cat <<'EOF'

【可选】配置 API key（不配置也能用，会 fallback 到 Claude Code 内置 WebSearch/WebFetch）：

  # 加到 ~/.zshrc
  export JINA_API_KEY="..."   # https://jina.ai
  export SERPER_API_KEY="..." # https://serper.dev
  export GITHUB_TOKEN="..."   # https://github.com/settings/tokens（只需 public_repo）

  source ~/.zshrc
  # 然后重新打开 Claude Code 让 plugin 拿到新环境变量

【强烈建议】备份你的 active 配置（长期沉淀，丢了哭死）：

  把 ~/.config/search-crew/ 放到 iCloud / Dropbox / 你自己的 dotfiles 仓库，
  原位置改成软链接；或者定期手动备份。

【可选】注册 Stop hook（让 pending 学习区在每次主 agent 工作结束时自动提示你）：

  在 ~/.claude/settings.json 加入：

  {
    "hooks": {
      "Stop": [
        {
          "command": "python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/stop_hook.py"
        }
      ]
    }
  }

  （具体字段格式以你本机的 Claude Code 版本为准）

【测试】

  对话直接说：「查一下当前最流行的开源 LLM 推理框架」（关键词触发 fast-search）
  /deep-search 深入调研开源 LLM 推理框架的现状
  ! python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/usage.py --last 10

EOF
