# Capability: browser-control

封装 chrome-devtools-mcp 的使用最佳实践，作为 site-search 的兜底能力指南。

## 适用 P- 行为

- [P-AGENT-003](../../USER_DESIGN.md) 浏览器是 site-search 的最后手段
- [P-MCP-001](../../USER_DESIGN.md) plugin 自带 chrome-devtools-mcp

## 行为描述

本能力以 skill 形态提供（`skills/browser-control/SKILL.md`），不含独立脚本，仅约束 site-search 在使用 `mcp__chrome-devtools__*` 工具时的行为模式。

### 何时启用

仅以下场景启用：

1. `site_search.py` 报告"此站点无适配器"
2. 目标站点是 SPA，搜索结果靠 JS 异步加载
3. URL 不可直接 deep link
4. 需要模拟用户交互（点击、滚动加载）

否则**必须**走 API 适配器或 `fetch.py`。

### 浏览器连接策略

- 优先用独立 Chrome profile（不污染用户日常浏览）
- Chrome 136+ 启用 remote debugging 时**必须**指定 `--user-data-dir`（chrome-devtools-mcp 官方安全约束）
- 不打开有敏感数据的站点
- 任务结束后必须调 close 工具释放资源

### 搜索任务的标准工作流

1. 打开站点首页（不直接到搜索 URL，SPA 可能需要 hydration）
2. 等待 accessibility tree 稳定
3. 通过 aria-label / placeholder / role="searchbox" 定位搜索框
4. 输入并触发，等待结果加载（注意防抖）
5. 读取 accessibility tree（**不要**靠截图让 LLM 看）
6. 跟进 top N 结果：每个用 navigation 跳转 + 抓内容
7. 抓到的内容仍走 `output.py` 写入 `site-search/site-search-NNN.md`

### 反模式

- 不绕过 robots.txt / 速率限制
- 不尝试登录用户未授权的站点
- 不 bypass anti-bot 验证码
- 不打开未在任务范围内的 URL
- 不同时开多个浏览器实例（一次只一个）

## 不变量

- 默认禁用，仅在 site-search 显式降级判断下启用
- 任务结束后必须释放浏览器资源
