# Design — borrow-smart-search-web-reader

## Context

外部两个 skill（`~/Documents/Config/skills/smart-search` 与 `~/Documents/Config/skills/web-reader`）已在用户日常调用中稳定使用。本次借鉴其策略层的同时，新接 grok / doubao / gemini 三家「AI 综述 + 引用源」一体化接口，作为 Search Crew ROUTING 起点表中「先建立假设」的入口层。

现状关键约束：

- `T-HTTP-001`：所有 HTTP 出口走 `lib/_http.py`，自动调 `lib/usage.py:record(...)` 打点。新增 backend 必须遵守。
- `T-STDLIB-001`：Python 脚本零第三方依赖。三家 AI API 必须用 stdlib `urllib` 直连，不引 `openai-python` / `google-genai` SDK。
- `I-FALLBACK-001`：零 key 状态下整条链路仍可用（回落 WebSearch / WebFetch）。新增 AI backend 也必须遵守此回落原则。
- `I-CONFIG-001`：`defaults/` → `~/.config/search-crew/` 单向拷贝，用户态可改 routing.yaml 但 plugin 升级不动 active。

## Goals / Non-Goals

**Goals:**

- 引入三家 AI 综述 backend，统一返回 `{summary, citations[], results[]}` 结构，与现有 jina/serper 共存
- ROUTING 起点表增加「AI 综述层」分类，覆盖通用调研 / 概念入门 / 中英文热点四个场景
- 「搜索摘要」段成为 cost summary 的固定子段，主 agent 最终回复同步携带
- 强制预检 / 触发反例 / 失败分类三处文字约定落到对应 SKILL.md 与 agent description
- 运行时频次台账：同 run 内同站点调用硬上限，AI 1 次 / 非 AI 2 次

**Non-Goals:**

- 不实现 autoresearch 式适配器自动优化（属于 B-004，后续 change）
- 不接入第四家 AI 源（Claude / GPT-4 / 文心等），未来另起 change
- 不重构现有 jina/serper 调用路径，AI backend 是**新增**而非替换
- 不改 `~/.config/search-crew/` 的迁移策略；新增 routing 段进 defaults，用户 merge 由 setup 命令引导

## Decisions

### D-1 三家 AI API 选型与契约对齐

> **实测修正（2026-05-23）**：原计划三家都用 `chat/completions` + `search_parameters` / `tools`。
> 实际联调发现：(1) xAI 旧 Live Search（`search_parameters`）已于 2026-01-12 废弃（HTTP 410），
> 改用 **Agent Tools API**（`/v1/responses` + `tools:[{type:web_search}]`）；(2) 火山方舟的联网搜索
> 也在 **Responses API**（`/api/v3/responses`）不在 chat/completions，且 backend 命名 `doubao`（沿用品牌名）
> （方舟托管 Doubao/DeepSeek/Kimi 多家，名实相符）。grok 与 ark 的 Responses API 响应结构一致，
> 共用 `ai_common.parse_responses_api`。下表已更新为实际形态。

| 厂商 | endpoint | 触发搜索的字段 | 返回引用源字段 |
|---|---|---|---|
| xAI Grok | `POST https://api.x.ai/v1/responses` | `tools: [{type: "web_search"}, {type: "x_search"}]` | `output[]` 中 type=message 项的 `content[].annotations[]`（type=url_citation） |
| 火山方舟 doubao | `POST https://ark.cn-beijing.volces.com/api/v3/responses` | `tools: [{type: "web_search"}]`（model 填 API id 如 `doubao-seed-2-0-pro-260215`） | 同 grok（Responses API 结构一致） |
| Google Gemini | `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` | `tools: [{google_search: {}}]` | `candidates[].groundingMetadata.groundingChunks[].web.uri` |

**对齐策略**：在 `lib/backends/ai_common.py` 定义统一返回结构 + 共享 Responses API 解析器：

```python
{
  "backend": "grok" | "gemini" | "doubao",
  "summary": str,          # AI 综述正文
  "citations": [           # 引用源
    {"url": str, "title": str, "snippet": str}
  ],
  "results": [...]         # 兼容 jina/serper 的 schema，从 citations 派生
}
```

三个 backend 各自的请求构造 + 响应解析隔离在 `ai_grok.py` / `ai_gemini.py` / `ai_doubao.py`；grok 与 ark 共用 `ai_common.parse_responses_api`，gemini 单独解析 grounding。

**为什么不用各家 SDK**：违反 `T-STDLIB-001`；三家请求/响应都是普通 JSON，`urllib` 足够；少一层依赖少一个升级负担。

### D-2 ROUTING 起点表的 AI 综述层位置

在 `defaults/routing.yaml` 新增 `ai_summary:` 顶层段：

