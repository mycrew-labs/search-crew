## ADDED Requirements

### Requirement: deep-search 按复杂度缩放投入（在 caps 内）
deep-search 第一轮规划时 MUST 在 `plan.md` 顶部显式记一行**复杂度评估 + 投入决策**（用几个 worker、预计几轮），并据此选用 worker 数与轮数。worker 数 MUST ≤ `~/.config/search-crew/limits.yaml` 的 `deep_search.per_round_breadth`（该值语义为**每轮上限**，非固定值）；轮数 MUST ≤ `deep_search.max_rounds`。简单题 MUST 用更少 worker / 更少轮（不铺满）；复杂题才铺满。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-28

#### Scenario: plan.md 含复杂度评估与投入决策
- **WHEN** deep-search 收到 topic 产出 plan.md
- **THEN** plan.md 顶部含一行形如「复杂度：中等 / 本轮 3 个 worker / 预计 2 轮」的评估，且实际 worker 数 ≤ per_round_breadth、轮数 ≤ max_rounds

#### Scenario: 简单题不铺满
- **WHEN** topic 较简单（单一主题中等深度）
- **THEN** deep-search 用 1-3 个 worker、1-2 轮即收，不必用满 per_round_breadth 或跑到 max_rounds

### Requirement: deep-search 把本次假设的调研范围写进 plan.md
deep-search MUST 在 `plan.md` 顶部写明**本次假设的调研范围 / 角度**（如「本次按 X 范围调研，如需调整请说」），使范围始终可见、可被上级或用户中途纠偏。（开跑前的主动澄清由主 agent 在派发前做，见 orchestration capability。）

#### Scenario: plan.md 顶部声明假设范围
- **WHEN** deep-search 收到 topic 产出 plan.md
- **THEN** plan.md 顶部含一段「本次假设范围 / 角度」声明

### Requirement: deep-search 派 worker 时给出任务契约四要素
deep-search 派 fast/site-search 时，Task prompt MUST 含四要素，缺任一视为缺陷：①目标（要回答的子问题）②输出格式（产物形态，按既有产物约定）③工具/源指引（起点路由 + routing 硬规则）④边界（不越界到别的子任务、不多轮、命中权威主题回信号）。

#### Scenario: 派发 prompt 四要素齐全
- **WHEN** deep-search 派一个 fast-search 跑某子任务
- **THEN** 该 Task 调用的 prompt 含明确的 目标 / 输出格式 / 工具源指引 / 边界 四部分

### Requirement: deep-search 综合阶段显式标注源间矛盾与循证状态
deep-search 综合 report.md / report.html 时，跨多源得到的结论若存在**冲突 / 分歧**，MUST 显式标出（指明哪个源说什么），MUST NOT 偷偷只选一个而不提分歧。每条关键结论 MUST 标注循证状态：已回官方源复核 / 未复核存疑（沿用循证四步第 4 步）。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-28

#### Scenario: 多源分歧被标出
- **WHEN** 两个来源对同一指标给出冲突数据
- **THEN** 报告显式呈现「⚠️ 分歧：源 A=X，源 B=Y」，而非只取其一

#### Scenario: 结论标循证状态
- **WHEN** 报告陈述一条来自非官方源的关键结论
- **THEN** 该结论标注「未在官方源验证」或「已复核」

### Requirement: deep-search 每轮做显式 gap 评估再决定下一步
deep-search 每轮写 `round-N.md` 时，除「派了什么 / 收了什么 / 子任务 done 自评」外，MUST 加一段显式 gap 评估：已覆盖什么、还缺什么、下一轮补哪个角度（或判定已够、进入综合）。该评估 MUST 作为「继续派下一轮 vs 收敛」的依据。

#### Scenario: round-N.md 含 gap 评估
- **WHEN** deep-search 完成第 N 轮
- **THEN** round-N.md 含「已覆盖 / 还缺 / 下一轮补哪个角度（或进入综合）」段，且下一步决策与该评估一致
