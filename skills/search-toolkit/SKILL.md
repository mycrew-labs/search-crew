---
name: search-toolkit
description: Search Crew 的搜索 / 抓取 / 站点 API / 产物组织工具包。供 fast-search / site-search / deep-search 三个 subagent 复用。零依赖 Python stdlib。
---

# search-toolkit

供 Search Crew subagent 调用的工具集。所有脚本都遵循统一 JSON CLI 契约，方便从 Bash 调起。

## 路径

所有脚本：`$CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/`。

## CLI 入口

| 脚本 | 用途 | 关键参数 |
|---|---|---|
| `search.py` | 通用搜索 | `--query`、`--max-results`、`--language`、`--prefer jina\|serper` |
| `fetch.py` | URL → markdown | `<url>` |
| `site_search.py` | 站点搜索（API 适配器优先） | `--site`、`--query`、`--max-results`；`--list-adapters` 列清单 |
| `check_backends.py` | 检查 backend / Chrome / MCP 状态 | 无参数 |
| `seed_user_config.py` | 拷贝 defaults → `~/.config/search-crew/` | 无参数（首次安装 / 兜底） |
| `stop_hook.py` | Stop 事件扫 pending 提示 | 通过 stdin 接 hook input |
| `finalize_usage.py` | 聚合 usage.jsonl → usage-summary.md | `<run_root>`；`--subagent <name>` 切片 |
| `usage.py` | 跨 run 用量查询（用户用 `!` 跑） | `--last N` / `--by-day` / `--by-week` / `--by-month` / `--by-backend` / `--since` / `--raw` |

## 通用输出契约

### 成功

```json
{ "backend": "jina", "results": [{"title": "...", "url": "...", "snippet": "...", "extra": {...}}, ...] }
```

所有 backend 返回的 `results[*]` 统一 schema：`{title, url, snippet, extra}`。

### 失败 / fallback

```json
{ "backend": null, "results": [], "fallback": "WEBSEARCH_FALLBACK" }
{ "source": null, "fallback": "WEBFETCH_FALLBACK" }
{ "adapter": null, "hint": "...", "results": [] }
```

调用方收到 fallback marker 时改用 Claude Code 内置 WebSearch / WebFetch 工具。

## Backend 路由起点（决策依据）

详见 [ROUTING.md](./ROUTING.md)。**Leader（主 agent / deep-search）按主题选择 backend，不要盲目降级**。

## 产物组织约定（P-DATA-001 / P-OUTPUT-001）

subagent 落盘时必须遵守：

1. 文件 / 子目录前缀以 subagent 名开头：`fast-search-*` / `site-search-*` / `deep-search-*`
2. 每个 subagent 必产 wiki 风格 `INDEX.md`（含子文件简介、ranking、推荐与否、关键词清单）
3. 单 markdown 头部 YAML front-matter 含 `keywords`、`url`、`ranking`、`recommended`
4. 关键片段用 `### anchor: <slug>` 标记，供报告 / 摘要按 anchor 引用
5. 附件统一 `<run_root>/attachments/<sha256[:12]>.<ext>`，markdown 用相对路径 `![](../attachments/<hash>.<ext>)`

`lib/output.py` 提供工具函数：

- `attachment_path(run_root, content, ext)` → 附件去重写盘
- `write_front_matter(keywords, **extra)` → 生成 YAML front-matter
- `evidence_anchor(slug)` → 生成 anchor markdown
- `render_index_md(...)` → 生成 INDEX.md 模板

## Usage 打点（P-USAGE-*）

`lib/_http.py` 出口自动调 `lib/usage.py:record(...)`，业务代码**禁止**绕过自己写 jsonl。打点字段见 [TECH T-USAGE-002](../../openspec/changes/add-usage-tracking/TECH.md)。

subagent 结束前必须调：

```bash
python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/finalize_usage.py --subagent <name> <run_root>
```

主 agent 在最终回复前调一次全局聚合：

```bash
python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/finalize_usage.py <run_root>
```

主 agent 给用户的回复**只一行** cost 总览（详见 commands/deep-search.md）。

## 错误处理

- HTTP 4xx / 解析错误 → `BackendError(retryable=False)`，调用方放弃
- HTTP 429 / 5xx / 超时 → `BackendError(retryable=True)`，调用方可重试或降级
- 无 key / 全部 backend 不可用 → 进程退出 0 + `fallback` 字段标 marker
