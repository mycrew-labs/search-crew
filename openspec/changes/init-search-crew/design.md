# Design · init-search-crew

> 本文件用于临时设计推演、备选方案对比、open issue 展开。归档后**不**保留——保留下来的内容应已沉淀进 TECH.md / capabilities/<name>/spec.md。

## OPEN-AGENT-002-A ：deep-search 研究边界判定

### 问题

deep-search 怎样算「研究完了」？现在没有干净的答案。需要一个既能确定性结束、又不过早 / 不无限循环的判定。

### 三种候选方案

#### 方案 A：纯清单驱动（OpenAI Deep Research 模式）

deep-search 第一轮先产出**研究计划清单**（角度 + 子任务），后续轮次都在完成清单。所有项目都至少有产物 → 结束。

- ✅ 边界最清楚；可视化好（可以告诉用户「还差 3 项」）
- ✅ 计划清单天然成为 `report.md` 的骨架
- ⚠️ 第一轮规划质量很关键，规划错了后续会被锁死
- ⚠️ 不能在过程中发现"原问题问错了"时主动重新规划（除非显式允许）

#### 方案 B：清单 + 用户确认

方案 A 加一步：清单产出后**先回到用户确认方向**，确认后才启动 research。

- ✅ 用户对边界完全可控；解决「规划错了」的兜底
- ✅ 让 `/deep-search` 自然变成双阶段（规划 / 执行），用户可以中途停手
- ⚠️ 增加一次交互回合；纯自动场景（如 deep-search 被 agent 间接调用）需要"无人值守模式"
- ⚠️ 计划评审本身也消耗 token / 时间

#### 方案 C：清单 + 自评 + 硬上限

方案 A 加：

- 每个子任务由 deep-search 自评是否已完成（够不够 / 新内容质量是否太低 / 已达预设深度）
- 整体加 `max_rounds` 硬上限（如 5 轮）兜底

- ✅ 兼顾确定性与灵活性
- ✅ 跟 P-ROUTE-001 循证流程自然契合（每子项都跑完循证算 done）
- ⚠️ 自评质量难以校验（LLM 可能"自我感觉良好"提前 done）

### 推荐与备用

**首版推荐方案 C**，理由：

- 不增加用户交互（保留无人值守能力）
- 自评 + 硬上限是工程上最稳的兜底组合
- 跟 P-ROUTE-001 的循证四步可以直接挂钩（一个子任务"done"的定义之一 = 该子任务已通过循证复核）

**未来升级到方案 B**：等用户用过几轮，知道 `/deep-search` 在什么场景下规划老出错时，再加一个 `--review-plan` 标记走 B 路径。

实现期需要写进 `agents/deep-search.md` prompt 的内容：

- 第一轮强制产出 `deep-search/plan.md`（结构：每个子任务一行 + 完成判据）
- 每轮末尾扫描 plan.md，按子任务自评打勾
- `max_rounds = 5` 硬上限（可由 `~/.config/search-crew/limits.yaml` 覆盖）
- 报告产出时若有未完成子任务，必须在报告显眼处标注

> 本方案在 capabilities/deep-search/spec.md 落地。OPEN-AGENT-002-A **关闭**为「采纳方案 C」。

## HTML 报告"在浏览器打开"的提示形态

P-OUTPUT-001 已锁定「HTML 由 LLM 自由生成」。这里只决定**报告产出后怎么告诉用户**。

候选：

- **A**：主 agent 在最终回复里附一行 `open <abs-path>`（mac）/ `xdg-open <abs-path>`（linux）
- **B**：plugin 自带 `scripts/open_report.py`，主 agent 提示用户跑 `python3 ... open_report.py <run_id>`
- **C**：主 agent 文本中给一个 `file://` 链接，用户自己点（取决于 Claude Code 终端 / IDE 渲染）

**采纳 A**：最低复杂度，跨平台命令分支由主 agent 按 `uname` / `$OSTYPE` 自己决定（在 `/deep-search` 命令的 prompt 中说明）。

## 多 subagent 并行的失败处理

P-PARALLEL-001 要求同 turn 并行派发。失败情形：

1. **个别 subagent 失败**：主 agent 收完返回后，把失败 subagent 标到 TaskUpdate 的 description，决定是否补派 / 跳过 / 询问用户
2. **全部失败**：主 agent 必须在最终回复里如实告知，**不允许编造结果**
3. **超时**：首版不设 subagent 维度超时（Claude Code Task tool 自带），仅在 deep-search `max_rounds` 兜底

实现层不引入额外的 fail-fast / retry 机制；首版以 prompt 约束为主。

## 附件 hash 冲突边界

T-ATTACH-001 用 `sha256[:12]`。理论冲突概率：单 run 内 1 万附件碰撞概率约 `10^4 * 10^4 / 2^96 ≈ 10^-21`，完全可忽略。

不做防御性 fallback；如果未来真出现碰撞，按 bug 处理。

## defaults 拷贝时机的边界

T-SEED-001 说 plugin 安装 hook + 运行时入口都可触发拷贝。竞争情况：

- 用户 plugin 装好之前自己手动建了 `~/.config/search-crew/`（罕见，但要兼容）
- 多个 subagent 并发首次启动（首次安装即跑多 subagent）→ 需要文件锁

**采纳**：

- `seed_user_config.py` 用 `os.makedirs(..., exist_ok=True)` + 文件级 `flock` 防并发
- 已存在的子文件**永不**覆盖（`if not exists then copy`）
- plugin hook 触发时先跑一次 seed；运行时入口在 `load_active_config()` 入口处兜底再跑一次（幂等）

## Stop hook 与 Claude Code hook 体系

T-PENDING-001 假设 Stop hook 输出会被 Claude Code 注入下一轮上下文。具体协议（hook JSON 格式 / 输出位置）依赖 Claude Code 当前版本。

实现时需要：

1. 实际跑通本机 Claude Code 的 Stop hook 写一个 hello-world，验证 stdout 是否会被注入下一轮上下文
2. 如果协议变化，更新 `scripts/stop_hook.py` 与 plugin.json / settings.json hook 注册方式
3. 兜底：哪怕 hook 协议不通，用户也可以手动调 `/search:review-pending`（不计入 USER_DESIGN，仅作为兜底）

这块在 tasks.md 里挂一个验证项。

## 模型选择（默认）

USER_DESIGN 只说「轻量级 / 旗舰级」。具体落到模型名：

- `fast-search` → `claude-haiku-4-5-20251001`（轻、快、成本低）
- `site-search` → `claude-sonnet-4-6`（中等成本，需要复杂判断 API 路径）
- `deep-search` → `claude-opus-4-7`（最强综合 / 报告）

写到 agents/*.md 的 frontmatter `model:` 字段。后续可由用户在 active config 改 alias。
