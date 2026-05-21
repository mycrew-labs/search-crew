# Tasks · add-usage-tracking

## 0. 规格门禁

- [x] USER_DESIGN delta 已用户确认（4 条 P-USAGE-*）
- [x] TECH.md 起草
- [x] design.md 起草
- [ ] 本 tasks.md 各项完成
- [ ] 每条 P- 已挂接 TC-
- [ ] capability spec 写入并引用 P-USAGE-*
- [ ] 归档前 Verify TECH references are valid
- [ ] 归档前 Sync final spec changes（delta 合并回 `openspec/` 根目录 + capabilities）

## 1. 公共打点 lib

- [ ] `skills/search-toolkit/scripts/lib/usage.py`：`record(...)` + 文件锁 + 状态目录解析
- [ ] `skills/search-toolkit/scripts/lib/pricing.py`：`estimate(backend, endpoint, units) -> (cost, source)`
- [ ] 把 `_http.py` 的 `request_json` / `request_text` 改造，调 `record(...)`（不允许业务代码绕过）

## 2. 单价表

- [ ] `defaults/pricing.yaml`：内置 Jina / Serper 首版单价表（加 `_last_updated` 字段）
- [ ] 把 `pricing.yaml` 纳入 `seed_user_config.py` 拷贝清单
- [ ] `usage.jsonl` schema 中实际记录 `pricing_source`

## 3. 摘要生成

- [ ] `skills/search-toolkit/scripts/finalize_usage.py`：聚合 `<run_root>/usage.jsonl` → `<run_root>/usage-summary.md` + 追加 `~/.local/state/search-crew/runs.jsonl`
- [ ] `lib/output.py`（init-search-crew 已规划）的 subagent 写盘流程钩入：subagent 结束前调用 `finalize_usage.py --subagent <name> <run_root>` 生成切片 summary
- [ ] 主 agent prompt 中插入：最终回复前必跑 `python3 finalize_usage.py <run_root>`

## 4. Agent 一行总览

- [ ] 改 `agents/fast-search.md` / `site-search.md` / `deep-search.md`：subagent 返回时把 `run_root` 显式回传给上级
- [ ] 改 `commands/deep-search.md`（主 agent 模板）：最终回复必须 append 一行 `📊 本次估算 ~$X.XXX USD（N 次调用 · 单价完整 / 部分缺失）`，**不附路径**
- [ ] 主 agent prompt 注明：用户追问明细 → Read `<run_root>/usage-summary.md` 后展示；用户追问历史 → 提示用户 `! python3 .../usage.py`，**不**主动调

## 5. `usage.py` 独立查询

- [ ] `skills/search-toolkit/scripts/usage.py`：`--last N` / `--by-day` / `--by-week` / `--by-month` / `--by-backend` / `--since` / `--raw`
- [ ] 输出走 stdout markdown / 表格；纯本地无网络
- [ ] README / EXTENDING 加一行说明用 `!` 跑

## 6. Routing 格式同步（与 init-search-crew 协调）

- [ ] 决定 `routing.yaml` 是否同步改 `routing.json`（理由：保持零依赖）。决策后同步更新 init-search-crew TECH.md

## 7. 验证清单

- [ ] **TC-USAGE-001**：跑一次完整 fast-search，断言：
    - `<run_root>/usage.jsonl` 有调用记录
    - `<run_root>/fast-search/usage-summary.md` 存在含按 backend 拆分
    - `<run_root>/usage-summary.md` 存在含全局汇总
    - 主 agent 回复只追加一行 `📊 本次估算 ...`，**不含**路径
- [ ] **TC-USAGE-002**：跑两次完整 run，断言：
    - `~/.local/state/search-crew/calls.jsonl` 行数 = 两次 run 的调用总和
    - `~/.local/state/search-crew/runs.jsonl` 多 2 行
    - 卸载 plugin 后这些文件仍在
- [ ] **TC-USAGE-003**：临时把 `~/.config/search-crew/pricing.yaml` 中 `jina.search` 改成 `0.999`，下一次 run 的 cost 反映新单价；删除该字段，调用走 `defaults/pricing.yaml` 兜底；删 defaults 中也没有的 backend → `pricing_source = "unknown"`，summary 显式标注「单价未知」
- [ ] **TC-USAGE-004**：在 Claude Code 中用户输入 `! python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/usage.py --last 5`，输出落在用户终端；下一轮主 agent 视野中**不含**该输出（context 卫生测试）
- [ ] **TC-CONTEXT-001**（贯穿性）：grep 主 agent 最终回复，断言不含 `/tmp/search-crew/` 字符串

## 8. 归档前同步

- [ ] 把 `USER_DESIGN.md` 内容（P-USAGE-001~004）追加到 `openspec/USER_DESIGN.md`（项目根）
- [ ] 把 `TECH.md` 内容（T-USAGE-001~007）追加到 `openspec/TECH.md`（项目根）
- [ ] 把 `capabilities/usage-tracking/spec.md` 移入 `openspec/specs/capabilities/usage-tracking/`
- [ ] 更新 `openspec/specs/INDEX.md` 台账
- [ ] 删除 / 归档 `openspec/changes/add-usage-tracking/`
- [ ] 把 Backlog B-005 标为已完成（在 `openspec/project.md`）
