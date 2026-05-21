# Capability: deep-search

跨多轮深度调研。派 fast-search / site-search 干活，自抓深挖允许，最终消化压缩成 HTML + Markdown 双格式报告。

## 适用 P- 行为

- [P-AGENT-001](../../USER_DESIGN.md) subagent 共性 + deep 特殊主交付物
- [P-AGENT-002](../../USER_DESIGN.md) 派活优先，自抓允许（含 OPEN-AGENT-002-A 已采纳方案 C）
- [P-ROUTE-001](../../USER_DESIGN.md) 循证四步（综合阶段对每条引用都套用）
- [P-DATA-001](../../USER_DESIGN.md) 调用语义：派 subagent 时必须把 traces 子目录路径传下去
- [P-OUTPUT-001](../../USER_DESIGN.md) report.html / report.md 双格式 + 保留底层产物
- [P-EVIDENCE-001](../../USER_DESIGN.md) 报告中每段结论挂证据
- [P-PARALLEL-001](../../USER_DESIGN.md) 每轮内同 turn 并行派发

## 行为描述

### 输入

- topic（调研主题完整描述）、可选 hint
- 模型：`claude-opus-4-7`

### 工作流（采纳 design.md 方案 C：清单 + 自评 + 硬上限）

#### 第一轮：规划

1. 把 topic 拆成研究计划：角度 + 子任务清单 + 每子任务的完成判据
2. 写 `deep-search/plan.md`
3. 第一批派发：每个子任务对应一个 fast-search 或 site-search subagent
4. 派发前 TaskCreate 建任务清单（任务描述面向用户）
5. 派发时把 `<deep-run-root>/deep-search/traces/<sub-name>-<sid>/` 作为目标目录传给下级

#### 第 N 轮（N ≥ 2）

1. Read 上一轮各 subagent 产出的 INDEX.md（不通读全文件）
2. 按需 grep 关键词跳到具体段落
3. 走 P-ROUTE-001 第三步：从非官方源得到的关键结论再派 site-search 复核
4. 按 plan.md 自评每个子任务是否 done（判据：内容充足 + 通过循证复核 + 新抓内容质量是否仍在提升）
5. 写 `deep-search/round-N.md`：本轮结论 + 自评结果
6. 决定是否继续：所有子任务 done OR 已达 max_rounds (5) → 进入综合阶段；否则派下一轮

#### 综合阶段

1. 写 `deep-search/report.md`（给主模型）：plan 骨架 + 各子任务结论 + 每段挂证据 anchor
2. 写 `deep-search/report.html`（给用户）：LLM 自由生成可视化形态，引用链接可点击
3. 两份必须语义等价
4. 若有未完成子任务，必须在两份报告显眼处标注
5. 更新 `deep-search/INDEX.md`：指向「用户先看 report.html，主模型先看 report.md」

### 输出

```
deep-search/
├── INDEX.md
├── plan.md
├── round-1.md, round-2.md, ...
├── report.html         # 用户主交付物
├── report.md           # 主模型主交付物
└── traces/             # 底层 fast/site 产物（保留可追溯）
    ├── fast-search-<sid>/
    └── site-search-<sid>/
```

### 配置

- `max_rounds` 硬上限默认 5，可由 `~/.config/search-crew/limits.yaml` 覆盖
- 自抓 fetch.py 允许直接调（已有 URL / 沿链接深挖），但禁止直接调 search.py 与 site_search.py（必须派 subagent）

## 不变量

- 第一轮必产 plan.md
- max_rounds 是硬上限，禁止无限循环
- 主交付物 = report.html + report.md 双格式，缺一不可，两版语义等价
- 派 subagent 时必须传 traces 子目录路径（避免产物散落）
- 直接抓页面（fetch.py）允许；自己拼 Jina / Serper 请求**禁止**
- 综合阶段不允许编造结论；未通过循证复核的内容必须标注

## 未来升级（不在首版）

- `--review-plan` 标记：plan.md 出来先回用户确认方向再启动（design.md 方案 B）
