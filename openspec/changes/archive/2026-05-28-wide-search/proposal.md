## Why

deep-search 求**深**（一个题、多轮挖掘）。但有一类需求是求**广**：对 N 个**同类对象**跑**同一套分析**，汇成对照矩阵——如「对比这 15 个开源推理框架的 性能/许可证/活跃度/部署难度」「调研这 20 家供应商的 价格/SLA/集成方式」。

参考 Manus Wide Research：单 agent 顺序处理 N 项会**context 退化**（第 1 项详尽、第 20 项潦草）；给**每个对象一个独立 context 的 worker 并行**，则第 N 项和第 1 项分析深度一致。这正好补上 Search Crew 缺的「广度并行 + 结构化对照」能力。

## What Changes

- **新增 `wide-search` subagent**（lead 角色）：把请求拆成「对象清单 + 统一分析 schema（列）」→ 同 turn 并行派 worker（每对象一个）→ 每 worker 独立 context 研究一个对象、按 schema 填一行（含每格的源 URL）→ lead 汇成**对照矩阵**（report.md 表格 + report.html 可排序 + traces 保留每行证据）。
- **worker 复用现有 fast/site-search**（已是 haiku/sonnet 档），**不新建 worker subagent**——wide 派很多 worker，复用 fast-search（haiku，便宜）天然压成本；个别对象需官方源精确查时派 site-search。
- **`wide-search` lead 用中等模型**（sonnet）：只负责定 schema + 派发 + 汇总，不需要旗舰。
- **硬上限 `wide_search.max_items`**（`limits.yaml`，建议默认 12）：超过则分批或要求用户收窄——防 N 个 worker 爆 token / 撞 Task 并发上限（Manus 敢 100+ 是因为每个跑独立 VM；我们派的是 Claude subagent，成本 ~15×）。
- **新增 `/search-wide` slash command**（命名空间 `/search-crew:search-wide`，沿用 search-* 体系）：显式触发；或对话语义识别「批量对比/分析 N 个同类对象」时主 agent 自动派。
- **新增 `/search-fast` slash command**（命名空间 `/search-crew:search-fast`）：把原本只能语义自动触发的 fast-search 也暴露为显式命令，让用户能主动发起一次通用快速调研（语义自动触发的老路径保留）。
- **schema 开跑前确认**：列（分析维度）派发前跟用户对一下（错一次会 ×N 倍亏）。

## Capabilities

### New Capabilities

- `wide-search`：对 N 个同类对象并行跑同一套分析、汇成对照矩阵的广度调研能力。worker 复用 fast/site-search；硬上限 max_items；循证不打折（每格可回溯源）；产物为矩阵（md 表格 + html 可排序 + traces）。

### Modified Capabilities

- `orchestration`：主 agent 路由新增「批量对比/分析 N 个同类对象 → 派 wide-search」分支；`/search-wide` 与 `/search-fast` 成为新的显式搜索 slash 命令（与 `/search-deep` 并列）——注意这与 orchestration 现有 locked 需求「唯一显式搜索 slash command 是 /search-deep」**冲突**，需 MODIFY 那条 locked（措辞从「唯一」改为「显式搜索命令有 /search-deep、/search-wide、/search-fast 三个」），归档前按锁确认 gate 提请用户确认。

## Impact

- **代码/产物**：新增 `agents/wide-search.md`（lead prompt）+ `commands/search-wide.md` + `commands/search-fast.md`；`defaults/limits.yaml` 加 `wide_search.max_items`；矩阵报告复用 deep-search 的 report.md/html + traces 约定。worker 复用现有 fast/site-search，无需新脚本。
- **模型**：lead = sonnet（中等）；worker = fast-search(haiku) 为主、site-search(sonnet) 按需——成本压在 worker 廉价档。
- **locked 影响**：MODIFY orchestration「唯一显式搜索 slash command」那条（user-confirmed），措辞改为列出 /search-deep、/search-wide、/search-fast 三个，归档前确认。
- **成本**：N 个 worker 并行，max_items 上限是主要控本手段；haiku worker 进一步压。
- **向后兼容**：纯新增能力，不改 deep-search / fast-search / site-search 现有行为。
