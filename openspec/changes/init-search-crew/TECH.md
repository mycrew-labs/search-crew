# TECH delta · init-search-crew

> 本文件为 change `init-search-crew` 的 TECH delta。归档后并入 `openspec/TECH.md`（项目根）。
>
> AI 在实现过程中可按需迭代本文件。每条 T- 决策都引用 `USER_DESIGN.md` 的 `P-` 编号，**不另立产品行为**。

## 技术决策台账

| 编号 | 描述 | 服务于 |
|---|---|---|
| T-PLUGIN-001 | Plugin 目录结构与 `.claude-plugin/plugin.json` 声明 | P-MCP-001 / P-CONFIG-001 |
| T-RUNTIME-001 | Subagent / Skill 脚本在运行时优先读 `~/.config/search-crew/`，plugin 内置 `defaults/` 仅用于首次拷贝 | P-CONFIG-001 |
| T-SEED-001 | 首次安装拷贝 defaults 的触发时机与幂等性 | P-CONFIG-001 |
| T-PENDING-001 | Pending 学习区目录布局 + Stop hook 提示交互 | P-LEARN-001 |
| T-SESSION-001 | Subagent 获取自己 session-id 的方式 | P-DATA-001 |
| T-OUTPUT-001 | 产物目录布局 + wiki 索引文件名 / 结构 + ranking / 关键词 schema | P-DATA-001 / P-OUTPUT-001 |
| T-ATTACH-001 | 附件去重与本地引用机制 | P-OUTPUT-001 |
| T-REPORT-001 | deep-search 双格式 `report.html` / `report.md` 输出契约 | P-AGENT-001 / P-OUTPUT-001 |
| T-EVIDENCE-001 | 证据 anchor 格式：跳回原始 markdown 段落的标识 | P-EVIDENCE-001 |
| T-ROUTE-001 | 循证四步在 subagent prompt + skill 工具中的落地机制 | P-ROUTE-001 |
| T-BACKEND-001 | 搜索 / 抓取脚本 CLI 契约：JSON in/out、stdlib 优先、fallback marker | P-FALLBACK-001 |
| T-ADAPTER-001 | 站点适配器注册表 + 用户态扩展点 | P-AGENT-003 / P-CONFIG-001 |
| T-MCP-001 | chrome-devtools-mcp 通过 plugin.json 自动拉起 + Chrome 检查 | P-MCP-001 |
| T-DISPATCH-001 | 主 agent / deep-search 同 turn 并行派发 + TaskCreate / TaskUpdate 工作流 | P-PARALLEL-001 / P-CMD-001 |
| T-UX-001 | subagent 启动协作邀请的输出位置（主 agent 文本输出 vs PreToolUse hook） | P-UX-001 |

---

## T-PLUGIN-001 ：Plugin 目录结构

```
search-crew/
├── README.md
├── .gitignore
├── .claude-plugin/
│   └── plugin.json
├── openspec/                             # 治理
├── agents/                               # subagent 定义
│   ├── fast-search.md
│   ├── site-search.md
│   └── deep-search.md
├── commands/                             # slash 命令（仅 deep-search + setup）
│   ├── deep-search.md
│   └── setup.md
├── skills/
│   ├── search-toolkit/
│   │   ├── SKILL.md
│   │   ├── ROUTING.md                    # 路由起点表（首版基线）
│   │   ├── scripts/                      # Python 入口 + lib
│   │   │   ├── search.py
│   │   │   ├── fetch.py
│   │   │   ├── site_search.py
│   │   │   ├── check_backends.py
│   │   │   ├── seed_user_config.py       # 首次拷贝 defaults → ~/.config/search-crew/
│   │   │   ├── stop_hook.py              # Stop hook 入口，扫 pending 提示
│   │   │   ├── output.py                 # 索引 / ranking / 关键词 / 附件 / report 写盘契约
│   │   │   └── lib/                      # backends + sites/
│   │   └── hooks/
│   │       └── on-install.sh             # plugin 安装后种子拷贝触发
│   └── browser-control/
│       └── SKILL.md
└── defaults/                             # 首次安装拷贝到 ~/.config/search-crew/ 的种子内容
    ├── routing.yaml                      # ROUTING.md 的可编辑版本（YAML 易程序化合并）
    ├── adapters/                         # 用户态可自定义的简单适配器（YAML 配置驱动）
    └── README.md
```

