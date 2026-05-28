## Why

deep-search 已是 orchestrator-worker（lead 规划 + 并行派 fast/site-search + 多轮自评 + 循证报告），但对照 ChatGPT Deep Research 与 Anthropic 多 agent 研究系统，有 5 处成熟做法可融入，提升「该深则深、该省则省、结论更可信」：

- Anthropic 实测：**token 用量解释 80% 的效果差异**，且多 agent ~15× token——所以「按复杂度缩放投入」既提质又控本。
- ChatGPT DR：开跑前**澄清范围**、综合阶段**找矛盾**，避免「跑完 5 轮发现方向错」和「罗列而不辨真伪」。

## What Changes

5 项增量（均在现有 locked 上限/结构内，不破坏现有行为）：

1. **按复杂度缩放投入**：lead 第一轮规划时先评估 query 复杂度，据此选用的 subagent 数（≤ `per_round_breadth` 上限）与预计轮数（≤ `max_rounds` 上限）。简单题 1-2 个 worker、1 轮即收；复杂题才铺满。`per_round_breadth` 由「固定值」语义改为「每轮上限」。
2. **开跑前快速澄清范围**：lead 在产出 plan.md 前，若 topic 有歧义/范围过宽，先向用户一句话确认调研角度/边界（非阻塞，用户不答则按合理默认继续）。
3. **subagent 任务契约四要素**：派 worker 时的契约 MUST 含 ①目标 ②输出格式 ③工具/源指引 ④边界（缺任一会 drift）。
4. **综合阶段显式找矛盾**：报告交叉多源时 MUST 标出冲突/分歧的结论（不只罗列），并指明哪些已循证复核、哪些存疑。
5. **轮间 interleaved thinking**：每轮结束后 lead MUST 显式评估「已覆盖什么 / 还缺什么 / 下一轮该补哪个角度」，再决定继续或收敛。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `deep-search`：新增 #1/#3/#4/#5 + 「plan.md 写假设范围」（ADDED）。均在现有 locked 需求（max_rounds 上限、plan.md、并行派发、双格式报告、traces）之内增量，不修改 locked 需求本身。
- `orchestration`：新增 #2「主 agent 派 deep-search 前对明显歧义做非阻塞澄清」（ADDED）——因 deep-search 是 subagent 跑起来不能与用户交互，澄清须在主 agent 派发前做。

## Impact

- **代码/产物**：主要改 `agents/deep-search.md`（subagent prompt：复杂度评估、澄清、契约四要素、找矛盾、轮间思考）+ `commands/search-deep.md`（lead 闭环）；`defaults/limits.yaml` 给 `per_round_breadth` 注释改为「每轮上限」语义（值不变）。
- **行为**：简单题更省（少 worker/少轮）；复杂题质量更高（契约清晰、找矛盾）。max_rounds / per_round_breadth 仍是硬上限。
- **测试**：行为以 prompt 为主，难单测；以 `tests/MANUAL.md` 补几条人工验证项为主。
- **向后兼容**：现有 deep-search 流程结构不变（仍 plan.md → 并行轮次 → 双格式报告 + traces），5 项是增量。
- **成本**：缩放 + 澄清降低简单/错方向的浪费；找矛盾/契约略增单轮 token，但提质。
