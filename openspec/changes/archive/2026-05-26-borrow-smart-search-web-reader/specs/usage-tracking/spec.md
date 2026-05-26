## ADDED Requirements

### Requirement: usage-summary.md 末尾追加「搜索摘要」段
`finalize_usage.py` 在生成 `<run_root>/usage-summary.md` 时 MUST 在文件末尾追加 `## 搜索摘要` 段，每行格式 `网站：<site> | 查询词：<term1>；<term2> | 次数：<n>`。被站点调用上限拦下的调用 MUST 单独写一行 `已跳过：<site>，原因：触发站点调用上限`。该段 MUST 含本次 run 所有真实发出的调用，含被拦下的尝试。搜索摘要 MUST 只写进 usage-summary.md（与 CLI `--show-queries`），MUST NOT 要求主 agent 把这段贴进给用户的最终回复（保留「仅一行 cost 总览」的克制设计）。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-26

#### Scenario: 一次完整调研
- **WHEN** 主 agent 跑完调研并调用 `finalize_usage.py <run_root>`
- **THEN** `<run_root>/usage-summary.md` 末尾存在 `## 搜索摘要` 段，每条调用 / 跳过一行

#### Scenario: 用户 CLI 看摘要
- **WHEN** 用户跑 `! python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/usage.py --last 1 --show-queries`
- **THEN** CLI 输出含最近一次 run 的「搜索摘要」段；输出不进入 agent context

### Requirement: 站点调用上限：同 run 同站点调用次数硬限
`lib/_http.py` 出口 MUST 维护一份进程内 `{(run_id, site): count}` 计数器；任何请求发出前 MUST 先查计数；达到上限的请求 MUST NOT 真正发出，MUST 由 `_http.py` 直接 raise `BackendError(retryable=False, reason="call_cap_exceeded")` 由上层捕获并落 fallback marker。上限值 MUST 可由 `~/.config/search-crew/limits.yaml` 的 `call_cap.ai_backend` / `call_cap.non_ai_backend` 覆盖，默认 AI backend 1 次、非 AI backend 2 次。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-26

#### Scenario: AI backend 默认 1 次
- **WHEN** 同 run 内对 grok 已成功调用 1 次后再次发起
- **THEN** 第 2 次请求被 `_http.py` 拦下，不真正发出 HTTP；调用方收到 `call_cap_exceeded` 错误

#### Scenario: 非 AI backend 默认 2 次
- **WHEN** 同 run 内对 jina-search 已调用 2 次后再次发起
- **THEN** 第 3 次请求被拦下

#### Scenario: 用户改 limits.yaml 覆盖默认
- **WHEN** 用户在 active `limits.yaml` 设 `call_cap.ai_backend: 2`
- **THEN** AI backend 同 run 上限变为 2 次，第 3 次才被拦

#### Scenario: HTTP 429 retry 不增计数
- **WHEN** `_http.py` 内部对一次请求做 retry（HTTP 429 / 5xx）
- **THEN** 整次调用只计 1 次，retry 不重复计数

#### Scenario: 跨 run 不互通
- **WHEN** run-A 结束后开始 run-B
- **THEN** run-B 的计数器为空，与 run-A 完全独立

### Requirement: 新增 AI backend 走统一 _http.py 出口与 usage 打点
新增的 grok / gemini / doubao backend MUST 通过 `lib/_http.py:request_json` 发请求，由 `_http.py` 自动调 `lib/usage.py:record(...)` 打点。MUST NOT 在 backend 模块内绕过 `_http.py` 自行 `urllib.request.urlopen`。

#### Scenario: grok backend 调用打点
- **WHEN** fast-search 调 `ai_grok.search(query)`
- **THEN** `~/.local/state/search-crew/calls.jsonl` 新增一条 `backend: "grok", endpoint: "responses"` 记录

#### Scenario: cost 缺失时 cost_estimate_usd 为 null
- **WHEN** 三家 AI backend 在 `pricing.yaml` 中无单价配置
- **THEN** 对应 jsonl 记录 `cost_estimate_usd: null`、`pricing_source: "unknown"`；usage-summary 末尾标「⚠️ grok / gemini / doubao 单价未知，未计入合计」
