## 1. AI 综述 backend 基础设施

- [x] 1.1 新增 `skills/search-toolkit/scripts/lib/backends/ai_common.py`：统一返回结构 `{backend, summary, citations[], results[]}` + citations → results 派生函数
- [x] 1.2 新增 `lib/backends/ai_grok.py`：xAI `chat/completions` + `search_parameters: {mode: "on", return_citations: true}`，解析顶层 `citations[]`
- [x] 1.3 新增 `lib/backends/ai_doubao.py`：火山方舟 `chat/completions` + `tools: [{type: "web_search"}]`，model 取 `ARK_MODEL_ID`（默认 `doubao-1-5-pro-32k-search`），解析 `annotations[].url_citation`
- [x] 1.4 新增 `lib/backends/ai_gemini.py`：Gemini `generateContent` + `tools: [{google_search: {}}]`，model 取 `GEMINI_MODEL_ID`（默认 `gemini-2.5-flash`），解析 `candidates[].grounding_metadata.grounding_chunks[].web.uri`
- [x] 1.5 三个 backend 顶部注释贴文档链接 + 最后验证日期；返回结构异常时 raise `BackendError`

## 2. 站点调用上限（_http.py 计数器）

- [x] 2.1 `lib/_http.py` 增模块级 `_call_counter: dict[tuple[str, str], int]`
- [x] 2.2 `request_json` / `request_text` 入口先取 `run_id`（环境变量 `SEARCH_CREW_RUN_ID`，缺省回落 PID）；查 `(run_id, site)` 计数
- [x] 2.3 达到上限直接 raise `BackendError(retryable=False, reason="call_cap_exceeded")`，**不发出**真实请求
- [x] 2.4 HTTP 429 / 5xx 内部 retry 不重复计数；只有调用方主动重发才增计数（_http.py 本身无 retry，每次 request_json 增计数一次）
- [x] 2.5 上限从 `~/.config/search-crew/limits.yaml` 读 `call_cap.ai_backend` / `call_cap.non_ai_backend`，默认 1 / 2
- [x] 2.6 `defaults/limits.yaml` 补 `call_cap:` 段（AI 1、非 AI 2）
- [x] 2.7 主 agent 派 subagent 时可通过 `SEARCH_CREW_RUN_ID` 让 subagent 共享调用上限计数器（更新 `agents/deep-search.md` 派发约定段；fast/site-search 不派下级，无需改）

## 3. ROUTING AI 综述层

- [x] 3.1 `defaults/routing.yaml` 增 `ai_summary:` 顶层段（`enabled: true` / `selection_order: [grok, doubao, gemini]` / `fallback_on_no_key: jina`）
- [x] 3.2 `skills/search-toolkit/ROUTING.md` 新增「AI 综述层」章节：描述触发条件（query 未命中硬规则 + AI key 已配）、三家选源逻辑（语言 / 语境）、与硬规则的优先级关系
- [x] 3.3 search.py 内增 `_pick_ai_backend()` 函数（按 selection_order + 可用 key 选一家）
- [x] 3.4 `search.py` 增 `--prefer ai|jina|serper` 与 `--ai-backend grok|doubao|gemini` 选项
- [x] 3.5 三家 AI key 均缺失时 search.py prefer=ai 自动回落 jina；与现有 `WEBSEARCH_FALLBACK` 机制兼容

## 4. usage-summary 搜索摘要段

- [x] 4.1 `lib/usage.py:record(...)` 记录 query 字段；落 calls.jsonl 时含 query
- [x] 4.2 `scripts/finalize_usage.py` 聚合时按 `(site, [queries])` 分组；生成 `## 搜索摘要` 段追加到 `<run_root>/usage-summary.md` 末尾
- [x] 4.3 被站点调用上限拦下的尝试单独写一行 `已跳过：<site>，原因：触发站点调用上限`
- [x] 4.4 `_http.py` 在 raise `call_cap_exceeded` 前也 record 一条 `status: "call_cap_exceeded"` 到 calls.jsonl

## 5. usage.py CLI 扩展

- [x] 5.1 `scripts/usage.py` 新增 `--show-queries` flag：输出最近 N 次 run 的「搜索摘要」段
- [x] 5.2 `--show-queries` 与现有 `--last N` 配合（取 N 次 run）；help 文本说明
- [x] 5.3 `usage.py --last 1 --show-queries` 输出端到端可读（端到端冒烟通过）

## 6. 主 agent cost 一行格式扩展

