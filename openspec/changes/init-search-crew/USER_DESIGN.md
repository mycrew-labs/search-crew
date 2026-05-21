# USER_DESIGN delta · init-search-crew

> 本文件为 change `init-search-crew` 的 USER_DESIGN delta。归档后并入 `openspec/USER_DESIGN.md`（项目根）。
>
> **本 delta 内容由用户拍板，AI 不得自行修改。** 若实现过程中发现需要调整 P- 条目，AI MUST 先提请用户确认。

## Vision

这虽然是一个搜索工具，但**如何让用户理解数据的关联关系**、**如何真正把循证传递下去**，才是它优化的方向。

- 「数据关联关系」由 P-DATA-001 / P-OUTPUT-001 承载：产物目录结构 + ranking + 关键词索引 + wiki 风格大纲 + 附件约定让主模型与用户能像浏览代码库一样自助导航。
- 「循证传递」由 P-ROUTE-001 / P-EVIDENCE-001 承载：从搜索过程的循证工作流，到结论使用阶段对原始证据（URL、原文、数字）的强制保留。
- 「自我进化」由 Backlog B-004 承载：长期目标是把 [karpathy/autoresearch](https://github.com/karpathy/autoresearch) 的 checklist 评分 + 山爬迭代引入站点适配器与查询策略的自动优化，让 plugin 越用越好。

### 阶段划分

- **第一阶段（本 change）**：把上面前两个 vision 主轴落到位——三个 subagent、循证工作流、产物组织约定、配置生命周期、Stop hook 学习闭环
- **第二阶段（后续 change）**：实现 B-004 autoresearch 式适配器自动优化，让「自我进化」从设想落到工程

## 产品行为编号台账

| 编号 | 描述 | 测试用例 | 状态 |
|---|---|---|---|
| P-CMD-001 | 唯一显式 slash command 是 `/deep-search`；其余搜索由对话语义触发自动派发 | TC-CMD-001 | 待确认 |
| P-AGENT-001 | 三个 subagent 都做 ranking + 摘要；职责边界互不重叠 | TC-AGENT-001 | 待确认 |
| P-AGENT-002 | deep-search 派活优先，自抓允许；**研究边界判定为 OPEN 待细化** | TC-AGENT-002 | 待确认 |
| P-AGENT-003 | site-search API 优先、浏览器兜底；新适配器先查 GitHub / 现成实现 | TC-AGENT-003 | 待确认 |
| P-ROUTE-001 | 循证路由：先官方源 → 扩展 → 关键结论回官方源复核；所有 subagent + 主 agent 都遵循 | TC-ROUTE-001 | 待确认 |
| P-FALLBACK-001 | API key 完全可选，未配置时 fallback 到内置 WebSearch / WebFetch | TC-FALLBACK-001 | 待确认 |
| P-DATA-001 | 产物目录与调用语义（含关键词索引、附件约定） | TC-DATA-001 | 待确认 |
| P-OUTPUT-001 | 文件命名前缀 + 索引文件 + ranking 展示 + 关键词列表 + 附件 hash 目录 | TC-OUTPUT-001 | 待确认 |
| P-MCP-001 | Plugin 自带 chrome-devtools-mcp，安装即拉起 | TC-MCP-001 | 待确认 |
| P-BRAND-001 | 品牌归属与 org / DockerHub namespace | n/a | 待确认 |
| P-PARALLEL-001 | 同 turn 并行派发；派发前先用结构化任务工具登记 | TC-PARALLEL-001 | 待确认 |
| P-CONFIG-001 | `~/.config/search-crew/` 是 runtime 唯一真相；onboarding 提示备份 / 软链接 | TC-CONFIG-001 | 待确认 |
| P-LEARN-001 | Pending 学习区 + Stop hook 自动提示晋升 / 丢弃 / 暂留 | TC-LEARN-001 | 待确认 |
| P-UX-001 | subagent 启动时向用户输出协作邀请，用户中途贴入的提示注入后续派发 | TC-UX-001 | 待确认 |
| P-EVIDENCE-001 | 主 agent / subagent 必须把原始 URL、关键原文、关键数字作为循证证据传递下去 | TC-EVIDENCE-001 | 待确认 |

---

## P-CMD-001 ：触发方式

- **唯一显式 slash command**：`/deep-search <主题>` —— 手动强制触发 deep-search
- **其余所有搜索场景**：用户在对话中自然表达搜索意图，主 agent 按语义自动派发对应 subagent
  - "查一下" / "找几个" / "X 是什么" → 主 agent 派 fast-search
  - "去官网查" / "看官方文档" / 命中权威性敏感主题（临床 / 专利 / 学术 / 编程语言官方文档等） → 主 agent 派 site-search（站点由主 agent 按 P-ROUTE-001 起点表选定）
- **不提供** `/search` 这样的总入口，也**不提供** `--site <url>` 这样的参数
  - 取消原因：让用户填一个具体 URL 容易出错（站点判断、子域名、版本路径都难约定），不如让主 agent 按主题自己定起点站

### 不变量

- 日常搜索不需要任何 slash command，关键词触发即可
- 唯一存在的显式 command 是 `/deep-search`，用于「我现在就要一次深度调研」

## P-AGENT-001 ：三个 subagent 的存在与职责边界

| Subagent | 默认模型层级 | 职责（共性 + 差异） | 主交付物 | 是否循环 |
|---|---|---|---|---|
| `fast-search` | 轻量级 | 通用搜索 + 抓取 + **ranking + 摘要** | 内容 md + wiki 索引（保留全料） | 否 |
| `site-search` | 旗舰级 | 站点精确搜索（API 优先 / 浏览器兜底）+ 抓取 + **ranking + 摘要** | 内容 md + wiki 索引（保留全料） | 内部可循环 |
| `deep-search` | 旗舰级 | 多轮调研：派发 fast/site + 自抓深挖 + 综合 + **消化压缩成报告** | **HTML 报告（给用户，直观可视）+ Markdown 报告（给主模型）+ 可追溯底层产物子目录** | 是 |

### 共性约定

- 三个 subagent **都必须**做 ranking 与摘要——具体形态由 P-OUTPUT-001 约定
- 三个 subagent **都必须**遵循 P-ROUTE-001 的循证工作流
- 三个 subagent **都必须**遵循 P-EVIDENCE-001 的证据传递约定（在摘要中就准备好可引用的证据片段）

### 不变量

- 职责互不重叠：fast 不做站内精确搜索；site 不做跨主题调研；deep 不自己实现搜索 backend
- ranking + 摘要是三者共性，不允许任何一个跳过

## P-AGENT-002 ：deep-search 的工作模式（派活优先，自抓允许）

- deep-search **不重新实现搜索 backend**：所有通用搜索通过派发 fast-search 完成，所有官方站精确搜索通过派发 site-search 完成
- deep-search **被允许**直接用 fetch 工具抓取已知 URL，并沿页面里的链接继续深挖
- 自抓应在以下条件出现时才用：
  - 已经拿到具体 URL，再派一个 subagent 反而绕路
  - 沿链接深挖某一线索时（典型如顺着引用、文献链、参考资料追下去）
- 主体仍是「规划、综合、判断、跟进」：每轮派发新一批 subagent，等结果回流，写 round-N.md 总结，决定是否再循环

**边界**：deep-search 不准为了一个一次性查询就自己拼 Jina/Serper 请求。

### 待解决问题 OPEN-AGENT-002-A ：研究完成边界判定

> **状态：未定，实现时细化。** 暂记参考方向，先建议性设计、暂不写死。

deep-search 怎样算「研究完了」目前没有干净答案。当前思考：

- **参考 OpenAI Deep Research**：先定义本次研究的**角度与结构清单**，完成清单即视为研究完成
- **完成标准的两种粒度**：
  - 整体粒度：清单中所有任务都至少有产物
  - 单项粒度：单项可由 deep-search 自评（是否已答 / 新抓内容质量是否太低 / 已达预设深度）
- **可选升级（未来）**：清单出来后**先跟用户确认方向**，确认后再启动 research——让结束边界与开头边界都对齐用户预期

实现期需要决定：
1. 首版直接走「清单完成即结束」，还是带「清单先经用户确认」？
2. 单项完成判定是 deep-search 自评，还是另派一个 reviewer subagent？
3. 是否保留兜底硬上限（如 max_rounds），避免无限循环？

## P-AGENT-003 ：site-search 的工作模式（API 优先，浏览器兜底）

按以下优先级降级：

1. **优先级 1：API 适配器**。如果 site 有专用适配器（见 ROUTING.md 适配器清单），直接调用
2. **优先级 2：固定 URL 模式**。即使没有适配器，很多站点搜索 URL 是 `https://<site>/search?q=<query>` 等可推断形式，用 fetch 抓取静态结果页
3. **优先级 3：Chrome DevTools MCP**。前两条都不行才动用浏览器
   - 适用：SPA 站点 / JS 异步加载结果 / 需要登录态 / URL 不可 deep link
4. 必须遵守 robots.txt 与速率限制，不得对单一站点高频请求

**不变量**：浏览器是最后手段，不得跳过前两级。

### 新适配器实现策略（强建议）

实现一个新站点适配器或调整查询方式时，**首选**做法：

1. 先去 GitHub 搜对应站点的现成抓取实现（例：搜 `mdn site:github.com`、搜 `<站点名> scraper / api wrapper`）
2. 同时用 fast-search 搜博客 / 教程 / Stack Overflow 上的查询模式总结
3. 找到一个或多个可参考实现 → 改写 / 移植 / 缝合
4. **没有现成参考时再自己猜接口**

理由：靠猜接口实现适配器调试成本极高；社区往往已经做过。

参照他人代码时必须遵守源仓库许可证，复用代码 SHOULD 在 adapter 文件顶部注释里写明来源链接与改写程度。

## P-ROUTE-001 ：循证路由（先官方源、再扩展、关键结论必须复核）

> **适用范围**：所有 subagent（fast-search / site-search / deep-search）+ 主 agent 都必须遵循本条。

主题路由清单是**起点**而非终点。整体逻辑是严格的循证：先在指定的官方 / 权威路径里搜，找不到再扩展到其他来源；任何从非官方来源得到的关键结论，**必须**回官方源复核，找不到官方记录的要在产物中明确标注「未在官方源验证」。

### 路由起点表（首版主题对应官方 / 权威路径）

| 主题 | 起点路径 |
|---|---|
| 临床研究 | site-search → clinicaltrials.gov + pubmed.ncbi.nlm.nih.gov |
| 专利 | site-search → patents.google.com / espacenet.com / cnipa / 智慧芽 |
| 学术论文 | site-search → arxiv.org / semantic-scholar.org |
| 编程语言 / 框架 / 库的使用说明 | site-search → context7 + 该项目自家官方文档站 |
| 官方产品文档（云 / 工具 / 中间件） | site-search → 对应官方文档站 |
| 包仓库 | site-search → PyPI / npm / crates.io / GitHub Releases 等对应官方仓库 |

这是**起点**，不是禁区。具体清单在 ROUTING.md 维护，AI 可在 TECH 层迭代扩展。

### 循证工作流（硬规则）

1. **第一步：先在起点搜**。命中主题时，必须先在对应官方 / 权威路径里搜
2. **第二步：信息不足时扩展**。起点结果不够时，可以扩展到通用搜索（fast-search）或其他来源补充
3. **第三步：关键结论必须回官方源复核**。任何在第二步从非官方来源得到的关键结论，调用方 MUST 派一个 site-search 回到对应官方路径**重新查证**「该结论在官方源是否有记录」
4. **第四步：未通过复核的内容必须标注**。官方源找不到的结论，要在最终产物中明确标注「未在官方源验证」；调用方不得把它当作已验证事实呈现给用户

### 不变量

- 跳过第一步、直接通用搜索处理上表主题，即视为产品行为缺陷
- 第三步的「回官方复核」是硬规则，不允许 AI 以「内容看起来对」为由跳过
- 起点路径清单可以由 AI 增删（TECH 层），但本节四步循证工作流不允许 AI 自行修改
- 不区分 subagent 类型：fast-search 派出去做的通用搜索，回收时主 agent 同样要按本流程做复核；site-search 当自己的目标站不是官方主源时，也要回头去主源比对；deep-search 在综合阶段对每条引用都要套用

## P-FALLBACK-001 ：API key 完全可选

- 任何 backend 的 API key 都是可选的
- 未配置时，搜索 / 抓取脚本 MUST 返回明确的 fallback 提示（如 `WEBSEARCH_FALLBACK` / `WEBFETCH_FALLBACK`），由调用方改用 Claude Code 内置 WebSearch / WebFetch
- `/setup` 必须如实报告每个 backend 的可用 / 未配置状态，并给出注册链接与 `~/.zshrc` 配置模板

**不变量**：plugin 在零 key 状态下仍能完成基本调研。

## P-DATA-001 ：产物目录与调用语义

### 目录约定

- 所有 run 产物落在 `/tmp/search-crew/<session_id>/`
- `<session_id>` 直接用**当前 subagent 自己的 session-id**，不需要额外调用时间函数或生成 run_id
- 主 agent 在最后回复中告知用户产物目录路径，并询问是否复制到项目目录

### 调用语义（关键）

**主线程 → subagent**：
- 主线程**不传**产出目录给 subagent
- subagent 自己用 `/tmp/search-crew/<自己的 session_id>/` 工作
- subagent 完成后**只返回产出目录路径 + 极简摘要**，主线程拿路径自己进去探索

**subagent → subagent**（典型：deep-search 调 fast-search / site-search）：
- 上级 subagent **必须把目标目录传给下级**（一般是上级自己的产出目录下的子路径）
- 下级在该路径内工作，产物归集在上级目录里
- 避免出现「一次 deep-search 的产物散落在好几个 session-id 目录」的情况

### 内容组织：让主模型像 grep 代码库一样自助导航

subagent 在落盘搜索结果时，**MUST** 同时完成以下三件事（细节由 P-OUTPUT-001 约定）：

1. **Ranking 落盘**：搜索结果按 ranking 排序保存，且 ranking 的得分 / 理由可见
2. **关键词索引**：摘要中显式列出本批内容的「关键词清单」（专业术语、人名、版本号、产品名、API 名、关键数字等），让主模型可以 grep 出关键词出现在哪个文件的哪段，只读那一段而不必通读
3. **附件存储约定**：抓回来的网页附件（图片 / PDF 等）统一存放，markdown 用相对路径引用，附件文件名用 hash 去重（细则见 P-OUTPUT-001「附件存储」段）

### 不变量

- 单次主线程发起的调研，最终用户视角下只看到**一个**根目录
- plugin 不写入用户项目目录，除非用户明确同意复制
- 主模型拿到产物目录后，必须能通过「读索引 + grep 关键词 + 跟引用读 markdown」三步走完导航，不必通读全部文件

## P-OUTPUT-001 ：产物命名前缀、索引文件、Ranking、关键词与附件存储

主线程拿到 subagent 返回的目录后，应该能像浏览一个**陌生但结构清晰的代码库**一样自助导航。具体约束如下。

### 文件命名前缀

所有 subagent 落盘的文件 / 子目录 MUST 以 subagent 名字开头：

- `fast-search/` 或 `fast-search-*.md` ：fast-search 抓回的内容与摘要
- `site-search/` 或 `site-search-*.md` ：site-search 抓回的内容与摘要
- `deep-search/` 或 `deep-search-*.md` ：deep-search 自己写的分析、轮次总结、链接深挖产物

混合命名（如 `results-1.md`）禁止。

### 索引文件（每个 subagent 必产，wiki 风格大纲）

每个 subagent 完成任务前 MUST 在自己的目录里生成约定的索引文件（具体文件名 / 内容结构由 `search-toolkit` skill 约定并维护）。**索引文件不是简单的文件清单，而是一份 wiki 风格的大纲**，至少回答以下五件事：

1. 本次任务的输入（query、参数、起点路由）
2. **子文件链接 + 该文件包含什么内容的一段话**（不只是 filename，而是"这个文件讲了什么"）
3. **推荐 / 不推荐去看 + 评分备注**（标注哪些 must-read、哪些可跳过、为什么 ranking 低；评分理由要可读）
4. **本次内容的关键词清单**（专业术语 / 人名 / 版本号 / 产品名 / API 名 / 关键数字等），给主模型 grep 用
5. 主线程进一步该读什么、按什么顺序读

**核心理念**：让主模型读这一份索引就能像读 wiki 主页一样，对整批产物有 mental model。

### Ranking 展示

- 每条结果必须带 ranking 得分 + 简短理由
- 索引文件中的结果列表按 ranking 排序，得分低的也保留但排后
- ranking 维度建议：与 query 的相关度、来源权威性、信息新鲜度、覆盖深度

### 关键词清单（关键约定）

- 每个 subagent 在生成摘要时，MUST 同步产出本批内容的「关键词清单」
- 关键词必须包含：专业术语、人名 / 团队名、版本号 / 时间、产品 / 项目 / API 名、关键数字（性能指标、价格、阈值等）
- 关键词清单写在索引文件中，**必须是可 grep 的纯文本形式**（一行一个或逗号分隔）
- 单条 markdown 的开头 SHOULD 也带本文件的关键词子集（让 grep 第一次命中就能定位）

理由：让主模型像「知道函数名再读代码」那样高效——通过 grep 关键词跳到具体 markdown 的具体段落，而不必通读所有产物。

### 附件存储约定

- 抓回来的所有附件（图片 / PDF / 大文件等）统一存放在 run 根目录下的 `attachments/` 子目录
- 附件文件名 = `<sha256[:12]>.<原扩展名>`（hash 去重，多 markdown 引同一附件只存一份）
- markdown 中通过**相对路径**引用：`![](../attachments/<hash>.png)`
- 索引文件中 SHOULD 维护一份 `attachments` 表：hash → 原始 URL + alt text / caption

### 按 subagent 区分的产物形态（关键）

不同 subagent 的产物语义不同，主交付物不一样：

**fast-search / site-search**（保留全料 + wiki 索引）：
- 主交付物 = 抓回的内容 markdown 文件 + wiki 风格大纲索引
- 原始内容尽量保留（带 ranking、推荐与否、关键词），让主模型自己挑哪些有用
- 适合：内容不算太多、主模型有能力消化的场景

**deep-search**（丢弃 + 报告，但保留追溯；HTML / Markdown 双格式）：
- deep-search 调研一轮下来，底层 fast/site 产物可能极其庞大；不能原样回传
- **主交付物 = 一份报告**，必须同时产出两个语义等价的版本：
  - **`report.html`**：给**用户**看。用更形象、直观、可视的方式呈现结论（图、表、卡片、折叠区块、彩色高亮等）；引用循证时把链接做成可点击的 anchor，链接对象为外部 URL 或本地 markdown 文件路径
  - **`report.md`**：给**主模型**看。同样的结论、结构、引用，但用纯 markdown，没有可视化装饰；主模型读这一份，不读 HTML（HTML 对 LLM 效率低）
- 两份文件内容必须语义等价，只是表达形式不同；不允许 HTML 多结论 / 少结论
- 底层 fast/site 派生产物**保留在子目录里**作为追溯（上级或用户想验证可以下钻），但不是主交付物
- 索引文件指向「用户先看 `report.html`，主模型先看 `report.md`」，需要时再按引用下钻底层产物
- 理由：deep-search 跨多轮、内容海量；原样上传消化不了；HTML 形态又让用户复核成本极低（可视化 + 一键跳转证据）

#### HTML 报告的生成方式（已定）

- **由 deep-search LLM 自由生成 HTML**：不预置 HTML 模板、不引入 pandoc / markdown-it 等静态转换链路、不强制图表库
- LLM 可以按当次内容自由选择形式（卡片、表格、折叠区块、内嵌 svg / mermaid 等），优先服务"用户读起来直观"
- 唯一硬约束（不允许实现层放宽）：
  - HTML 给用户、Markdown 给主模型
  - `report.html` 与 `report.md` 语义等价
  - 引用循证时，HTML 中链接必须可点击，链接对象为外部 URL 或本地 markdown 路径
- design.md 阶段只需补充：报告产出后是否在用户回复中附「在浏览器打开」的命令提示（实现细节，不约束 LLM 内部写法）

### 不变量

- 主线程**只需要一个目录路径**就能理解整个产物结构，不依赖 subagent 的额外口头说明
- skill 必须把命名前缀、索引文件结构、ranking、关键词清单、附件目录约定全部作为强约定记录，所有 subagent 必须遵守
- ranking 与关键词清单是 subagent 处理内容时**当下**就要完成的工作，不允许「先全抓回来后续再补」
- fast/site 必须保留全料；deep-search 必须丢弃绝大部分原始内容、给报告，但**必须保留可追溯的底层产物**
- deep-search 报告必须同时输出 `report.html`（给用户）与 `report.md`（给主模型），两份语义等价

## P-MCP-001 ：自带 chrome-devtools-mcp

- `.claude-plugin/plugin.json` 通过 `mcpServers.chrome-devtools` 字段声明，命令为 `npx -y chrome-devtools-mcp@latest`
- Claude Code 安装 plugin 时自动拉起，无需用户额外配置
- 首次使用 site-search 走浏览器路径时，需要本地有 Google Chrome；`/setup` 应检查并提示

## P-BRAND-001 ：品牌与命名

- 项目品牌：**MyCrew**
- GitHub org：<https://github.com/mycrew-labs>
- Docker Hub namespace：<https://hub.docker.com/repositories/mycrew>
  - 镜像名本身**不强制**以 `mycrew` 开头，只要发布在该 namespace 下即可
- 本 plugin 仓库名：`search-crew`

## P-PARALLEL-001 ：并行派发与任务登记

- 单轮内多个 subagent 必须在同一 turn 内一次性派发（并行），不得串行
- 派发 subagent 前，主 agent / deep-search MUST 先调用 **TaskCreate** 建立任务清单，并在执行过程中用 **TaskUpdate** 维护状态
- 工具名以官方文档为准（避免字段理解上的分歧）：<https://code.claude.com/docs/en/agent-sdk/todo-tracking> ——自 TypeScript Agent SDK 0.3.142 / Claude Code v2.1.142 起，sessions 改用 `TaskCreate` / `TaskUpdate` / `TaskGet` / `TaskList`，取代旧 `TodoWrite`
- 任务描述面向用户（"查找 React 官方关于 Suspense 的最新说法"），不写"派发 site-search worker"这种内部叙事

**不变量**：用户在任意时刻能通过 TaskList 看到当前调研全貌。

## P-CONFIG-001 ：配置真相与生命周期

- `~/.config/search-crew/` 是 runtime **唯一**配置真相
- **首次安装**：plugin 把内置 `defaults/` 一次性**拷贝**到 `~/.config/search-crew/`
- **此后**：runtime 只读 active 目录；plugin 升级**不动** active；plugin 内的 defaults 仅作为参考
- 用户对 active 拥有**完全所有权**：可以禁用 / 替换 / 重写任何系统默认行为，包括关掉某个适配器、改起点路由、加自定义参数、加自己的 Python 适配器文件
- 不提供 `diff-defaults` / `adopt-defaults` 这类同步命令——用户想看新 defaults 直接去 plugin 仓库看

### Onboarding 提示（必做）

`/setup` 首次运行时 MUST 醒目地提示用户：

> `~/.config/search-crew/` 是你长期积累的配置（包含路由偏好、自定义适配器、晋升过的 pending 规则）。**强烈建议**：
> 1. 把它放到一个会同步备份的目录（如 iCloud / Dropbox / 你自己的 dotfiles 仓库），原位置改成软链接；或
> 2. 定期手动备份。
>
> 否则一旦本地 `~/.config/search-crew/` 丢失，你长期沉淀的偏好就找不回来了。

### 不变量

- runtime 永不读 plugin 内置 defaults（首次安装拷贝那一次除外）
- AI **永不**直接修改 active 目录的内容；要建议改动 → 走 P-LEARN-001 的 pending 流程

## P-LEARN-001 ：Pending 学习区 + Stop hook 自动提示

- AI 在使用中发现新路由 / 新站点 / 新参数偏好时，写入 `~/.config/search-crew/pending/`
- 当次 run 用了 pending 项，必须在产物中标注「来自 pending，未确认」
- **Stop hook**：每次主 agent 工作告一段落（Claude Code Stop 事件），plugin 自动扫描 pending 目录
  - 非空时向用户呈现简洁提示：「这次调研产生了 N 条候选规则，是否要……」
  - 三个选项：
    - **晋升为长期规则** → 合并进 active
    - **丢弃** → 删除 pending 项
    - **暂留** → 保留，下次 Stop 再问
- 用户全程无需记任何命令；交互入口完全在 Stop hook 自动提示里

### 不变量

- pending 项不参与运行时默认行为，仅在被晋升后才纳入 active
- pending 来源的内容在产物里必须显式标注

## P-UX-001 ：subagent 启动时的协作邀请

- 每当主 agent 派发 subagent 开始搜索时，向用户输出**一行**简洁、非阻塞的提示：
  > 💡 如果你已经知道权威数据源或希望使用的查询条件，可以直接贴进来，AI 会优先采用
- 用户在等候期间贴入的内容，主 agent 视为**高优先级 hint**：
  - 注入到下一轮派发的 subagent prompt 中
  - 或附加到当前正在运行的 subagent 的后续判断依据
  - 用户提供的数据源 / 查询条件优先级高于 active 配置里的默认起点
- 提示应在每次 run 至少出现一次，多 subagent 派发时不必重复

### 不变量

- 用户随时可参与，不必等调研结束才能干预
- 用户提供的内容不会污染 active 配置（除非走 P-LEARN-001 流程被显式晋升）

## P-EVIDENCE-001 ：循证证据必须传递

> **本条与 P-ROUTE-001 互补**：P-ROUTE-001 管「搜索过程的循证」，本条管「结论使用阶段对原始证据的强制保留」。两条同时生效，才能让 vision 中的「循证传递」真正闭环。

主 agent / 任一 subagent 在向用户呈现任何**来自搜索的判断、用语、概念、代码实现、数字**时，**必须**附带循证证据。证据形式：

| 证据元素 | 强度 |
|---|---|
| 原始 URL（结论引用的具体页面） | **必须** |
| 关键原文摘录（一两句原话，证明结论不是脑补的转译） | 结论性强的内容**必须**；纯流程性描述可省 |
| 关键数字 / 性能指标 / 价格 / 版本号 | 如有，**必须** |

### 工作约定

- **subagent 在摘要时就要准备好可引用的证据片段**：索引文件 / 摘要 markdown 里必须保留可定位到原始 markdown 的 anchor（如「见 `fast-search-3.md` 第 12 行」）
- **主 agent 在最终回复用户时**：每段结论后必须挂上证据（URL + 必要时的原文 / 数字）
- 来自 P-LEARN-001 pending 的内容、来自 P-ROUTE-001 第 4 步「未在官方源验证」的内容，主 agent 必须在最终回复中**显式标注**这一点

### 不变量

- 搜索来的内容如果没有证据出现在最终回答中，视为**循证链断裂**缺陷
- 「证据」不是脚注美化，而是用户复核的入口——必须可点击 / 可定位 / 可比对原文
