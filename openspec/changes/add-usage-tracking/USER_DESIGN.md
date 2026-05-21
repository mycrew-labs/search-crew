# USER_DESIGN delta · add-usage-tracking

> 本文件为 change `add-usage-tracking` 的 USER_DESIGN delta。归档后并入 `openspec/USER_DESIGN.md`（项目根）。
>
> **本 delta 内容由用户拍板，AI 不得自行修改。**

## 设计理念

参考 [`@vibe-cafe/vibe-usage`](https://www.npmjs.com/package/@vibe-cafe/vibe-usage) 的模式：

- **raw data 永久持久化**，独立于"是否展示过给用户"——便于未来做更精细的统计 / 分布分析
- **展示给用户的部分尽量不进主 agent context**：主 agent 在回复里只留指针（一句"本次估算 ~$0.02，明细见 ..."），详情走落盘文件或用户主动跑 `! python3 .../usage.py` 看
- 精度要求不高：估算够用，回头能做统计就行

## 产品行为编号台账

| 编号 | 描述 | 测试用例 | 状态 |
|---|---|---|---|
| P-USAGE-001 | 每次 run 必落 cost summary 文件；主 agent 回复只留指针不复述 | TC-USAGE-001 | 待确认 |
| P-USAGE-002 | 原始打点 + 跨 run 累积**永久保留**到 `~/.local/state/search-crew/`，不自动清理 | TC-USAGE-002 | 待确认 |
| P-USAGE-003 | 单价表 `pricing.yaml` 由 plugin 内置 + 用户可在 active 覆盖 | TC-USAGE-003 | 待确认 |
| P-USAGE-004 | 独立查询入口 `scripts/usage.py`，用户用 `!` 跑，输出不进主 context | TC-USAGE-004 | 待确认 |

---

## P-USAGE-001 ：每次 run 必落 cost summary 文件；主 agent 回复只给一行总览

### 行为

- 每次 backend 调用（Jina / Serper / 未来新增的需密钥 API）必须落一条记录到 `<run_root>/usage.jsonl`
- 记录字段：`{ ts, backend, endpoint, status, latency_ms, tokens_or_units, cost_estimate_usd, run_id, subagent }`
- 每个 subagent 在交付前 MUST 把本 subagent 的小计写入 `<run_root>/<subagent>/usage-summary.md`
- run 结束时 MUST 在 `<run_root>/usage-summary.md` 写一份全局汇总（人类可读的 markdown）
- **主 agent 在最终回复用户时**：
    - **只追加一行总览**：`📊 本次估算 ~$X.XXX USD（N 次调用）`
    - **不附文件路径**（避免污染 context；用户绝大多数时候不需要看明细）
    - 不复述按 backend / subagent 的拆分
- **如果用户后续追问明细 / 拆分 / 历史**：
    - 明细 / 拆分 → 主 agent 自己根据本 run 的 `<run_root>` 路径（由 `<session_id>` 推导，约定固定为 `/tmp/search-crew/<session_id>/usage-summary.md`）Read 该文件，展示拆分内容
    - 历史 → 主 agent 提示用户跑 `! python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/usage.py --last N`（用户主动跑，输出不进 context）
- agent 必须知道路径约定，但**不**在回复里写出来——只有被问到时才 Read 并展示

### `usage-summary.md` 模板

```markdown
# 本次使用汇总

- run_id: <session_id>
- 时间: <iso8601> ~ <iso8601>
- 估算合计: ~$0.023 USD（**估算**，可能与官方账单有误差）

## 按 backend

| Backend | 次数 | 估算 cost |
|---|---:|---:|
| jina-search | 8 | ~$0.012 |
| jina-reader | 12 | ~$0.008 |
| serper | 3 | ~$0.003 |
| webfetch-fallback | 2 | $0（内置） |

## 按 subagent

| Subagent | 次数 | 估算 cost |
|---|---:|---:|
| fast-search | 14 | ~$0.014 |
| site-search | 6 | ~$0.006 |
| deep-search | 3 | ~$0.003 |

> 详细打点见 `usage.jsonl`（jsonl 一行一条）。
```

### 不变量

- 每次 run **必须**有 `usage.jsonl` 和 `usage-summary.md`，缺一视为缺陷
- cost 是**估算**，markdown 中必须明确写"估算"字样，不得伪装为精确
- 不计费的调用（如 Claude Code 内置 WebSearch fallback、本地 chrome-devtools-mcp 抓取）SHOULD 也记次数，但 `cost_estimate_usd = 0`
- 主 agent 在回复里**只**追加一行总览，**不**附路径、**不**复述拆分——这是 context 卫生的强约束
- agent 必须知道 `usage-summary.md` 的固定路径约定 `/tmp/search-crew/<session_id>/usage-summary.md`，以便用户追问时即时 Read 展示

## P-USAGE-002 ：原始打点永久持久化（vibe-usage 风）

### 设计原则

借鉴 [`@vibe-cafe/vibe-usage`](https://www.npmjs.com/package/@vibe-cafe/vibe-usage)：

- 把原始调用打点当成**第一类持久化资产**，独立于"是否展示过给用户"
- 现在不做的统计 / 分析，未来想做时 raw data 还在
- 用户卸载 / 重装 plugin、清 `/tmp/`，都不影响 raw data

### 行为

- **打点级 raw**：每次 backend 调用打点除了写 `<run_root>/usage.jsonl`（单 run 临时），还要**追加复制**到 `~/.local/state/search-crew/calls.jsonl`（永久）
- **run 级汇总**：每次 run 结束时把汇总追加到 `~/.local/state/search-crew/runs.jsonl`
- 字段：
    - `calls.jsonl`：与 `<run_root>/usage.jsonl` 同 schema（多加 `run_id` 与 `subagent` 用于 join）
    - `runs.jsonl`：`{ run_id, started_at, ended_at, prompt_summary, totals: { calls, cost_estimate_usd, by_backend } }`

### 位置选择理由

- `~/.local/state/search-crew/` 而**不是** `~/.config/search-crew/`：usage 数据是**统计 / 历史**，不是配置；放配置目录会污染用户备份语义、与 `pricing.yaml` 等真正的偏好混淆
- 沿用 XDG Base Directory 约定（`$XDG_STATE_HOME` 兜底 `~/.local/state/`）
- `/tmp/search-crew/<run_id>/` 是 OS 重启后会清理的临时区，**不**承担永久持久化

### 不变量

- `calls.jsonl` / `runs.jsonl` **永不**自动删除 / 截断 / rotate；任何清理由用户主动做
- 不写入 `~/.config/search-crew/`，避免污染 P-CONFIG-001 的配置真相
- raw 数据保留**所有**调用字段，未来分析需要什么字段都不用回头补
- `~/.local/state/search-crew/` 不存在时由 plugin 自动创建（不需用户配置）

## P-USAGE-003 ：单价表

### 行为

- plugin 内置 `defaults/pricing.yaml`，包含首版支持的 backend 单价（Jina / Serper 等）
- 首次安装拷贝到 `~/.config/search-crew/pricing.yaml`（沿用 P-CONFIG-001 的 seed 机制）
- 运行时只读 `~/.config/search-crew/pricing.yaml`
- 价格过时 → 用户**直接改 active 文件**；plugin 升级**不会**覆盖

### 形态

```yaml
# pricing.yaml
last_updated: "2025-05-15"     # 用户改的话顺手改这行
unit: USD

jina:
  search: 0.0015               # per request
  reader: 0.0007               # per request

serper:
  search: 0.001                # per request

# 未来扩展示例（用户自加）
# openai:
#   gpt-5-input: 0.0000025     # per token
#   gpt-5-output: 0.00001
```

### 不变量

- 单价表是 active 配置的一部分，遵循 P-CONFIG-001 / P-LEARN-001 的所有权约束
- 不出现在 plugin 内置 defaults 里的 backend 调用 → cost_estimate_usd = null（不为 0，与"已知不计费"区分）；产物中显式标注「单价未知」

## P-USAGE-004 ：独立查询入口（不进主 context）

### 设计原则

参考 [`@vibe-cafe/vibe-usage`](https://www.npmjs.com/package/@vibe-cafe/vibe-usage) 的 standalone CLI 模式：用户主动跑命令查看历史 / 分布，结果直出终端，**不进任何 agent 的 context**。

### 行为

- plugin 提供 `scripts/usage.py`，从 `~/.local/state/search-crew/{calls,runs}.jsonl` 读取数据
- 用户通过 **`!` 前缀**在 Claude Code 中执行（用户记忆中 `! <command>` 是直接 shell 执行，输出落在用户终端但**不**注入 agent context）
- 调用示例：
  ```
  ! python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/usage.py --last 10
  ! python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/usage.py --by-day
  ! python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/usage.py --by-backend
  ```
- 首版功能（最小可用）：
    - `--last N`：列最近 N 次 run 的 cost 摘要
    - `--by-day` / `--by-week` / `--by-month`：按时间段汇总
    - `--by-backend`：按 backend 汇总
    - `--raw`：直接 dump `calls.jsonl` 给用户自己 jq

### 与主 agent 的关系

- 主 agent 在最终回复**仅**提一次 `usage.py` 的存在（"想看历史可跑 ..."），不主动调用它
- 用户主动跑 `! ...` 时，主 agent 不参与；输出对话上下文 100% 不进入 agent 视野

### 不变量

- `usage.py` 必须能在没有 backend key / 没有网络的情况下纯本地跑通（它只读 jsonl）
- 输出 **MUST NOT** 包含 PII / 用户原始 query 中可能的敏感片段（首版直接不存 query，只存 endpoint 与 meta；如未来要存需走新 change）
- plugin **不**主动派 subagent 帮用户跑统计——必须保持"用户主动 `!` 调"才能不进 context
