# Design — deep-search-research-upgrades

## Context

deep-search 现状（locked）：第一轮产 plan.md（角度+子任务+完成判据）→ 同 turn 并行派 fast/site-search（传 target_dir）→ 每轮自评 → 受 `max_rounds`（默认 5）硬上限 → 综合产 report.md + report.html + traces。`per_round_breadth`（默认 4）现在是「每轮派几个」的固定值。

本次 5 项增量全部在这套结构内增强 prompt 行为，不改 locked 需求本身。主要落在 `agents/deep-search.md`（subagent prompt）与 `commands/search-deep.md`（主 agent 闭环）。

**关键约束**：deep-search 是 subagent，**跑起来后无法与用户来回交互**。所以「开跑前澄清」（#2）必须发生在**主 agent 派发之前**（search-deep 命令流程里），不是 deep-search 内部。

## Goals / Non-Goals

**Goals:** 该深则深、该省则省（缩放）；错方向早拦（澄清）；worker 不 drift（契约）；结论可信（找矛盾）；每轮有判断（轮间思考）。

**Non-Goals:** 不改现有结构（plan.md → 并行轮次 → 双格式报告 + traces）；不动 `max_rounds` locked 上限；不引入异步编排（仍同步轮次）；不重写 worker（仍 fast/site-search）。

## Decisions

### D-1 复杂度缩放（在 caps 内选投入）

lead 在 plan.md 里**显式记一行复杂度评估 + 投入决策**，参考 Anthropic 的缩放规则（映射到我们的 caps）：

| query 类型 | worker 数（≤ `per_round_breadth`） | 轮数（≤ `max_rounds`） |
|---|---|---|
| 误入的简单事实/单点（本该 fast/site） | 1 | 1，尽快收 |
| 单一主题中等深度 | 2-3 | 1-2 |
| 横向对比 / 多角度 | 3-4 | 2-3 |
| 复杂跨域 / 需循证链 | 铺满 breadth | 至 max_rounds |

`per_round_breadth` 语义从「固定派 4 个」改为「**每轮上限**」——lead 按复杂度选 ≤ 它的数。`limits.yaml` 仅改注释，值不变。

**为什么放 plan.md**：评估可见、可被用户/上级质疑，也是 traces 的一部分。

### D-2 开跑前澄清范围（主 agent 层，非阻塞）

落在 `commands/search-deep.md`（主 agent 派 deep-search **之前**）：

- topic **有明显歧义 / 范围过宽**时，主 agent 先发**一句话**澄清（如「你要的是 A 角度还是 B？默认我按 A 全面查」），**非阻塞**：用户不答则按句中言明的合理默认继续派发。
- topic 已清晰则**不问**，直接派（避免每次都打扰——回应你之前「默认静默、只在明显歧义才问」的倾向）。
- deep-search 内部仍把**本次假设范围**写进 plan.md 顶部（「本次按 X 范围调研，如需调整请说」），让范围始终可见、可中途纠偏。

### D-3 subagent 任务契约四要素

deep-search 派 fast/site-search 时，Task prompt MUST 含四要素（缺任一 → drift）：

```
目标：这个 worker 要回答的具体子问题
输出格式：期望的产物形态（如 fast-search-NNN.md + INDEX，按既有约定）
工具/源指引：起点路由（该走 fast 还是 site、哪些官方源），含 routing 硬规则提醒
边界：不做什么（不越界到别的子任务、不多轮、命中权威主题回信号）
```

现有「传 target_dir」locked 需求不变，契约四要素是其上的增量（target_dir 属「边界」的一部分）。

### D-4 综合阶段显式找矛盾

report.md / report.html 综合时，除按 plan 子任务组织结论外，MUST：

- 交叉多源发现**冲突/分歧**时，单独标出（如「⚠️ 分歧：源 A 说 X，源 B 说 Y」），不偷偷选一个。
- 每条关键结论标注循证状态：已回官方源复核 / 未复核存疑（沿用循证四步第 4 步「未通过复核必须标注」）。

### D-5 轮间 interleaved thinking

每轮结束写 `round-N.md` 时，除现有「派了什么/收了什么/子任务 done 自评」外，MUST 加一段**显式 gap 评估**：

```
已覆盖：...
还缺：...
下一轮补哪个角度（或：已够，进入综合）
```

强化现有自评——从「子任务 done/not-done」升级到「主动找缺口 + 决定下一步」。

## Risks / Trade-offs

- **复杂度评估可能误判**（把复杂题评简单 → 投入不足）。缓解：评估写在 plan.md 可见；轮间思考（D-5）能在发现覆盖不足时补轮（仍 ≤ max_rounds）。
- **澄清打扰**：问太多惹烦。缓解：仅明显歧义才问、非阻塞、有默认。
- **找矛盾增 token**：综合阶段多一层对比。缓解：值得（结论可信度是 deep-search 的核心价值）。
- **prompt 行为难量化测试**：以 MANUAL.md 人工验证为主。

## Open Questions

- 复杂度评估要不要做成可量化 rubric 写进 limits.yaml？倾向**不**——放 prompt 里更灵活，limits 只管硬上限。
- #2 澄清的「歧义」判定阈值靠主 agent 判断，无硬规则——接受软判断。
