# Fast Search

一轮通用快速调研。搜索 + 抓取 + ranking + 摘要，不循环。被主 agent 或 deep-search 派发，每次处理一个子主题。

## Purpose

把"找几个相关 URL 看看说了什么"这类轻量任务从主对话隔离出去，避免污染 context；同时保证产物结构化（关键词 + ranking + INDEX）让上层快速消化。

## Requirements

### Requirement: fast-search 不做站内精确搜索，不做多轮调研
fast-search subagent SHALL 只跑**一轮**通用搜索 + 抓取 + 摘要。MUST NOT 做站内精确搜索（该交给 site-search）。MUST NOT 做多轮跨主题挖掘（该交给 deep-search）。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 接到任务后只跑一轮
- **WHEN** fast-search 收到 query
- **THEN** 跑一次搜索 + 抓 top N + 写盘 + 返回；不发起第二轮搜索

#### Scenario: 命中权威主题时返回信号给上级
- **WHEN** fast-search 发现 query 主题应该走 site-search（如临床 / 专利 / 官方文档）
- **THEN** 返回信号给上级，请上级派 site-search，不自己强行做

### Requirement: fast-search 产出 ranking + 摘要 + 关键词
fast-search MUST 在产物中给每条结果打 ranking 分数（0-10）+ 推荐等级（must-read / should-read / skip-able）+ 关键词清单。这三件事 MUST 在抓取阶段**当下**完成，不允许「先全抓回来后续再补」。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 单 markdown 头部含关键词
- **WHEN** fast-search 写 `fast-search-001.md`
- **THEN** 文件头部 YAML front-matter 含 `url` / `ranking` / `recommended` / `keywords` 四个字段

#### Scenario: INDEX 按 ranking 排序
- **WHEN** fast-search 写 `INDEX.md`
- **THEN** 子文件列表按 ranking 降序，且每条含简介 + 推荐等级 + 关键词子集

### Requirement: fast-search 在零 key 时 fallback 到 WebSearch
fast-search 在 `search.py` 返回 `WEBSEARCH_FALLBACK` 时 MUST 改用 Claude Code 内置 WebSearch；在 `fetch.py` 返回 `WEBFETCH_FALLBACK` 时 MUST 改用 WebFetch。整个流程在零 key 状态下仍能完成。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 零 key fallback
- **WHEN** 环境变量 `JINA_API_KEY` 与 `SERPER_API_KEY` 均未设置
- **THEN** fast-search 调 `search.py` 后收到 `WEBSEARCH_FALLBACK` marker，转而调用 WebSearch 完成检索

### Requirement: fast-search 产物文件以 subagent 名字为前缀
所有 fast-search 落盘的文件 / 子目录 MUST 以 `fast-search` 为前缀（`fast-search-NNN.md` / `fast-search/`）。混合命名（如 `results-1.md`）禁止。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-21

#### Scenario: 落盘命名
- **WHEN** fast-search 抓回三个结果
- **THEN** 文件名形如 `fast-search-001.md`、`fast-search-002.md`、`fast-search-003.md`，全部以 `fast-search-` 开头
