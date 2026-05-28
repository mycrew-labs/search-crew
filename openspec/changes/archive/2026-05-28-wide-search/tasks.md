## 1. wide-search lead subagent（agents/wide-search.md）

- [x] 1.1 写 frontmatter：name=wide-search、model=claude-sonnet-4-6、tools=Bash,Read,Write,Task、description（批量对照矩阵 lead）
- [x] 1.2 启动必读段：SKILL.md / ROUTING.md / limits.yaml（读 `wide_search.max_items`）
- [x] 1.3 接收参数段：topic（批量对比需求）/ target_dir（可选，缺省用 session-id）/ purpose
- [x] 1.4 工作流第一步「拆对象清单 + 统一分析 schema」+ **派发前 MUST 向用户确认对象清单与列**（×N 风险，等放行再派）
- [x] 1.5 工作流第二步「一对象一 worker、同 turn 并行派发」：复用 fast-search（默认 haiku）/ site-search（按需），派每个 worker 的 Task prompt 含任务契约四要素，输出格式 = 按 schema 填一行 + 每格附源 URL
- [x] 1.6 max_items 约束：超限分批 / 请用户收窄，禁止一次铺超 max_items 个 worker
- [x] 1.7 汇总段：产 report.md（md 表格 + 每格 anchor）+ report.html（可排序表格，语义等价）+ traces 保留；单点 worker 失败标「未获取」不毁整表
- [x] 1.8 返回三行（report.html / report.md / cost 一行，cost 调 finalize_usage.py --one-line）
- [x] 1.9 关键约束段 + 何时不该用 wide-search（单对象深挖走 deep-search、单点查询走 fast/site）

## 2. slash 命令

- [x] 2.1 新增 `commands/search-wide.md`：frontmatter name=search-wide；主 agent 工作流（TaskCreate → 协作邀请 → 派 wide-search → 等返回 → 读 report.md → 回复用户三块）参照 search-deep.md 结构
- [x] 2.2 新增 `commands/search-fast.md`：薄封装，主 agent 收到即派一个 fast-search，按既有 fast-search 产物约定返回；说明语义自动触发老路径仍保留

## 3. 配置（defaults/limits.yaml）

- [x] 3.1 加 `wide_search.max_items: 12` 段 + 注释（每次最多并行几个 worker；超限分批或收窄；理由：Claude subagent 非独立 VM，成本 ~15×）

## 4. 文档 / 人工验证

- [x] 4.1 README / EXTENDING：补 wide-search 能力说明（求广、对照矩阵、worker 复用廉价档）+ 三个 search-* 命令一览
- [x] 4.2 `tests/MANUAL.md` 补人工验证项：wide-search 派发前确认 schema；一对象一 worker 并行；超 max_items 分批；矩阵双格式 + 每格可回溯；单点失败标「未获取」；/search-fast 能显式触发 fast-search

## 5. 归档前：锁确认 gate（按 change-flow 规则）

- [x] 5.1 `openspec validate wide-search --strict` 通过
- [ ] 5.2 完工简报：本次 MODIFY 了 locked「唯一显式搜索 slash command 是 /search-deep」（→ 三命令并列），新「显式搜索 slash command：/search-deep、/search-wide、/search-fast」拟落 user-confirmed 锁；逐条跟用户确认
- [ ] 5.3 用户确认 → 落锁 → bump version → `openspec archive wide-search` → commit
- [ ] 5.4 **manual** · reload 后实测：`/search-wide` 跑一个批量对比（看是否先确认 schema + 并行 worker + 出矩阵）；`/search-fast` 跑一次（看是否显式触发 fast-search）