```yaml
ai_summary:
  # 用户没指定站点 / 主题是综述类 / 概念入门 / 热点时，优先派 AI 综述
  triggers:
    - "通用调研"
    - "概念入门"
    - "中文热点"     # → doubao 优先
    - "英文舆论"     # → grok 优先
    - "全球综述"     # → gemini 优先
  selection_order: [grok, doubao, gemini]
  fallback_on_no_key: jina   # AI key 都没配 → 退回 jina
```

**为什么 selection_order 不动态**：保持 SKILL.md 与 routing.yaml 双源可读；用户改 yaml 即可改优先级，不需要动代码。语言/语境的细化判断由 subagent 在 prompt 里完成，不下放到 yaml 表达。

**与 ROUTING 硬规则的关系**：硬规则（临床研究 / 专利 / 官方文档）**优先级高于** AI 综述层。AI 综述仅在 query 未命中任何硬规则时启用。

### D-3 站点调用上限：进程内 vs 持久化

**决定**：进程内（`lib/_http.py` 模块级 dict），不持久化。同一 subagent run 结束即释放。

**替代方案**：写到 `~/.config/search-crew/usage/<run_id>/call-cap.json` 持久化。

**为什么选进程内**：

- 站点调用上限目的是「防同 run 反复追打」，不是跨 run 学习
- 持久化版本需要锁 + 清理策略，复杂度不值
- 跨 run 的趋势分析由现有 `usage.py` CLI 覆盖

**数据结构**：

```python
# lib/_http.py
_call_counter = {}   # {(run_id, site): count}
# 调用 request_json 前先查计数，超限直接 raise BackendError(retryable=False, reason="call_cap_exceeded")
```

`run_id` 从环境变量 `SEARCH_CREW_RUN_ID` 取（主 agent 派 subagent 时注入；未注入时回落到进程 PID）。

**阈值**：AI backend 1 次，非 AI backend 2 次。可在 `~/.config/search-crew/limits.yaml` 覆盖（与 `site_search.browser_step_timeout_sec` 同层）。

### D-4 搜索摘要段位置：只写 usage-summary，不进主 agent 回复

**决定**：搜索摘要只追加到 `<run_root>/usage-summary.md` 末尾；**不**要求主 agent 把这段贴进给用户的最终回复。两条 locked requirement（orchestration / usage-tracking 的「主 agent 回复只追加一行 cost 总览」）一字不动。

`finalize_usage.py` 生成的固定格式：

```markdown
## 搜索摘要

- 网站：jina-search | 查询词：开源 LLM 推理框架 | 次数：1
- 网站：site-search:github.com | 查询词：vLLM；TensorRT-LLM | 次数：2
- 网站：grok | 查询词：开源 LLM 推理框架对比 2026 | 次数：1
- 已跳过：ark，原因：触发站点调用上限
```

**为什么不进主 agent 回复**（与最初 proposal 不同的取舍）：

- Search Crew 现有循证已经两层覆盖：`report.md` 内的 traces 引用 + `usage-summary.md`
- deep-search 用户主要看 `report.html`，对话末尾的搜索台账边际价值低
- fast-search 单跑场景搜索次数本就少（1-2 次），摘要等于废话
- 「仅一行 cost 总览」是 user-confirmed 设计，能不破就别破

**小补丁（cost 一行扩展）**：现在那行 cost 总览扩成「带覆盖面数字」的形态，把过程信号压缩进同一行：

```
📊 本次估算 ~$0.043 USD（12 次调用 · 4 个源 · 2 次触发站点调用上限）
```

「N 个源」「N 次触发上限」两个数字让用户在主对话即可感知效率信号；想看完整摘要则跑 `! python3 .../usage.py` 或打开 `usage-summary.md`。这条算 cost 一行的格式微调，cost 一行的精确字数本就没锁死，属于 ai-derived 范围，不触发 MODIFY locked。

**用户访问搜索摘要的路径**：

1. `! python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/usage.py --last 1 --show-queries`（新增 `--show-queries` flag）
2. 直接打开 `<run_root>/usage-summary.md` 查看「搜索摘要」段

### D-5 触发边界反例的写法

参考 web-reader 的「不要因为以下情况使用本 skill」段。三个 agent description 各加一个 `## 不要触发本 agent 的场景` 段，例如：

- **fast-search**：不要因「单条事实查询」「已有 URL 只需 fetch」「需要站内精确搜索」触发
- **site-search**：不要因「无明确目标站点」「跨多站点综述」「读取已知 URL」触发
- **deep-search**：不要因「单轮够用」「无需循证链」「用户只问一句」触发

**为什么放在 description 里而非单独文件**：subagent 路由触发判断由主 agent 在派发前完成，description 是它唯一看到的「触发条件」字段。反例与正例同栏目，主 agent 读到即用。

