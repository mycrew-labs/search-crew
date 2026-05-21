# TECH delta · add-usage-tracking

> 本文件为 change `add-usage-tracking` 的 TECH delta。归档后并入 `openspec/TECH.md`（项目根）。
>
> 依赖 `init-search-crew` 已确定的 TECH 决策（T-BACKEND-001 / T-RUNTIME-001 / T-CONFIG-001 / T-SEED-001 / T-OUTPUT-001 / T-SESSION-001）。

## 技术决策台账

| 编号 | 描述 | 服务于 |
|---|---|---|
| T-USAGE-001 | 打点埋点位置：统一在 `lib/_http.py` 出口拦截 | P-USAGE-001 |
| T-USAGE-002 | `usage.jsonl` / `calls.jsonl` / `runs.jsonl` 三层 schema 与原子追加 | P-USAGE-001 / P-USAGE-002 |
| T-USAGE-003 | `usage-summary.md` 生成时机：subagent 自身结束 + run 整体结束 | P-USAGE-001 |
| T-USAGE-004 | 主 agent 路径推导：固定 `/tmp/search-crew/<session_id>/usage-summary.md` | P-USAGE-001 |
| T-USAGE-005 | 状态目录 `~/.local/state/search-crew/` 解析（XDG_STATE_HOME 优先） | P-USAGE-002 |
| T-USAGE-006 | `pricing.yaml` 加载 + 单价缺失策略 | P-USAGE-003 |
| T-USAGE-007 | `usage.py` CLI 契约 + 不进 context 的呈现保证 | P-USAGE-004 |

---

## T-USAGE-001 ：打点埋点位置（统一在 `_http.py` 出口）

- 所有 backend 调用都经过 `skills/search-toolkit/scripts/lib/_http.py` 的 `request_json` / `request_text`
- 在这两个函数返回前**统一**写打点（成功、失败、超时各一次）
- 不在每个 backend 模块里散点埋——避免遗漏 + 保证 schema 一致
- `lib/jina.py` / `lib/serper.py` / `lib/sites/*.py` 调 `_http` 时传 `backend` 与 `endpoint` 标签，`_http` 拼装记录

新增 `lib/usage.py`：

```python
def record(*, backend: str, endpoint: str, status: int | str,
           latency_ms: int, tokens_or_units: int | None,
           run_root: pathlib.Path, subagent: str) -> None:
    """统一写打点。同时追加到 run 临时 jsonl 与全局永久 calls.jsonl。"""
```

`_http.py` 调用上面这个函数；不允许任何业务代码绕过它自行写 jsonl。

## T-USAGE-002 ：三层 jsonl Schema

### 单调用粒度

`<run_root>/usage.jsonl` 与 `~/.local/state/search-crew/calls.jsonl` 共享 schema：

```json
{
  "ts": "2026-05-21T10:30:15.123Z",
  "run_id": "<session_id>",
  "subagent": "fast-search",
  "backend": "jina",
  "endpoint": "search",
  "status": 200,
  "latency_ms": 842,
  "tokens_or_units": 1,
  "cost_estimate_usd": 0.0015,
  "pricing_source": "active"
}
```

`pricing_source` 取值：`active` / `default` / `unknown`（`unknown` 时 `cost_estimate_usd = null`）。

### Run 汇总粒度

`~/.local/state/search-crew/runs.jsonl`：

```json
{
  "run_id": "<session_id>",
  "started_at": "2026-05-21T10:28:00Z",
  "ended_at": "2026-05-21T10:32:11Z",
  "totals": {
    "calls": 23,
    "cost_estimate_usd": 0.023,
    "by_backend": {"jina": {"calls": 20, "cost": 0.020}, "serper": {"calls": 3, "cost": 0.003}},
    "by_subagent": {"fast-search": {"calls": 14, "cost": 0.014}, "site-search": {"calls": 6, "cost": 0.006}, "deep-search": {"calls": 3, "cost": 0.003}}
  },
  "pricing_completeness": "full"
}
```

`pricing_completeness` 取值：`full` / `partial` / `none`（partial 与 none 时摘要必须显式标注「单价未知项已被忽略」）。

### 原子追加

- 用 `open(path, "a")` + 一行 JSON + `\n` 模式追加
- 多进程并发追加用 `fcntl.flock(LOCK_EX)` 串行化（POSIX）
- 写失败不抛出阻塞业务：stderr 警告 + 继续；usage 缺失视为可容忍降级

## T-USAGE-003 ：summary 生成时机

