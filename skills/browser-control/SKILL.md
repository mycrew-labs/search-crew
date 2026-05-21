---
name: browser-control
description: Search Crew 通过 Chrome DevTools MCP 控制浏览器的最佳实践。site-search 在 API 适配器搞不定时降级到本 skill。
---

# Browser Control

本 skill 整合 chrome-devtools-mcp 的官方使用建议，供 site-search 在浏览器操作场景参考。

## 何时启用

仅以下情况启用 `mcp__chrome-devtools__*` 工具：

1. `site_search.py` 报告"此站点无适配器"
2. 目标站点是 SPA，搜索结果靠 JS 异步加载
3. URL 不可直接 deep link 到结果页
4. 需要模拟用户交互（点击、滚动加载、关闭弹窗后才能搜索）

否则**必须**优先 API 路径——更快、更稳、更省 token。

## 浏览器连接策略

chrome-devtools-mcp 自带最佳实践，但需注意：

- 优先用**独立 Chrome profile**（不污染用户日常浏览）
- Chrome 136+ 启用 remote debugging 时**必须**指定 `--user-data-dir`（chrome-devtools-mcp 官方安全要求）
- **不**打开有敏感数据的站点
- 浏览器实例的 cookies / localStorage 会被 MCP 读取，需谨慎处理
- 任务结束后**必须**调 close 工具释放资源

## 工具集（chrome-devtools-mcp 提供）

按职责粗分（具体工具名以 `chrome-devtools-mcp@latest --help` 输出为准）：

### 导航与页面状态

- 打开 URL、前进后退、等待加载完成
- 截图、读取 DOM、读取 accessibility tree

### 交互

- 点击元素、填表、提交、键盘输入
- 滚动、悬停、拖拽

### 检查

- 读取 console 消息、网络请求、performance trace
- 在页面上下文执行 JavaScript（用于绕过简单的 SPA 状态问题）

## 搜索任务的标准工作流

1. **打开站点首页**（**不**直接到搜索 URL，SPA 可能需要 hydration）
2. **等待页面就绪**（accessibility tree 稳定，而不是固定 sleep）
3. **定位搜索框**（优先用 `aria-label` / `placeholder` / `role="searchbox"`）
4. **输入查询并触发**（注意有些站点搜索框有防抖，要等结果加载）
5. **读取结果列表**（**用 accessibility tree**，不要靠截图让 LLM 看图——更精确）
6. **跟进 top N 结果**（每个用 navigation 跳转 + 抓内容，仍按 `output.py` 约定写盘）
7. **关浏览器**

## 反模式（不要做）

- 不绕过 robots.txt 或速率限制
- 不尝试登录用户未明确授权的站点
- 不 bypass anti-bot 验证码
- 不打开未在任务范围内的 URL
- 不同时开多个浏览器实例（一次只一个）
- 不靠截图让 LLM"看"页面（accessibility tree 更精确，且不占视觉 token）

## 错误处理

- 浏览器启动失败 → 返回明确错误，提示用户检查 Chrome 安装（参考 `check_backends.py`）
- 页面超时 → 单页操作硬上限 60 秒（见 `~/.config/search-crew/limits.yaml` 中 `site_search.browser_step_timeout_sec`）
- 元素找不到 → 把 accessibility tree snapshot 写到 site-search 产物里供主 agent 判断下一步

## 与 fetch.py 的边界

- 静态 HTML / 能直接 deep link 的页面：用 `fetch.py`（走 Jina Reader），**不要用 MCP**
- SPA / 需要交互 / 需要登录态 / URL 不可直接定位：才用 MCP

## 性能与资源

- 每次浏览器操作约 2-10 秒（远比 API 调用慢）
- 同时只开一个浏览器实例
- 任务结束**必须**调 close
- 浏览器抓的内容仍走 `lib/_http.py` 的打点钩子之外，自行用 `lib/usage.py:record(backend="chrome-devtools-mcp", endpoint="navigate", ...)` 打点（保持 cost summary 完整）