- [x] 6.1 `commands/deep-search.md` 的 cost 总览段说明从「N 次调用」改为「N 次调用 · M 个源 · K 次触发站点调用上限」（K=0 时省略 K 段）
- [x] 6.2 `agents/{fast,site,deep}-search.md` 主 agent 闭环说明同步该格式
- [x] 6.3 `finalize_usage.py` 增 `--one-line` 输出模式：从 usage-summary 派生「N 个源 · K 次触发上限」两个数字，方便主 agent 拿到现成字符串拼回复

## 7. agent description 反例段

- [x] 7.1 `agents/fast-search.md` 增「## 不要触发本 agent 的场景」段，至少 5 条反例
- [x] 7.2 `agents/site-search.md` 增同名反例段，至少 4 条
- [x] 7.3 `agents/deep-search.md` 增同名反例段，至少 4 条

## 8. SKILL.md 调整

- [x] 8.1 `skills/search-toolkit/SKILL.md` 顶部加「backend 是当前实现，不是身份」声明段
- [x] 8.2 `skills/browser-control/SKILL.md` 顶部加同样声明段
- [x] 8.3 `skills/search-toolkit/SKILL.md` 新增「site-search 强制预检」子节，写明 `--list-adapters` checklist
- [x] 8.4 `skills/browser-control/SKILL.md` 「错误处理」段改为六分类表（网络不可达 / 需要登录 / iframe / 反爬 / 403 / MCP 断连），每行配主 agent 下一步建议

## 9. 配置 / 环境变量 / 文档同步

- [x] 9.1 `.env.example` 增三个 key：`XAI_API_KEY` / `ARK_API_KEY` + `ARK_MODEL_ID` / `GEMINI_API_KEY` + `GEMINI_MODEL_ID`，每行注释「可选，未配自动回落」
- [x] 9.2 `defaults/limits.yaml` 补 `call_cap:` 段（见 2.6）
- [x] 9.3 `defaults/routing.yaml` 增 `ai_summary:` 段（见 3.1）
- [x] 9.4 `defaults/pricing.yaml` 占位三家 backend 的 `null` 单价（保留 `pricing_source: "unknown"`，配合 usage-summary 末尾的警告）
- [x] 9.5 `EXTENDING.md` 新增「AI 综述 backend」章节：三家 API 文档链接、如何关闭 AI 综述层（routing.yaml）、如何加第四家
- [x] 9.6 `README.md` 安装段提到三家 AI key 可选；触发方式段说明 AI 综述层
- [x] 9.7 `commands/setup.md` / `scripts/check_backends.py` 在输出末尾追加「缺失的可选 AI key 提示」段
- [x] 9.8 `scripts/seed_user_config.py` 增 `--merge` 子模式：检测 active routing.yaml 缺 `ai_summary` 段时主动 merge 进去（不破坏用户已改字段）

## 10. 测试与验证

- [x] 10.1 `tests/` 增 `test_call_cap.py`：mock `_http.py` 验证 AI 上限 1 次 / 非 AI 上限 2 次 / HTTP 429 retry 不重复计数 / 跨 run 不互通
- [x] 10.2 `tests/` 增 `test_ai_backends.py`：mock 三家 HTTP 响应，验证 `{summary, citations}` 解析正确
- [x] 10.3 `tests/` 增 `test_finalize_usage_summary.py`：验证 usage-summary.md 末尾「搜索摘要」段格式 + 已跳过记录
- [ ] 10.4 **manual** · 端到端冒烟：本地配齐三家 key，跑一次 `/deep-search 调研 2026 主流开源 LLM 推理框架`，验证 traces 含 AI 综述记录 + usage-summary 含搜索摘要段 + cost 一行带「M 个源 · K 次触发上限」
- [ ] 10.5 **manual** · 零 key 冒烟：清空 AI key，跑一次 fast-search，验证自动回落 jina（与现有 WEBSEARCH_FALLBACK 一致）

## 11. spec / 归档准备

- [x] 11.1 `openspec validate borrow-smart-search-web-reader --strict` 通过
- [x] 11.2 实施期发现的 spec 偏差同步更新到 `openspec/changes/borrow-smart-search-web-reader/specs/<capability>/spec.md`（ai-derived 块可直接改；触及 locked 须停下来单独提请用户）
- [ ] 11.3 **manual** · 实施完成后跑 `openspec archive borrow-smart-search-web-reader` 把 delta 合并到主 `openspec/specs/`
