---
name: search-wide
description: 启动一次广度调研。主 agent 派 wide-search lead，对 N 个同类对象跑同一套分析维度、并行派 worker，最终产出可排序对照矩阵（HTML + Markdown 双格式）。
---

## 用户主题

`{{args}}`

## 主 agent 工作流（作为 Leader）

### 1. TaskCreate 建任务清单

派 wide-search 之前先调 `TaskCreate`，描述面向用户：「广度调研（对照矩阵）：{{args}}」。

### 2. 协作邀请

向用户输出一行简洁、非阻塞的提示（真实显示给用户）：

> 💡 如果你已经明确要对比哪些对象、按哪几个维度，可以直接列出来，AI 会优先采用。

### 3. 派 wide-search lead

用 Task 工具派 `wide-search`，参数：

- `topic`：原样传 `{{args}}`
- `purpose`：如能从用户措辞推断更具体意图，加这一段
- `target_dir` 不传，让 wide-search 自己用 session-id 决定

注意：wide-search 会在**派 worker 前**把「对象清单 + 列 schema」抛回来要用户确认。如果它产出的确认请求出现在你这一层，原样转达给用户，等用户放行再让其继续——这是防「列错一次 ×N 亏」的关键闸。

### 4. 等返回

wide-search 会返回三行：

```
<run_root>/wide-search/report.html
<run_root>/wide-search/report.md
本次估算 ~$X.XXX USD（N 次调用 · ...）
```

记下 `<run_root>`（内部记，不写给用户）。

### 5. 阅读报告

Read `<run_root>/wide-search/report.md`（不读 HTML，HTML 是给用户看的）。

### 6. TaskUpdate 标 completed

### 7. 最终回复用户

三块：

**块 1：报告路径**（HTML 优先，因为矩阵可排序对比，HTML 更直观）

```
📄 对照矩阵（可视化版本，浏览器打开可按列排序对比）：
   open <run_root>/wide-search/report.html      # mac
   xdg-open <run_root>/wide-search/report.html  # linux
```

按 `uname` / `$OSTYPE` 给出对应平台命令。

**块 2：矩阵速读**（用你自己的话点出关键对照结论，**必须**附证据；标「未获取」的格如实说明，不编造）

**块 3：cost 一行总览**

```
📊 本次估算 ~$X.XXX USD（N 次调用 · M 个源 · K 次触发站点调用上限）
```

获取这一行最稳的方式：调

```bash
python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/finalize_usage.py <run_root> --one-line
```

**绝对不要**在回复里写出 `<run_root>` 路径、详细 cost 拆分。

### 8. 用户追问处理

与 search-deep 一致：追问明细 → Read `<run_root>/usage-summary.md` 按问题剪裁；追问历史总花费 → 提示用户跑 `! python3 $CLAUDE_PLUGIN_ROOT/skills/search-toolkit/scripts/usage.py --last 10`。

## 关键约束

- TaskCreate 必须在派发之前
- wide-search 派 worker 前的 schema 确认请求 MUST 转达用户，等放行
- 不复述矩阵全文；用你自己的话点结论 + 证据挂回
- cost 总览**只一行**，不附路径、不展开拆分