`.claude-plugin/plugin.json` ：

- `mcpServers.chrome-devtools` = `npx -y chrome-devtools-mcp@latest`
- 不需要在 plugin.json 里声明 hook；hook 走 `~/.claude/settings.json` 用户配置或 plugin 内 SKILL.md 中说明（取决于 Claude Code plugin 当时支持的 hook 注入机制——见 T-PENDING-001 设计阶段决策）

## T-RUNTIME-001 ：运行时配置读取顺序

所有 subagent / skill 脚本运行时：

1. 仅读 `~/.config/search-crew/` 下的内容（routing、adapters、参数偏好）
2. 永不直接读 plugin 内置 `defaults/`
3. 如果 `~/.config/search-crew/` 不存在 → 触发种子拷贝（T-SEED-001），再读
4. 读 pending 时附带「pending 来源」标记，调用方按 P-LEARN-001 在产物里标注

实现统一在 `lib/config.py`（待实现）中提供 `load_active_config()` / `load_pending()`。

## T-SEED-001 ：首次安装拷贝 defaults

触发顺序：

1. **首选**：plugin 安装钩子 `skills/search-toolkit/hooks/on-install.sh` 执行时调用 `python3 scripts/seed_user_config.py`
2. **兜底**：任何运行时入口（`search.py` / `fetch.py` 等）进入时先检测 `~/.config/search-crew/` 是否存在；不存在则就地拷贝并打日志

幂等约束：

- `seed_user_config.py` 必须用 `if not exists` 守卫，绝不覆盖已有目录
- plugin 升级**不重拷贝**，绝不动 active

拷贝内容：`defaults/` 目录原样拷到 `~/.config/search-crew/`。

## T-PENDING-001 ：Pending 学习区与 Stop hook

目录布局：

```
~/.config/search-crew/
├── routing.yaml
├── adapters/
└── pending/
    ├── routing/
    │   └── <timestamp>-<slug>.yaml      # 新路由候选
    ├── adapters/
    │   └── <timestamp>-<slug>.yaml      # 新适配器配置候选
    └── _meta.json                       # 累计计数 / 上次提示时间
```

Stop hook 流程：

1. Claude Code Stop 事件触发 `scripts/stop_hook.py`
2. 脚本扫描 `pending/` 子目录文件总数 `N`
3. 当 `N > 0` 且距上次提示已超阈值（默认 0，即每次必提示），向 stdout 输出**结构化 hook 消息**
4. 该消息会被 Claude Code 注入下一轮上下文 / 显示给用户
5. 用户回复"晋升 / 丢弃 / 暂留"后，主 agent 调对应工具（`promote_pending` / `discard_pending` / 不动）完成动作

具体 hook 消息格式与触发约定，在 design.md 中确认 Claude Code 当前 Stop hook 协议后定稿。

## T-SESSION-001 ：Subagent 获取自己的 session-id

Claude Code 给 subagent 的运行环境通常注入 `CLAUDE_SESSION_ID`（或类似环境变量）。优先级：

1. 读环境变量 `CLAUDE_SESSION_ID`
2. 兜底读 `$CLAUDE_PLUGIN_ROOT/.session-marker` 之类文件（若存在）
3. 兜底用时间戳 + 短随机串生成（**仅在前两者均不可用时**，并 stderr 警告）

封装在 `lib/runtime.py` 的 `get_session_id()`，全 plugin 唯一来源。design.md 阶段需要核对 Claude Code 当前实际暴露的环境变量名（写错就拿不到正确 id），如果不一致更新本节。

## T-OUTPUT-001 ：产物目录布局 + wiki 索引 schema

