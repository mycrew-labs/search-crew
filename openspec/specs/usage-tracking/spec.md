# Usage Tracking

API 调用次数与估算成本的打点、汇总、永久持久化、独立查询。参考 [vibe-usage](https://www.npmjs.com/package/@vibe-cafe/vibe-usage) 的模式。

## Purpose

让用户每次拿到调研产物时能直接看到本次花了多少钱（次数 + 估算 cost），并保留所有原始打点供未来做更精细的统计——同时不污染主 agent 的 context。

## Requirements

### Requirement: 每次 run 必落 usage-summary.md
每次 backend 调用 MUST 落一条记录到 `<run_root>/usage.jsonl`。run 结束时 MUST 生成 `<run_root>/usage-summary.md`（人类可读 markdown，含 by_backend / by_subagent 拆分）。每个 subagent 结束前 MUST 在 `<run_root>/<subagent>/usage-summary.md` 写本 subagent 的切片摘要。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 一次完整调研
- **WHEN** 主 agent 跑完一次 deep-search 并调用 `finalize_usage.py <run_root>`
- **THEN** `<run_root>/usage.jsonl` 存在；`<run_root>/usage-summary.md` 存在，内含「调用总数 / 估算合计 / by_backend / by_subagent」段

#### Scenario: 各 subagent 切片
- **WHEN** fast-search 结束前调用 `finalize_usage.py --subagent fast-search <run_root>`
- **THEN** `<run_root>/fast-search/usage-summary.md` 存在，只含本 subagent 的 usage 切片

### Requirement: 主 agent 回复只追加一行 cost 总览
主 agent 在最终回复结尾 MUST 追加且仅追加**一行** cost 总览（形如 `📊 本次估算 ~$X.XXX USD（N 次调用）`）。**MUST NOT** 在回复里附路径、复述按 backend / subagent 的拆分。用户追问明细时主 agent SHALL Read `<run_root>/usage-summary.md` 后呈现拆分；run_root 路径由 subagent 派发时记下，不靠主 agent 自己回想字符串。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 默认回复只一行
- **WHEN** 主 agent 完成调研给用户最终回复
- **THEN** 回复结尾有且仅有一行 cost 总览；不出现 `/tmp/search-crew/`、不出现 `usage-summary.md` 字符串、不列按 backend 拆分

#### Scenario: 用户追问明细
- **WHEN** 用户在 cost 总览出现后说「按 backend 拆开看」
- **THEN** 主 agent 拼出 `<run_root>/usage-summary.md` 路径并 Read，把表格呈现给用户

### Requirement: 原始打点永久持久化到 ~/.local/state/search-crew/
每次打点 MUST 同步追加到 `~/.local/state/search-crew/calls.jsonl`；每次 run 结束 MUST 追加一行汇总到 `~/.local/state/search-crew/runs.jsonl`。这两个文件 MUST 永不自动清理 / 截断 / rotate——任何清理由用户主动做。**MUST NOT** 写入 `~/.config/search-crew/`（配置与统计语义分离）。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 跨 run 累积
- **WHEN** 完成两次独立调研
- **THEN** `~/.local/state/search-crew/calls.jsonl` 行数 = 两次 run 调用之和；`~/.local/state/search-crew/runs.jsonl` 增加 2 行

#### Scenario: 卸载 plugin 后数据仍在
- **WHEN** 用户卸载 plugin 然后重装
- **THEN** `~/.local/state/search-crew/{calls,runs}.jsonl` 不丢，历史数据完整可查

### Requirement: 单价表 pricing.yaml 用户可覆盖
plugin 内置 `defaults/pricing.yaml` 含基线单价；首次安装拷贝到 `~/.config/search-crew/pricing.yaml`；runtime 只读 active 版本；用户改 active 立即生效。某 backend / endpoint 单价未配置时 `cost_estimate_usd` MUST 为 `null`，`pricing_source` 标 `unknown`；usage-summary 中 MUST 显式标注「⚠️ 以下调用单价未知，未计入合计」。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 用户改单价
- **WHEN** 用户在 active `pricing.yaml` 把 `jina.search` 单价改为 0.999
- **THEN** 下一次 run 的 cost_estimate_usd 反映新单价

#### Scenario: 单价缺失
- **WHEN** backend 'brave' 在 pricing.yaml 中无配置，被调用
- **THEN** 该条 jsonl 记录 `cost_estimate_usd: null`、`pricing_source: "unknown"`；usage-summary 末尾标「⚠️ brave:search 等单价未知，未计入合计」

### Requirement: 独立查询入口 usage.py 不进 context
plugin MUST 提供 `scripts/usage.py` 作为独立 CLI 查询入口。用户用 `!` 前缀执行（如 `! python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/usage.py --last 10`），输出落在用户终端，**MUST NOT** 进入任何 agent 的 context。主 agent **MUST NOT** 主动调用 usage.py。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 用户主动跑
- **WHEN** 用户在 Claude Code 输入 `! python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/usage.py --last 5`
- **THEN** 输出列出最近 5 次 run 的 cost；输出**不**进入主 agent 的 context（用户终端直出）

#### Scenario: 主 agent 不主动调
- **WHEN** 用户在对话中说「我想看历史」
- **THEN** 主 agent 提示用户跑 `! python3 .../usage.py --last 10`，**不**自己用 Bash 跑该命令

### Requirement: 业务代码不允许绕过 _http.py 自行打点
所有 backend 调用 MUST 经 `lib/_http.py` 出口；业务代码 MUST NOT 自行写 `usage.jsonl`。打点 schema 由 `lib/usage.py:record(...)` 统一负责。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 新 backend 添加
- **WHEN** 加一个新 backend 模块
- **THEN** 该模块的 HTTP 请求通过 `lib/_http.py:request_json` / `request_text`；打点自动产生，不需要 backend 代码手写
