# Capability: usage-tracking

API 调用次数与估算成本的打点、汇总、永久持久化、独立查询。

## 适用 P- 行为

- [P-USAGE-001](../../USER_DESIGN.md) 每次 run 必落 cost summary 文件；主 agent 回复只给一行总览
- [P-USAGE-002](../../USER_DESIGN.md) 原始打点 + run 汇总永久持久化（vibe-usage 风）
- [P-USAGE-003](../../USER_DESIGN.md) 单价表
- [P-USAGE-004](../../USER_DESIGN.md) 独立查询入口

## 行为描述

### 三层数据

1. **临时（per-run）**
    - `<run_root>/usage.jsonl`：每次 backend 调用一行
    - `<run_root>/<subagent>/usage-summary.md`：subagent 切片摘要
    - `<run_root>/usage-summary.md`：run 整体摘要
2. **永久（cross-run）**
    - `~/.local/state/search-crew/calls.jsonl`：与 per-run 同 schema 的全量打点
    - `~/.local/state/search-crew/runs.jsonl`：每次 run 一行汇总
3. **配置**
    - `~/.config/search-crew/pricing.yaml`：用户态单价表（首次安装从 plugin defaults 拷贝）

### 打点路径

```
backend HTTP 请求 (jina / serper / sites/*.py)
    ↓
lib/_http.py  ← 统一出口，调 lib/usage.py:record(...)
    ↓
写 <run_root>/usage.jsonl + 写 ~/.local/state/search-crew/calls.jsonl
```

业务代码**不允许**绕过 `_http.py` 自行写打点。

### 摘要生成

- subagent 结束前调 `python3 finalize_usage.py --subagent <name> <run_root>` → 生成切片
- 主 agent 在最终回复前调 `python3 finalize_usage.py <run_root>` → 生成全局 + 追加 `runs.jsonl`

### 主 agent 行为约束

- 最终回复**只追加一行**：`📊 本次估算 ~$X.XXX USD（N 次调用 · <pricing_status>）`
- **不**附路径
- 用户追问明细 → Read `<run_root>/usage-summary.md` 后展示（run_root 由 subagent 派发时返回，主 agent 自己记得）
- 用户追问历史 → 提示 `! python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/usage.py --last N`，**不**主动调

### 独立查询

`scripts/usage.py` 是 standalone CLI（vibe-usage 模式）：

- 用户用 `!` 前缀执行；输出落用户终端、不进任何 agent context
- 纯本地、无网络、不需要 API key
- 子参数：`--last N` / `--by-day` / `--by-week` / `--by-month` / `--by-backend` / `--since` / `--raw`

### 单价缺失策略

- 调用某 backend / endpoint 时 `pricing.yaml` 无对应单价 → `cost_estimate_usd = null`, `pricing_source = "unknown"`
- `finalize_usage.py` 聚合时跳过 null 项，并在 summary 末尾标注「⚠️ 以下调用单价未知，未计入合计：...」
- 主 agent 一行总览中 status 字段反映：`单价完整` / `部分缺失` / `全部未知`

## 不变量

- 每次 run **必须**产出 `usage.jsonl` + `usage-summary.md`；缺失视为缺陷
- raw 打点数据 **永不**自动清理（永久持久化承诺）
- 主 agent 回复 **不**含 `/tmp/search-crew/` 字符串（context 卫生）
- `usage.py` **永不**被 agent 自动调用，必须由用户主动 `!` 触发
- cost 标识必须含「估算」字样，不得伪装为精确账单
- 业务代码**不允许**绕过 `lib/_http.py` 自行写打点