```
/tmp/search-crew/<session_id>/
├── INDEX.md                              # wiki 风格主索引（任一 subagent 入口）
├── fast-search/                          # fast-search 落盘
│   ├── INDEX.md                          # fast-search 自己的 wiki 索引
│   ├── fast-search-001.md                # 抓回的内容（content + 关键词头部）
│   ├── fast-search-002.md
│   └── ...
├── site-search/                          # site-search 落盘
│   └── ...
├── deep-search/                          # deep-search 落盘
│   ├── INDEX.md
│   ├── report.html                       # 用户交付物（LLM 自由生成）
│   ├── report.md                         # 主模型交付物（与 html 语义等价）
│   ├── round-1.md / round-2.md / ...     # 轮次总结
│   └── traces/                           # 被 deep-search 派出去的 fast/site 子产物
│       ├── fast-search-<sub_sid>/
│       └── site-search-<sub_sid>/
└── attachments/                          # 全 run 共用附件目录
    ├── <sha256[:12]>.png
    └── ...
```

**INDEX.md schema（wiki 风格大纲）**——见 [USER_DESIGN.md P-OUTPUT-001](USER_DESIGN.md#p-output-001-产物命名前缀索引文件ranking关键词与附件存储) 的「索引文件」段。具体 markdown 模板示例：

```markdown
# INDEX · <subagent-name> · <session_id>

## Input
- query: ...
- params: ...
- 起点路由: ...

## Files (按 ranking 排序)

### ★★★★★  fast-search-003.md
- 来源: https://...
- ranking: 9.2/10
- 推荐: must-read
- 简介: <一段话讲清楚这个文件讲了什么>
- 关键词: react@19, suspense, transition, useTransition, ...

### ★★★☆☆  fast-search-001.md
...

## Keywords (全集)
react@19, suspense, ...

## Next-Read
1. fast-search-003.md（must-read）
2. fast-search-005.md（数据对比表）
```

**单 markdown 头部**：必须包含本文件关键词子集（YAML front-matter 或一段「关键词：」段落），让 `grep` 首次命中即可定位。

## T-ATTACH-001 ：附件去重

- 抓取到的二进制 / 大文本附件统一写入 `<run_root>/attachments/`
- 文件名 = `<sha256(content)[:12]>.<ext>`
- 写之前先检测同名文件是否存在，存在则跳过（天然去重）
- markdown 中引用：`![](../attachments/<hash>.<ext>)`
- INDEX.md 维护 `attachments` 表：`hash → (源 URL, alt, caption)`
- 12 字符 hash 碰撞概率极低（同 run 内可视为零），实现层不做额外冲突处理；如未来发现冲突再走新 change

## T-REPORT-001 ：deep-search 双格式产出契约

- 文件名固定：`report.html` 与 `report.md`，必须位于 `<run_root>/deep-search/` 下
- 产出由 deep-search subagent 在最后一步生成（LLM 自由写法）
- subagent prompt 中硬编码两条产出契约：
  - 文件名必须正确
  - HTML 中的循证链接必须可点击（外部 URL 直接 `<a href>`，本地 markdown 引用用相对路径 `<a href="../fast-search/fast-search-003.md#...">`）
- 主 agent 把 `report.html` 路径告诉用户（提示用 `open report.html` 在浏览器打开）；自己进一步阅读 / 引用走 `report.md`

## T-EVIDENCE-001 ：证据 anchor 格式

- 单 markdown 内用 `### anchor: <slug>` 标记可被外部引用的片段（slug 在 INDEX.md 注册）
- 报告 / 摘要中引用某段证据：`见 [fast-search-003 §<slug>](../fast-search/fast-search-003.md#<slug>)`
- HTML 报告中等价 `<a href="../fast-search/fast-search-003.md#<slug>">`
- 文件级引用（无具体段）：直接 `[fast-search-003](../fast-search/fast-search-003.md)`

写盘契约封装在 `scripts/output.py` 的 `EvidenceWriter` 类，subagent 通过它统一落盘 anchor。

## T-ROUTE-001 ：循证四步落地

- 路由起点表落在 `~/.config/search-crew/routing.yaml`
- 每个 subagent prompt 顶部强制要求"启动前 Read `$CLAUDE_PLUGIN_ROOT/skills/search-toolkit/ROUTING.md`"（用户拷贝后改读 `~/.config/search-crew/routing.yaml`）
- 第三步「回官方源复核」由调用方在拿到 fast-search 结果后**显式派一个 site-search**完成
- 第四步「未在官方源验证」由 site-search 在没找到记录时返回明确状态，主 agent / deep-search 在最终产物中显式标注

不做隐式 enforcement（避免误杀）；以 prompt 约束 + 产物模板约束为主，违例由 reviewer / 用户人工抓。

## T-BACKEND-001 ：搜索 / 抓取脚本 CLI 契约

所有 Python 入口脚本：

- 使用 Python 3.13 stdlib（`urllib`，避免 `requests` 等第三方依赖），符合 plugin 零部署摩擦目标
- CLI 风格：`python3 search.py --query <q> --max-results N --language zh-cn`
- 标准输出 = JSON（`{ "results": [...], "backend": "jina", "fallback": null }`）
- 失败：
  - Backend API 失败 → 抛 `BackendError`，进程退出 1，stderr 写人类可读说明
  - 无可用 backend → 进程退出 0，stdout 输出 `{ "fallback": "WEBSEARCH_FALLBACK" }`，由调用方改用内置 WebSearch

约束：

- 所有 backend 实现统一返回 `{title, url, snippet, extra}` 结构
- 公共定义放 `scripts/lib/__init__.py`

## T-ADAPTER-001 ：站点适配器注册表 + 用户扩展点

两类适配器：

- **代码型**（复杂逻辑）：plugin 内置 + 用户可在 `~/.config/search-crew/adapters/*.py` 加文件
  - 用 entry point 约定：每个模块导出 `SITE`（域名）+ `search(query, max_results) -> list[result]`
- **配置型**（URL 模式 + JSON path / CSS selector）：`~/.config/search-crew/adapters/*.yaml`
  - 由 `lib/sites/_yaml_adapter.py` 通用驱动，零代码扩展

加载顺序：plugin 内置代码型适配器 → 用户态代码型 → 用户态配置型；同 host 后者覆盖前者。

## T-MCP-001 ：chrome-devtools-mcp 拉起 + Chrome 检查

- 通过 `.claude-plugin/plugin.json` 的 `mcpServers.chrome-devtools` 声明，Claude Code 安装 plugin 时按需启动
- `scripts/check_backends.py` 检查：
  - `npx chrome-devtools-mcp@latest --version` 能否执行
  - 系统 Chrome 是否存在（mac: `mdfind kMDItemCFBundleIdentifier == com.google.Chrome`；linux: `which google-chrome chromium`）
- `/setup` 命令调用上述检查，把结果展示给用户

## T-DISPATCH-001 ：并行派发与任务工具

- 主 agent / deep-search 派 subagent 前 MUST 调 `TaskCreate` 建立任务清单
- 一次派多个 subagent 必须在同一 message 里发起多个 Task tool 调用（Claude Code 框架原生支持的并行）
- subagent 完成 → 调 `TaskUpdate` 标 completed
- 工具名以 <https://code.claude.com/docs/en/agent-sdk/todo-tracking> 为准；如 SDK 后续重命名，更新本节

## T-UX-001 ：subagent 启动协作邀请的输出位置

候选实现：

- **方案 A（首选）**：主 agent / `/deep-search` 命令在派发 subagent **之前**，直接在 user-facing text 输出一行「💡 ...」提示
  - 优点：不依赖 hook、跨 SDK 版本稳定、用户直接看到
- **方案 B**：用 PreToolUse hook 拦截 Task 工具调用，注入提示
  - 优点：派发位置统一；缺点：依赖具体 hook 协议

首版走方案 A；方案 B 待 Claude Code hook 体系稳定后评估。
