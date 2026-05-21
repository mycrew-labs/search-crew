# Design · add-usage-tracking

## Raw 数据 vs Summary 数据的边界

不要让 raw 数据与 summary 数据互为索引。两者各司其职：

| 类型 | 文件 | 写入时机 | 谁读 |
|---|---|---|---|
| Raw 调用打点（临时） | `<run_root>/usage.jsonl` | 每次调用即时追加 | `finalize_usage.py` 聚合用；用户调试时 jq |
| Raw 调用打点（永久） | `~/.local/state/search-crew/calls.jsonl` | 每次调用即时追加 | `usage.py` |
| Run 汇总（永久） | `~/.local/state/search-crew/runs.jsonl` | run 结束时追加一行 | `usage.py` 主要数据源 |
| Run 摘要 md（临时） | `<run_root>/usage-summary.md` | run 结束时生成 | 主 agent 被追问时 Read |
| Subagent 切片 md（临时） | `<run_root>/<subagent>/usage-summary.md` | subagent 结束时生成 | 调试 / 用户深入查看 |

设计原则：**写多份是廉价的**（jsonl 一行几十字节），不要为了节省去做实时聚合（聚合期容易丢数据 / 难并发）。

## Agent 如何在追问时拼路径

无需把路径写进 context，但 agent 必须有约定。两种做法：

### A. 路径硬编码在 agent prompt

把 `/tmp/search-crew/<session_id>/usage-summary.md` 写进 `agents/*.md` 的 prompt 模板。agent 自己知道 `session_id` 是当前 subagent / 主 agent 的 session id（已有 `get_session_id()` 概念）。

- ✅ 零运行时依赖；agent 启动时就知道
- ⚠️ session_id 在主 agent 视角是什么？主 agent 自己也是一个 session
- ⚠️ 主 agent 派出去的 subagent 是另外的 session id；产物根目录由 deep-search 派 fast-search 时显式传

### B. agent 跟踪它发起的 run 的 run_root

主 agent 调 deep-search / fast-search / site-search 时，subagent 返回 `(run_root, summary)`。主 agent 把 `run_root` 记在某处（最简单是同 turn message 里）。用户追问"看明细"时，主 agent 用记下来的 `run_root` 拼 `<run_root>/usage-summary.md`。

- ✅ 直接、无歧义；天然支持「同一次对话里跑了多次调研」
- ⚠️ 主 agent 必须在派发完返回前记录 run_root（这本来就是 P-DATA-001 的要求）

**采纳 B**。理由：P-DATA-001 已经要求 subagent 返回 run_root；usage-summary.md 在 run_root 下是固定约定，主 agent 拼起来 trivial。

### 反模式

- ❌ 主 agent 每次回复都把 run_root 写出来（污染 context）
- ✅ run_root 在主 agent 工作记忆 / TodoWrite 任务描述中存在；用户追问时 Read 文件而不复述路径

## Pricing 缺失策略

调用某 backend 时如果 `pricing.yaml` 没记该 backend 的某 endpoint 单价：

1. `lib/pricing.py` 返回 `(None, "unknown")`
2. `usage.jsonl` 写入 `cost_estimate_usd: null, pricing_source: "unknown"`
3. `finalize_usage.py` 聚合时把 `null` 跳过（不计入总和），并在 `usage-summary.md` 末尾追加一段「⚠️ 以下调用的单价未知，未计入总成本：`<list>`」
4. `runs.jsonl` 的 `pricing_completeness` 字段标 `partial` 或 `none`

主 agent 在最终一行总览里 SHOULD 加标记：

```
📊 本次估算 ~$0.023 USD（23 次调用 · 单价完整）
📊 本次估算 ≥$0.020 USD（23 次调用 · 3 次单价未知，估算偏低）
```

## 配置文件格式

`pricing.yaml` 与 `routing.yaml`（init-search-crew）保持一致都用 YAML。理由：

- YAML 对人类编辑（备份偏好、改单价）远比 JSON 友好（支持注释、不需要满文件引号 / 逗号）
- 用户已经决定 `routing.yaml` 走 YAML，pricing 没必要单独走 JSON 制造不一致
- 解析方案在 TECH.md T-USAGE-006 备选三方案中选一种实现期决策（倾向 vendor 极简 YAML subset parser）

## 未来扩展接口预留

虽然首版不实现，但 jsonl schema 与 `usage.py` 接口要留好扩展点：

- `calls.jsonl` schema：所有可选字段（`tokens_or_units`、`pricing_source`）允许为 null，未来加新字段不打破老数据
- `runs.jsonl` 的 `totals` 用 dict 结构，未来加新维度（如 `by_session_type`）不冲突
- `usage.py` 用 subcommand 风格的 argparse 结构，新增功能（如 `--alert`）作为新子命令叠加

## Context 卫生测试

实现时验证：

1. 跑一次完整 deep-search，断言主 agent 最终回复只有**一行** cost 总览（grep `📊 本次估算`）
2. 不能出现 `/tmp/search-crew/` 路径出现在主 agent 回复
3. 用户接着说"看明细"，主 agent Read summary 文件后呈现，但还是不该把原始 jsonl 全文贴出来
