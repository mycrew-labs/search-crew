## 1. deep-search subagent prompt（agents/deep-search.md）

- [x] 1.1 第一轮规划段加「复杂度评估 + 投入决策」：plan.md 顶部写一行（复杂度 / 本轮 worker 数 / 预计轮数），按 Anthropic 缩放规则（简单 1-2 worker·1 轮 → 复杂铺满·至 max_rounds），worker 数 ≤ per_round_breadth、轮数 ≤ max_rounds
- [x] 1.2 plan.md 顶部加「本次假设调研范围 / 角度」声明（可中途纠偏）
- [x] 1.3 派 worker 段补「任务契约四要素」模板：目标 / 输出格式 / 工具源指引（含 routing 硬规则）/ 边界
- [x] 1.4 综合阶段段加「显式找矛盾」：跨源冲突 MUST 标出（⚠️ 分歧：源 A=X，源 B=Y）+ 每结论标循证状态（已复核 / 未复核存疑）
- [x] 1.5 每轮 round-N.md 段加「gap 评估」：已覆盖 / 还缺 / 下一轮补哪个角度（或进入综合），并作为继续 vs 收敛的依据

## 2. 主 agent 闭环（commands/search-deep.md）

- [x] 2.1 派 deep-search 前加「明显歧义 → 一句话非阻塞澄清（含默认）」步骤；清晰 topic 默认静默不问

## 3. 配置注释（defaults/limits.yaml）

- [x] 3.1 `deep_search.per_round_breadth` 注释从「每轮派几个」改为「**每轮上限**」（值不变，lead 按复杂度选 ≤ 它）

## 4. 文档 / 人工验证

- [x] 4.1 `tests/MANUAL.md` 补人工验证项：plan.md 含复杂度评估 + 假设范围；派发 prompt 四要素；报告标分歧 + 循证状态；round-N.md 含 gap 评估；歧义 topic 主 agent 先问
- [ ] 4.2 （可选）README / EXTENDING 提一句 deep-search 现在按复杂度缩放 + 找矛盾（如对外行为值得说明）

## 5. 归档前：锁确认 gate（按 change-flow 规则）

- [x] 5.1 `openspec validate deep-search-research-upgrades --strict` 通过
- [x] 5.2 完工简报：拟加锁清单（这 6 条新需求里哪些是你拍板要固化的）+ 本次未改任何已 locked 需求（全 ADDED）逐条跟你确认
- [x] 5.3 用户确认 → 落锁（复杂度缩放 / 派发前澄清 / 找矛盾 三条 user-confirmed）→ `openspec archive deep-search-research-upgrades`
- [ ] 5.4 **manual** · reload 后实测：跑一个简单 topic（看是否少 worker/少轮）+ 一个歧义 topic（看主 agent 是否先问）+ 一个对比 topic（看报告是否标分歧）
