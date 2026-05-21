# Tasks · init-search-crew

> 实现期可执行步骤 + 规格同步项 + 验证清单。完成一项打勾一项；遇到偏差先回头同步 USER_DESIGN / TECH，再继续。

## 0. 规格门禁

- [x] USER_DESIGN delta 已经用户确认
- [x] TECH.md 起草
- [x] design.md 起草，OPEN-AGENT-002-A 已选定方案 C
- [ ] 本 tasks.md 各项完成
- [ ] 每条新增 P- 行为已挂接 TC- 测试用例
- [ ] capabilities/<name>/spec.md 各能力 spec 写入并引用 P-
- [ ] 归档前 Verify TECH references are valid
- [ ] 归档前 Sync final spec changes（delta 合并回 `openspec/` 根目录 + `openspec/specs/capabilities/`）

## 1. 仓库骨架

- [ ] 写 `.claude-plugin/plugin.json`（含 `mcpServers.chrome-devtools`）
- [ ] 写 `defaults/README.md` + `defaults/routing.yaml`（首版起点表）+ `defaults/adapters/` 占位
- [ ] 写 `agents/fast-search.md`、`agents/site-search.md`、`agents/deep-search.md`（含模型选择、prompt 主体、产物契约、循证 / 证据约束）
- [ ] 写 `commands/deep-search.md`、`commands/setup.md`

## 2. Skill: search-toolkit

- [ ] `skills/search-toolkit/SKILL.md`（脚本签名、JSON schema、错误约定、调用 ROUTING.md 的说明）
- [ ] `skills/search-toolkit/ROUTING.md`（路由起点表 + 适配器清单 + 循证四步硬规则；与 `defaults/routing.yaml` 内容对齐）
- [ ] `scripts/lib/__init__.py`：`BackendError`、`normalize_result`、`emit`、`env`
- [ ] `scripts/lib/_http.py`：stdlib `urllib` 封装 JSON / text 请求
- [ ] `scripts/lib/jina.py`、`scripts/lib/serper.py`
- [ ] `scripts/lib/sites/__init__.py`（适配器注册表 + Algolia 索引清单）
- [ ] `scripts/lib/sites/{github,mdn,algolia,readthedocs,pypi,npm}.py`
- [ ] `scripts/lib/config.py`：`load_active_config()`、`load_pending()`、active / pending 路径常量
- [ ] `scripts/lib/runtime.py`：`get_session_id()` 按 T-SESSION-001 的优先级实现
- [ ] `scripts/lib/output.py`：`EvidenceWriter`、INDEX.md 模板、关键词头部、附件 hash 写盘
- [ ] `scripts/search.py`（通用搜索入口）
- [ ] `scripts/fetch.py`（URL → markdown，Jina Reader 优先）
- [ ] `scripts/site_search.py`（站点搜索入口；`--list-adapters` 子命令）
- [ ] `scripts/check_backends.py`（被 `/setup` 调用）
- [ ] `scripts/seed_user_config.py`（首次拷贝 defaults → `~/.config/search-crew/`，带 flock 与幂等守卫）
- [ ] `scripts/stop_hook.py`（扫 pending，输出 hook 消息）
- [ ] `skills/search-toolkit/hooks/on-install.sh`（plugin 安装后调 seed_user_config + check_backends）

## 3. Skill: browser-control

- [ ] `skills/browser-control/SKILL.md`：何时启用 MCP、与 fetch.py 的边界、chrome-devtools-mcp 工具集分类、错误处理、Chrome profile 安全建议

## 4. 配置真相与 onboarding

- [ ] `/setup` 命令：检查 backends + Chrome + MCP + `~/.config/search-crew/` 状态；首次运行醒目提示备份 / 软链接（P-CONFIG-001 onboarding 段）

## 5. Stop hook 接入（依赖外部验证）

- [ ] 验证：在本机 Claude Code 上手写一个 stop hook hello world，确认 stdout 是否注入下一轮上下文
- [ ] 如果协议确认 → 把 `scripts/stop_hook.py` 接进用户 `~/.claude/settings.json`（plugin 自带样例 + setup 命令引导用户接入）
- [ ] 如果协议不通 → 兜底提供 `/search:review-pending` 命令（design.md 已记）

## 6. 文档

- [ ] `README.md` 已存在（vision + 阶段路线图 + 治理）
- [ ] `EXTENDING.md`：新增 backend / 新增站点适配器 / 新增 ROUTING 主题三种扩展指引
- [ ] `.env.example`：可选 API key 清单（JINA / SERPER / GITHUB）

## 7. 验证清单（每条 P- 对应 TC-）

- [ ] **TC-CMD-001**：日常对话「查一下 X」自动派 fast-search 不需 slash command；`/deep-search Y` 派 deep；无 `/search` / `--site`
- [ ] **TC-AGENT-001**：三个 subagent 都产出 ranking + 摘要（grep 索引文件确认）
- [ ] **TC-AGENT-002**：deep-search 第一轮产出 `plan.md`；正常情况下完成清单即结束；max_rounds 兜底有效
- [ ] **TC-AGENT-003**：site-search 命中 github.com 走 API 适配器，命中无适配器站点走 fetch URL，再不行才用 MCP；命令日志可证
- [ ] **TC-ROUTE-001**：手工构造一个落在「学术论文」起点的 query，断网 arxiv 后看是否标注「未在官方源验证」；fast-search 派出去的结果也走复核
- [ ] **TC-FALLBACK-001**：`unset JINA_API_KEY SERPER_API_KEY` 后 `search.py` 输出 `WEBSEARCH_FALLBACK`，主 agent 改用 WebSearch
- [ ] **TC-DATA-001**：单次 deep-search 调多个 fast/site，所有产物在同一 `<deep-session_id>/` 根目录下；用户视角只有一个根
- [ ] **TC-OUTPUT-001**：检查任一 run 的 INDEX.md 是 wiki 风格大纲（含子文件简介、推荐与否、ranking 备注、关键词清单）；attachments/ 用 hash 命名；deep-search 同时产出 `report.html` 与 `report.md`
- [ ] **TC-MCP-001**：`/plugin install search-crew` 触发 npx 拉起 chrome-devtools-mcp；`/setup` 报告 Chrome 检查结果
- [ ] **TC-PARALLEL-001**：deep-search 一轮内多个 subagent 在同 message 派出；TaskList 在派发前已有任务记录
- [ ] **TC-CONFIG-001**：首次安装后 `~/.config/search-crew/` 出现并含 defaults 拷贝；二次安装 / 用户改完后再装不覆盖
- [ ] **TC-LEARN-001**：人为往 `pending/` 放一条；下一次 Stop 时收到提示；用户回「晋升」后该条进入 active
- [ ] **TC-UX-001**：`/deep-search` 启动时主 agent 文本输出协作邀请；用户中途贴入的数据源在下一轮派发优先采纳
- [ ] **TC-EVIDENCE-001**：deep-search `report.md` / 主 agent 最终回复中每段结论附 URL（结论性段落含原文摘录 + 数字）；缺失视为缺陷

## 8. 归档前同步

- [ ] 把 `openspec/changes/init-search-crew/USER_DESIGN.md` 内容合并进 `openspec/USER_DESIGN.md`（项目根）
- [ ] 把 `openspec/changes/init-search-crew/TECH.md` 合并进 `openspec/TECH.md`（项目根）
- [ ] 把各 capability spec 移入 `openspec/specs/capabilities/<name>/spec.md`
- [ ] 更新 `openspec/specs/INDEX.md` 台账
- [ ] 删除 / 归档 `openspec/changes/init-search-crew/`（按 OpenSpec 归档约定）
