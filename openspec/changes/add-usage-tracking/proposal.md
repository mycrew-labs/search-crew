# Proposal: 为 Search Crew 加入 API 调用统计

## 背景

`init-search-crew` 把 plugin 主体能力定了下来，但有一个用户可感知的盲点：**用了多少调用、估算花了多少钱**没人告诉用户。

- Jina / Serper 等 backend 都按调用量计费，用得多了账单会跳
- deep-search 一次跨多轮，单次调研可能消耗几十次后端调用，但用户事后回看完全看不到
- 即便不为了控成本，"我这次调研用了多少调用"本身也是用户视角的合理信息

来源：项目 Backlog B-005。

## 动机

- 让用户每次拿到调研产物时，能**直接**看到本次花了多少（次数 + 估算 cost）
- 让用户能跨 run 回看自己历史使用，便于自己控成本 / 复盘
- 让单价表对用户透明、可覆盖：plugin 内置一份基线，用户随时可在 `~/.config/search-crew/pricing.yaml` 改写

## 范围（In Scope）

1. **单 run 内打点 + 摘要**：每次 backend 调用打点到 `<run_root>/usage.jsonl`；run 结束时生成 `<run_root>/usage-summary.md`（人类可读）
2. **主 agent 回复只留指针**：不复述 cost 详情进 context，仅给一句"详见 ..."；详细 markdown 走落盘
3. **原始打点 + run 汇总永久持久化**（vibe-usage 风）：raw 数据复制到 `~/.local/state/search-crew/calls.jsonl` 与 `runs.jsonl`，永不自动清理；未来想做更细的统计，原始数据都在
4. **单价表可覆盖**：plugin 内置 `defaults/pricing.yaml`，首次安装拷贝到 `~/.config/search-crew/pricing.yaml`，运行时读 active；过时由用户改
5. **独立查询入口**：`scripts/usage.py` 由用户主动 `!` 前缀执行；输出不进任何 agent 的 context

## 非目标（Non-Goals）

- **不实现** deep-search `report.html` 内嵌 cost 可视化（留后续 change，scope ↑ 一档时再做）
- **不实现** 阈值告警 / 月度报告 / 邮件提醒（留后续 change）
- **不实现** 精确账单对账：cost 是按内置单价表的**估算**，允许与实际账单有误差（API 没有暴露真实计费时不主动查账单）
- **不实现** 跨多 key / 多账户的成本拆分
- **不实现** Stop hook 中显示 cost summary（如有需要走后续 change）
- **不实现** 主 agent 在回复中详细复述 cost 数字（明确反目标，为 context 卫生）
- **不存储**用户原始 query 字符串到 raw jsonl（隐私默认；如未来要存走新 change）

## 影响面

- 新增 P-USAGE-001 / 002 / 003 三条产品行为
- TECH 层需要：
    - 改 `lib/_http.py` 增加打点（写 `usage.jsonl`）
    - 改 `lib/output.py` 增加 cost summary 段
    - 新增 `lib/pricing.py`：单价表加载 + 估算
    - 改 `seed_user_config.py` 把 `pricing.yaml` 也纳入首次拷贝
    - 改各 subagent prompt：要求最终落盘前调 `EvidenceWriter` / 等价工具追加 cost summary
- 不引入新 backend，不动 routing / 适配器
- 不破坏 init-search-crew 已确定的任何约定

## 与 init-search-crew 的关系

本 change **依赖** init-search-crew 已建立的产物组织 / 配置生命周期 / subagent 工作流。两者可同步开发：

- 实现层先把 init-search-crew 的核心打通 → 在它的 lib 上加打点钩子（侵入很小）
- USER_DESIGN 层独立：本 change 的三条 P-USAGE-* 不与 init-search-crew 的 P-* 冲突
