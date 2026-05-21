# Capability: fast-search

一轮通用快速调研。搜索 + 抓取 + ranking + 摘要，无循环。

## 适用 P- 行为

- [P-AGENT-001](../../USER_DESIGN.md) 三个 subagent 共性 + 边界
- [P-DATA-001](../../USER_DESIGN.md) 产物目录与调用语义
- [P-OUTPUT-001](../../USER_DESIGN.md) wiki 索引、ranking、关键词清单、附件约定
- [P-ROUTE-001](../../USER_DESIGN.md) 循证四步（fast-search 也遵循；主要承担第一步「先在起点搜」和第二步「扩展」）
- [P-EVIDENCE-001](../../USER_DESIGN.md) 证据准备
- [P-FALLBACK-001](../../USER_DESIGN.md) 零 key fallback

## 行为描述

### 输入

- 上级（主 agent 或 deep-search）派发：query、可选 target 目录、可选 hint
- 模型：`claude-haiku-4-5-20251001`

### 工作流（一轮）

1. 用 `search.py` 跑通用搜索（Jina / Serper / fallback WebSearch）
2. 对返回结果按 ranking 排序，挑 top N（默认 5）
3. 对每条用 `fetch.py` 抓取 markdown
4. 把内容写入 `<run_root>/fast-search/fast-search-NNN.md`，头部加关键词；附件按 hash 写 `<run_root>/attachments/`
5. 生成 `<run_root>/fast-search/INDEX.md`（wiki 风格大纲）
6. 返回 `(目录路径, 一句话摘要)` 给上级

### 输出

- `fast-search/fast-search-NNN.md` × N：原始抓取内容 + 关键词头部 + evidence anchor
- `fast-search/INDEX.md`：wiki 大纲（子文件简介、ranking、推荐与否、关键词清单、Next-Read 推荐）
- `attachments/<hash>.<ext>`：附件去重

## 不变量

- 不做站内精确搜索（那是 site-search 的活）
- 不做多轮挖掘（那是 deep-search 的活）
- 必须落 wiki INDEX.md，不允许只丢 markdown 走
- ranking + 关键词清单是处理内容时**当下**就要完成，不可延后补