- **subagent 自身结束**：subagent 在写自己的 `INDEX.md` 之后，**额外**写一份 `<run_root>/<subagent>/usage-summary.md`，仅含本 subagent 切片
- **run 整体结束**：由谁触发？
    - 主 agent 派完所有 subagent、收完所有产物时调 `python3 scripts/finalize_usage.py <run_root>`
    - `finalize_usage.py`：读 `<run_root>/usage.jsonl` → 生成 `<run_root>/usage-summary.md` + 追加 run 级行到 `~/.local/state/search-crew/runs.jsonl`
- 主 agent 在 prompt 中硬约定：最终回复**之前**必须跑 `finalize_usage.py`，否则视为未完成

## T-USAGE-004 ：主 agent 路径推导

主 agent 已经从 `get_session_id()` 拿到 `<session_id>`（与产物根目录共用）。

- run_root = `/tmp/search-crew/<session_id>/`
- summary 文件 = `<run_root>/usage-summary.md`

主 agent prompt 中明确写明该约定（指令性，不依赖运行期注入），用户追问"看明细"时主 agent 直接拼路径 Read 即可。

## T-USAGE-005 ：状态目录解析

`~/.local/state/search-crew/` 实际路径：

```python
def state_dir() -> pathlib.Path:
    base = os.environ.get("XDG_STATE_HOME") or "~/.local/state"
    return pathlib.Path(base).expanduser() / "search-crew"
```

首次写入前 `mkdir(parents=True, exist_ok=True)`。

## T-USAGE-006 ：单价加载 + 缺失策略

`lib/pricing.py`：

```python
def estimate(backend: str, endpoint: str, tokens_or_units: int | None) -> tuple[float | None, str]:
    """返回 (cost_estimate_usd, pricing_source)。"""
    # 1. 读 ~/.config/search-crew/pricing.yaml
    # 2. 找不到对应 backend/endpoint → 兜底找 plugin defaults/pricing.yaml
    # 3. 都没有 → 返回 (None, "unknown")
```

`pricing.yaml` 与 `routing.yaml` 都用 YAML（用户决策：YAML 对人类更友好，配置文件值得这点解析成本）。

YAML 解析方案（实现期决策，三选一）：

1. **vendor 极简 YAML subset parser**（推荐）：放 `skills/search-toolkit/scripts/lib/_yaml.py`，只支持本 plugin 实际用到的子集（map / list / 字符串 / 数字 / 注释），约 200 行。零外部依赖
2. **要求 PyYAML**：on-install 时检测 `pip install --user pyyaml`；用户体验有摩擦但功能完整
3. **vendor PyYAML 纯 python 实现**：拷一份到 plugin，绕过 pip 安装步骤

倾向 1：本 plugin 的配置结构非常扁平（路由起点表、单价表、limits），不需要 anchors / merge keys / 多文档等高级 YAML 特性。

routing.yaml 与 pricing.yaml 用同一个 `_yaml.py` 解析。

## T-USAGE-007 ：`usage.py` CLI 契约

`skills/search-toolkit/scripts/usage.py`：

| 参数 | 行为 |
|---|---|
| `--last N` | 列最近 N 次 run 的 totals（默认 N=10） |
| `--by-day` / `--by-week` / `--by-month` | 按时间段聚合 |
| `--by-backend` | 按 backend 聚合 |
| `--raw` | 直接 cat `calls.jsonl` |
| `--since YYYY-MM-DD` | 限定起始日期 |
| 无参数 | 默认 `--last 10` |

- 纯本地、无网络、不需要任何 API key
- 输出走 stdout（人类可读 markdown 或表格），错误走 stderr
- 默认 `LC_ALL` / `LANG` 取环境，输出中文优先

### Context 隔离保证

- `usage.py` **本身**不会被自动调用：plugin 不在任何 subagent prompt 里写「跑 usage.py」
- 主 agent 在用户追问"想看历史"时**只口头提示**用户跑 `! python3 ...`；不主动 `Bash` 它
- 主 agent prompt 中明确写：「绝不主动调 usage.py；它的输出是给用户终端看的，不需要进 context」

潜在反模式（实现时需要在 agent prompt 拦截）：

- ❌ 主 agent 自己跑 `Bash python3 usage.py` 然后把输出转述给用户 → 这会进 context
- ✅ 主 agent 提示用户「跑 `! python3 ...`」由用户自己执行

如未来 Claude Code 提供「执行命令但不进 context」的工具，再升级。
