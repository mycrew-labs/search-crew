## Context

deep-search 求**深**：一个题、多轮挖掘、循环判断。但「对 N 个**同类对象**跑**同一套分析**、汇成对照矩阵」这类**广度**需求，deep-search 的多轮规划层是错配的——它会把 N 个对象塞进一条循环里串行处理，导致 context 退化（第 1 项详尽、第 N 项潦草）。

参考 Manus Wide Research：给**每个对象一个独立 context 的 worker 并行**，第 N 项与第 1 项分析深度一致。Search Crew 已有 fast-search（haiku，便宜）/ site-search（sonnet，官方源精确）两档廉价 worker，可直接复用，无需新建 worker subagent。

本变更同时把原本只能语义自动触发的 fast-search 暴露为显式 `/search-fast` 命令——这与 wide-search 共用同一处 locked 需求（orchestration「唯一显式搜索 slash command」）的修改，故一并处理。

## Goals / Non-Goals

**Goals:**
- 新增 `wide-search` lead subagent：拆「对象清单 + 统一分析 schema（列）」→ 同 turn 并行派 worker（每对象一个）→ 汇成对照矩阵。
- worker 复用现有 fast/site-search，不新建 worker subagent，成本压在廉价档。
- 循证不打折：矩阵每格可回溯到源 URL（沿用 deep-search 的 traces 约定）。
- 硬上限 `wide_search.max_items` 防 N 个 worker 爆 token / 撞并发。
- schema（列）派发前与用户确认一次（错一次 ×N 倍亏）。
- 暴露 `/search-wide` 与 `/search-fast` 两个显式命令，与 `/search-deep` 并列。

**Non-Goals:**
- 不改 deep-search / fast-search / site-search 现有行为（纯新增 + 复用）。
- 不做 deep-search 那种多轮循环挖掘——wide-search 是「一对象一 worker、单轮并行」，深度由 worker 自己负责。
- 不为 worker 新建独立 VM / 沙箱（Manus 敢 100+ 是因每个跑独立 VM；我们派 Claude subagent，成本 ~15×，靠 max_items 控本）。

## Decisions

### D1：lead = sonnet，worker = fast-search(haiku) 为主、site-search(sonnet) 按需
lead 只负责定 schema + 派发 + 汇总，不需要旗舰模型，用 sonnet。worker 是真正干活的，但每个只研究一个对象、填一行，fast-search(haiku) 足够；个别对象需官方源精确查时派 site-search。成本结构：N 个 haiku worker + 1 个 sonnet lead，远低于 N 个 opus。

### D2：一对象一 worker，同 turn 并行派发
每个对象单独一个 worker、独立 context，避免 Manus 指出的 context 退化。MUST 在同一 message 里发起多个 Task 调用（沿用 deep-search 的「同 turn 并行」locked 约束）。

### D3：worker 任务契约四要素（复用 deep-search 模式）
派每个 worker 的 Task prompt MUST 含目标 / 输出格式 / 工具源指引 / 边界四要素。wide-search 特有的是「输出格式」必须是**按 schema 填一行**（每格含源 URL），让 lead 能机械地拼成矩阵。

### D4：schema 派发前确认（防 ×N 亏）
列（分析维度）一旦错，N 个 worker 全跑偏，损失 ×N。故 lead 在派发前 MUST 把对象清单 + 列 schema 输出给用户对一次。这与 deep-search 的「派发前澄清」精神一致，但更强制——deep-search 是非阻塞澄清，wide-search 因 ×N 风险默认**等用户确认 schema 再派**（用户可一句话说「就这样」放行）。

### D5：max_items 硬上限（默认 12）
对象数超过 max_items 时，lead MUST 分批（跑完一批再跑下一批）或要求用户收窄，MUST NOT 一次性铺 N 个 worker 撞 Task 并发上限 / 爆 token。默认 12 是「一屏矩阵可读 + 成本可控」的折中。

### D6：矩阵产物，复用 deep-search 双格式约定
- `report.md`：markdown 表格（行=对象，列=schema 维度，每格含证据 anchor 指向 traces）。
- `report.html`：可排序表格（用户可按列排序对比），与 report.md 语义等价。
- `traces/<worker>-<sid>/`：每个 worker 的原始产物，保留每行每格的证据。
- 沿用 deep-search 的 `finalize_usage.py` 出 cost 一行 + usage-summary.md。

### D7：部分 worker 失败不毁整张矩阵
某对象 worker 失败 / 没查到时，该行对应格标「未获取」，矩阵照常产出，MUST NOT 因单点失败放弃整张表。

### D8：/search-fast 命令薄封装
`/search-fast` 不引入新能力，只是给 fast-search 一个显式入口：主 agent 收到即派一个 fast-search，按既有 fast-search 产物约定返回。语义自动触发的老路径保留不变。

## Risks / Trade-offs

- **N 个 worker token 爆炸**：靠 max_items（默认 12）+ haiku worker 压。超限分批。
- **Task 并发上限**：同 turn 派太多 Task 可能撞 runtime 并发限制 → max_items 同时也是并发护栏；分批是兜底。
- **schema 错 → ×N 亏**：D4 强制派发前确认 schema，是本设计最重要的控本闸。
- **修改 locked 需求**：orchestration「唯一显式搜索 slash command」是 user-confirmed 锁，MODIFY 它必须走锁确认 gate，归档前逐条跟用户确认。
- **worker 深度不均**：虽然一对象一 worker 避免了 context 退化，但 haiku worker 对复杂对象可能不够深 → 允许 lead 对个别对象升级派 site-search 或标注「该项信息有限」。
