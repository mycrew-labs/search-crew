# Search Crew Plugin

Claude Code plugin，为调研类任务提供三层能力：快速搜索、站点精确搜索、深度循环挖掘。通过文件系统作为中介实现 context 隔离。

## 品牌归属

- 项目品牌：**MyCrew**（Search Crew 是 MyCrew 旗下首个 plugin）
- GitHub org：<https://github.com/mycrew-labs>
- Docker Hub namespace：<https://hub.docker.com/repositories/mycrew>

## 规格分层

- `openspec/project.md` / `openspec/USER_DESIGN.md` / `openspec/TECH.md` ：项目最高级别约定，与 `project.md` 平级，直接放 `openspec/` 根目录
- `openspec/specs/capabilities/<name>/spec.md` ：单能力详细行为描述
- `openspec/changes/<id>/` ：进行中的变更与对应 delta
- `USER_DESIGN.md` 与 `proposal.md` 的范围 / 非目标由用户拍板，AI 不得自行修改
- `TECH.md` / `design.md` / `tasks.md` / `capabilities/<name>/spec.md` 由 AI 在实现过程中迭代

## 工作流

每个变更：

1. `openspec/changes/<change-id>/proposal.md` ：背景、动机、范围、非目标
2. `openspec/changes/<change-id>/USER_DESIGN.md` delta ：新增 / 修改 P- 行为，需用户确认
3. `openspec/changes/<change-id>/TECH.md` delta ：架构方案 T- 决策
4. `design.md` ：临时设计推演
5. `tasks.md` ：可执行步骤 + 规格同步项

合并归档后，USER_DESIGN / TECH delta 沉淀回 `openspec/` 根目录的对应文件，能力 delta 沉淀回 `openspec/specs/capabilities/<name>/spec.md`。

## Backlog（项目级长期待办）

> 当前不在任何进行中 change 的范围内；后续按需起新 change。

- **B-001 自建文档转 Markdown 镜像**：参考 / 借鉴 [docling](https://github.com/docling-project/docling) 与 [markitdown](https://github.com/microsoft/markitdown)，将文档（PDF / DOCX / PPTX / XLSX / HTML / 图片 / 音频 / EPub / ZIP 等）转 Markdown 的能力编译成 Docker 镜像，发布到 `hub.docker.com/repositories/mycrew`。
- **B-002 轻量运行环境**：调用方式参考 [microsandbox](https://github.com/superradcompany/microsandbox)，让用户客户端只需安装一次轻量级运行环境，无须长驻 daemon，每次像执行命令一样完成转换。
- **B-003 集成进 Search Crew**：把 B-001 / B-002 的能力作为 fetch / site-search 的转换后端之一，让抓回来的非文本资源也能进入 Markdown 流。
- **B-004 autoresearch 式适配器自动优化**：把 [karpathy/autoresearch](https://github.com/karpathy/autoresearch) 的「checklist 评分 + 山爬迭代」流程引入「新增 / 优化站点适配器与查询策略」的过程。
    - **评判函数**：本场景特别清晰——能不能找到内容、多次运行的稳定性、速度、准确性，都是天然可量化的维度。
    - **优化循环**：参考 autoresearch 的 5 步法（小改 prompt / 适配器代码 → 跑 10 个测试用例 → 用 3-6 个是/否 checklist 打分 → 比上一轮高就保留，低就回滚 → 重复直到连续 3 轮 >90% 或人喊停）。
    - **落地形态**：新建适配器 / 调整查询条件时，可以让一个独立 agent 按这套流程自动迭代；产物是一份打分日志 + 最终采纳的版本，走 Pending → Active 通道供用户审核。
    - **关联**：与 Pending 学习区（见 USER_DESIGN P-LEARN-001 草案）配合，自动迭代产物天然落在 pending，Stop hook 时统一提示用户晋升或丢弃。
- **B-005 API 调用次数与 cost 统计**：对所有需要密钥访问的 backend（Jina、Serper、未来可能的 OpenAI / Claude API 等）记录每次调用次数与按官方计费的估算成本，让用户清楚地知道每次调研花了多少。
    - **粒度**：单次 run 内附 `usage.jsonl` 打点（backend / endpoint / status / tokens / cost_estimate），最终主交付物末尾追加一段 cost summary；跨 run 汇总到 `~/.local/state/search-crew/usage.jsonl`（统计不是配置，故不放 `~/.config/search-crew/`）。
    - **价格表**：每个 backend 的单价表内置在 plugin，过时由用户在 `~/.config/search-crew/pricing.yaml` 覆盖。
    - **未决方向**（起新 change 时讨论）：
      - 是否需要月度 / 日度报告 + 阈值告警？
      - 是否在 Stop hook 提示中带本次 cost summary？
      - 是否要把 cost 信息也写进 deep-search `report.html` 给用户直观看见？
    - **关联**：本能力会带出新 P-USAGE-001 行为（cost 统计的对外承诺），起新 change 时需要走 USER_DESIGN 流程。

## 关联规则

- 全局：`$AI_HOME/AGENTS.md`、`$AI_HOME/rules/change-flow.md`
- Python 脚本编码规范：`$AI_HOME/rules/coding/python.md`
- 临时脚本依赖：PEP 723 + `uv run`（见 `rules/change-flow.md` 临时脚本节）
