# Capability: orchestration

主 agent 在收到搜索类需求时的路由、派发、综合、回复闭环。

## 适用 P- 行为

- [P-CMD-001](../../USER_DESIGN.md) 触发方式
- [P-PARALLEL-001](../../USER_DESIGN.md) 并行派发与任务登记
- [P-UX-001](../../USER_DESIGN.md) 协作邀请
- [P-EVIDENCE-001](../../USER_DESIGN.md) 证据传递（主 agent 在最终回复中的强制保留）
- [P-ROUTE-001](../../USER_DESIGN.md) 循证四步（主 agent 也遵循）

## 行为描述

### 入口

1. 用户在对话中提到搜索意图 → 主 agent 按语义判断派 fast / site
2. 用户显式 `/deep-search <主题>` → 主 agent 强制派 deep
3. 不响应 `/search` 也不接受 `--site` 参数

### 派发前

1. 调 `TaskCreate` 建任务清单（任务描述面向用户）
2. 在 user-facing text 中输出协作邀请（💡 提示一行）
3. 同 turn 内若派多个 subagent，必须一次性发起多个 Task tool 调用

### 派发后

1. 等所有 subagent 返回
2. 调 `TaskUpdate` 标 completed
3. Read 各 subagent 产出目录的 INDEX.md（不通读全文件）
4. 按需 grep 关键词跳到具体 markdown 段落
5. 走 P-ROUTE-001 第三步：从非官方源得到的关键结论再派一个 site-search 复核（如适用）

### 最终回复

1. 给出结论 + 每段挂证据（URL + 必要时原文 / 数字）
2. 标注 pending 来源 / 未通过官方复核的结论
3. 告知产物目录路径，询问是否复制到项目目录
4. deep-search 场景：附「在浏览器打开 `report.html`」的命令（mac: `open`，linux: `xdg-open`）

## 不变量

- 日常搜索无需 slash command；唯一显式 command 是 `/deep-search`
- TaskCreate 必须在派发之前调，不许事后补
- 主 agent 不复述 subagent 内容；用自己的话综合，但证据必须挂回去
