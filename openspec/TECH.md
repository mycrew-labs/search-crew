# TECH

> 项目级架构决策（ADR 风），AI 拥有，可按需迭代。重大架构转向 SHOULD 主动告知用户。
>
> 具体每条 ADR 服务于 `USER_DESIGN.md` 的某条不变量。不在本文件复述行为细节——行为定义在 `openspec/specs/<capability>/spec.md`。

## T-ARCH-001 ：Plugin 目录结构与三类入口

- `.claude-plugin/plugin.json` 声明 `mcpServers.chrome-devtools`（Claude Code 安装即拉起）
- `agents/{fast,site,deep}-search.md`：三个 subagent 定义（含 prompt）
- `commands/{deep-search,setup}.md`：用户显式 slash command
- `skills/search-toolkit/`（Python 工具包）+ `skills/browser-control/`（MCP 使用规范）
- `defaults/` 首次安装一次性拷贝到 `~/.config/search-crew/`

服务于：`I-CONFIG-001`、`I-DATA-001`。

## T-ARCH-002 ：Subagent 模型分层

- `fast-search` → 轻量级模型（默认 `claude-haiku-4-5-20251001`）
- `site-search` → 中等模型（默认 `claude-sonnet-4-6`）
- `deep-search` → 旗舰模型（默认 `claude-opus-4-7`）

用户可在 active config 内通过 alias 改。理由：分层降本，复杂度匹配模型能力。

## T-STDLIB-001 ：Python 脚本零第三方依赖

所有 `skills/search-toolkit/scripts/` 仅用 Python 3.13 stdlib（含极简自研 YAML subset parser `lib/_yaml.py`）。

理由：

- plugin 安装零依赖摩擦，不要求用户 `pip install`
- 跟 `uv` 单文件脚本模式兼容
- 复杂度可控（YAML subset parser 约 200 行，覆盖本项目所有配置）

服务于：`I-FALLBACK-001`、`I-CONFIG-001`。

## T-HTTP-001 ：HTTP 调用统一出口 + 自动 cost 打点

所有 backend / 站点适配器经 `lib/_http.py` 的 `request_json` / `request_text`。出口处统一调 `lib/usage.py:record(...)` 打点。

业务代码**不允许**绕过 `_http.py` 自行写 jsonl。

理由：保证 cost 统计零漏报；schema 一致；retry / 超时 / 错误分类集中。

服务于：`I-EVIDENCE-001`（cost 是循证的一部分）。

## T-CONFIG-001 ：用户态 active 配置生命周期

- 首次安装：`skills/search-toolkit/hooks/on-install.sh` 调 `seed_user_config.py` 把 `defaults/` 拷到 `~/.config/search-crew/`
- 运行时：`lib/config.py` 永远只读 active 目录（带 flock 兜底 seed）
- 升级：plugin 内置 `defaults/` 可以变，但**不影响** active
- pending 学习区：`~/.config/search-crew/pending/` 由 Stop hook 扫描，AI 写入候选规则

服务于：`I-CONFIG-001`、`I-LEARN-001`。

## T-STATE-001 ：Usage 持久化路径区分

- 临时（per-run，会被 OS 清）：`/tmp/search-crew/<session_id>/usage.jsonl`
- 永久（跨 run，用户不删则永存）：`~/.local/state/search-crew/{calls,runs}.jsonl`

理由：configuration vs statistics 语义分离——配置走 `~/.config/`，统计走 `~/.local/state/`（XDG 约定）。

服务于：`I-CONFIG-001`（统计不污染配置）。

## T-MCP-001 ：chrome-devtools-mcp 通过 plugin.json 自动拉起

不在 plugin 自身代码中调 MCP；声明在 `.claude-plugin/plugin.json` 的 `mcpServers` 字段，Claude Code 安装时自动启动 `npx -y chrome-devtools-mcp@latest`。

理由：MCP server 由 plugin 声明，不增加 plugin 代码复杂度；用户唯一前置条件是本机有 Chrome。

服务于：site-search 浏览器降级路径。

## T-EVIDENCE-001 ：证据 anchor + INDEX wiki 大纲

- 每个 subagent 落盘的 markdown 头部含 YAML front-matter（`url`、`ranking`、`recommended`、`keywords`）
- 关键段落用 `### anchor: <slug>` 标记，供 deep-search 报告 / 主 agent 引用
- 每个 subagent 必产 wiki 风格 `INDEX.md`，含子文件简介、ranking、推荐与否、关键词清单

理由：让主 agent 像浏览代码库一样自助导航；让用户复核成本极低。

服务于：`I-EVIDENCE-001`、Vision 的「数据关联关系」主轴。

## T-ATTACH-001 ：附件 sha256 hash 去重

抓取到的二进制 / 大文本附件统一写 `<run_root>/attachments/<sha256[:12]>.<ext>`。markdown 用相对路径 `../attachments/<hash>.<ext>` 引用。

理由：天然去重；hash 短到 12 字符碰撞概率单 run 内可视为零。

## T-PARALLEL-001 ：subagent 派发用 TaskCreate / TaskUpdate

不用旧 `TodoWrite`，按 Claude Code v2.1.142 / Agent SDK 0.3.142 起的官方结构化任务工具（[文档](https://code.claude.com/docs/en/agent-sdk/todo-tracking)）。

服务于：`I-PARALLEL-001`。
