# Capability: site-search

在指定官方站点内的精确搜索。API 优先、浏览器兜底；承担循证四步中的「回官方源复核」职责。

## 适用 P- 行为

- [P-AGENT-001](../../USER_DESIGN.md) subagent 共性
- [P-AGENT-003](../../USER_DESIGN.md) API 优先 / 浏览器兜底 + 新适配器先查 GitHub
- [P-ROUTE-001](../../USER_DESIGN.md) 循证四步（site-search 是「第一步起点搜」和「第三步回官方源复核」的主力执行者）
- [P-DATA-001](../../USER_DESIGN.md) / [P-OUTPUT-001](../../USER_DESIGN.md) 产物组织
- [P-EVIDENCE-001](../../USER_DESIGN.md) 证据准备
- [P-MCP-001](../../USER_DESIGN.md) chrome-devtools-mcp 兜底

## 行为描述

### 输入

- query、site（域名）、可选 verify 标记（说明本次任务是循证复核）、可选 target 目录
- 模型：`claude-sonnet-4-6`

### 工作流（三级降级）

1. **API 适配器**（首选）：
   - 跑 `python3 site_search.py --site <site> --query <q>` 命中适配器走 API
   - 适配器清单查 `~/.config/search-crew/adapters/` + plugin 内置
2. **固定 URL 模式**：
   - 适配器 miss → 用 `fetch.py` 抓 `https://<site>/search?q=<q>` 等可推断的搜索 URL
3. **Chrome DevTools MCP**（兜底）：
   - 上两条都不行才动用 `mcp__chrome-devtools__*`
   - 适用：SPA / JS 异步 / 需要登录 / URL 不可 deep link

### 复核场景（来自 P-ROUTE-001 第三步）

- 调用方传 `verify=true` + 待复核的关键结论
- site-search 在官方站搜该结论 → 找到 → 标 "verified"；未找到 → 标 "not-in-official-source"
- 返回结果显式声明该结论的官方状态

### 新适配器实现策略

任何首次接触的站点，先：

1. GitHub 搜 `<site> api / scraper / wrapper`
2. fast-search 搜博客教程
3. 找到现成参考后改写 / 缝合
4. 没有再自己猜

参照他人代码 MUST 在适配器文件顶部注明来源 + 改写程度。

### 输出

- `site-search/site-search-NNN.md`：每条命中结果的抓取内容 + 关键词头部 + evidence anchor
- `site-search/INDEX.md`：wiki 大纲（含每条 verify 状态）
- `attachments/<hash>.<ext>`

## 不变量

- 浏览器是最后手段，跳过前两级视为缺陷
- robots.txt 与速率限制 MUST 遵守
- 复核场景必须给出明确的 verified / not-in-official-source 状态