### D-6 失败分类六类与对应建议

browser-control SKILL.md 的「错误处理」段从扁平列表改成分类表：

| 失败点 | 主 agent 下一步建议 |
|---|---|
| 网络不可达 | 检查代理 / 切到 AI 综述 backend |
| 需要登录 | 写到 `INDEX.md` 标 `needs_login: true`，停止本站，建议用户提供 cookies |
| 内容在 iframe | 尝试 frame switch；失败转 fetch.py + Jina Reader |
| 反爬拦截 | 跳过本站，回落同类专用源或 AI 综述 |
| 权限不足（403） | 标 `permission_denied`，跳过 |
| 工具不可用（MCP 断连） | 提示用户重启 Chrome MCP，临时回落到 fetch.py |

### D-7 `.env.example` 与 EXTENDING 同步范围

`.env.example` 新增三行 + 注释说明每行可选：

```bash
# AI 综述 backend（任意一个未配也行；都未配 → 回落 jina）
GROK_API_KEY=     # grok（xAI Agent Tools API）
DOUBAO_API_KEY=   # doubao（火山方舟，托管 Doubao/DeepSeek 等）
GEMINI_API_KEY=                       # gemini（Google Search Grounding）
```

`EXTENDING.md` 新增「AI 综述 backend」章节，覆盖：

- 三家 API 文档链接
- 如何在 routing.yaml 关闭 AI 综述层（设 `ai_summary.enabled: false`）
- 如何加第四家（在 `lib/backends/ai_<name>.py` 实现 + routing.yaml selection_order 追加）

## Risks / Trade-offs

- **三家 API 升级风险**：xAI / 火山方舟的 search_parameters 是相对较新的字段，可能改名。**缓解**：每个 backend 文件顶部注释贴文档链接 + 最后验证日期；返回结构改变时 raise `BackendError`，回落 jina。
- **AI 综述层与硬规则的边界判断**：subagent 自行判断 query 是否命中硬规则可能错判，导致临床研究类问题被路由到 grok。**缓解**：硬规则在 ROUTING.md 顶部，subagent 必读；prompt 里加「先看硬规则再看 AI 综述层」。
- **频次台账误伤合理 retry**：HTTP 429 自动 retry 时被计数器拦下。**缓解**：`request_json` 内部 retry 不增计数，只有调用方主动重发才增。
- **进程内计数器在 deep-search 多 subagent 并发场景下不共享**：每个 subagent 是独立 Python 进程，dict 不互通。**缓解**：本期接受这一限制；多 agent 并发本就少见，每个 subagent 自己的频次约束已够；未来若需要跨进程共享再升级到 `~/.cache/search-crew/frequency-<run_id>.json` + flock。
- **`.env.example` 与现有用户实际 .zshrc 不一致**：用户在 `~/.zshrc` 已有部分 key，新增 key 不会自动出现。**缓解**：在 `/setup` 命令的检查脚本 `check_backends.py` 输出末尾追加「缺失的可选 AI key」提示。

## Migration Plan

1. **代码落地**（不涉及破坏性改动）：先合并新增 `lib/backends/ai_*.py` + `_http.py` 频次台账，不动现有 jina/serper 路径。
2. **defaults/routing.yaml 增 ai_summary 段**：用户态 `~/.config/search-crew/routing.yaml` 不会被覆盖（plugin 升级单向），用户需手动 merge 或重跑 `/setup --reseed`。
3. **`/setup` 增 reseed 提示**：检测到 active routing.yaml 缺 `ai_summary` 段时提示用户运行 `python3 scripts/seed_user_config.py --merge`（新增子模式）。
4. **`.env.example` 更新**：用户参考新文件自行补 key 到 `~/.zshrc`。
5. **回滚策略**：用户态 routing.yaml 改 `ai_summary.enabled: false` 即关闭整层；plugin 端 revert 该 commit 即可还原代码。

## Open Questions

> **实测落定（2026-05-26）**：原 Open Question 关于「默认 model / model 用哪个环境变量」已被新决策取代——
> model 不在代码 hardcode、也不用环境变量，全部进 `routing.yaml ai_summary.models.<backend>.{fast,deep}`，
> 按 subagent 分层（fast-search→fast / deep-search→deep）。env 只保留 3 个 API key：
> `GROK_API_KEY` / `GEMINI_API_KEY` / `DOUBAO_API_KEY`。backend 用品牌名 grok / gemini / doubao。

- **cost 估算单价**：三家计费颗粒不同（grok 按 search 次数 + token；doubao 按 token；gemini grounding 按 1k requests）。本期先**只记录调用次数**，cost 字段填 `null`，后续 change（B-005-ext）补单价表后再填。
