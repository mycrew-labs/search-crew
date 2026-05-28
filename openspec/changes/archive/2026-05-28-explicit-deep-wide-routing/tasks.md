## 1. spec（已写 delta，归档时合并）

- [x] 1.1 orchestration：REMOVE+ADD 自动派发语义（casual→/search-fast、deep/wide 显式专属）+ REMOVE wide 自动路由
- [x] 1.2 deep-search：MODIFY「同 turn 并行」「传 target 目录」两条 locked 的 fast-search → evidence-search
- [x] 1.3 site-search：MODIFY「新适配器查现成」「产出 ranking 约定」「触发反例」三条的 fast-search → evidence-search / /search-fast

## 2. agent / 命令文档

- [x] 2.1 `agents/deep-search.md` / `agents/wide-search.md` description：明确「仅 /search-deep / /search-wide 显式触发，不被对话语义自动派发」
- [x] 2.2 `agents/site-search.md`：反例段 / 产物约定里的 fast-search → evidence-search；"无目标站 / 模糊探索" 反例指向 /search-fast，"跨多站综述" 指向 /search-deep
- [x] 2.3 README 三层入口：casual 查询行明确「自动到 /search-fast 快答」；deep/wide 标「显式」

## 3. 验证 + 归档

- [x] 3.1 `openspec validate explicit-deep-wide-routing --strict` 通过 + 全量 unittest
- [x] 3.2 grep 确认 live specs 无残留 worker 语义的 fast-search
- [ ] 3.3 完工简报：MODIFY orchestration「对话语义触发」+ deep「传 target」「同 turn 并行」locked、REMOVE wide 自动路由；逐条确认 → bump → archive → commit → push
