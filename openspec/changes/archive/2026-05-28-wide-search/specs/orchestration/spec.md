## REMOVED Requirements

### Requirement: 唯一显式搜索 slash command 是 /search-deep
**Reason**: 显式搜索命令不再唯一——新增 `/search-wide`（批量对照矩阵）与 `/search-fast`（通用快速调研）两个显式入口；由下方「显式搜索 slash command：/search-deep、/search-wide、/search-fast」取代。
**Migration**: `/search-deep` 行为不变；用户另获 `/search-wide`、`/search-fast` 两个新命令；fast-search 的语义自动触发老路径保留。

## ADDED Requirements

### Requirement: 显式搜索 slash command：/search-deep、/search-wide、/search-fast
系统 SHALL 提供三个用户显式触发的搜索 slash command：`/search-deep <主题>`（强制 deep-search 深度循环）、`/search-wide <批量对比需求>`（强制 wide-search 对照矩阵）、`/search-fast <主题>`（强制一次 fast-search 通用快速调研）。插件命名空间下分别为 `/search-crew:search-deep`、`/search-crew:search-wide`、`/search-crew:search-fast`。命令短名 MUST 用 `search-*` 前缀，避免占用 `/deep-search`、`/setup` 这类通用全局名。无显式命令时其余搜索场景 MUST 仍由对话语义自动判断派发。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-28

#### Scenario: 用户输入 /search-wide 跟批量对比需求
- **WHEN** 用户输入 `/search-wide 对比这 12 个开源推理框架的性能/许可证/活跃度`
- **THEN** 主 agent 派出 wide-search lead 处理该批量对照需求

#### Scenario: 用户输入 /search-fast 跟主题
- **WHEN** 用户输入 `/search-fast 当前最流行的开源向量数据库`
- **THEN** 主 agent 派出一个 fast-search subagent 做一次通用快速调研

#### Scenario: /search-deep 行为不变
- **WHEN** 用户输入 `/search-deep 调研开源 LLM 推理框架`
- **THEN** 主 agent 派出 deep-search subagent 处理该主题

#### Scenario: 不存在裸通用 /search
- **WHEN** 用户尝试 `/search ...`
- **THEN** Claude Code 报告该命令不存在；真正的命令是 `/search-deep`、`/search-wide`、`/search-fast`（或带 `/search-crew:` 命名空间）

### Requirement: 主 agent 路由「批量对比/分析 N 个同类对象」到 wide-search
主 agent 在无显式命令时，若对话语义识别为「对 N 个**同类对象**跑**同一套分析维度**、要对照结果」（如「对比这 15 个框架的 X/Y/Z」「调研这 20 家供应商的价格/SLA」），SHALL 自动派 wide-search，而非 fast-search 或 deep-search。单对象多角度深挖仍走 deep-search；单点查询仍走 fast/site-search。

#### Scenario: 语义识别批量对照需求
- **WHEN** 用户说「帮我对比这 10 个 Rust HTTP 框架的吞吐、生态、上手难度」（未用 slash 命令）
- **THEN** 主 agent 自动派 wide-search lead，而非把 10 个对象塞进一个 fast-search

#### Scenario: 单对象深挖不误派 wide-search
- **WHEN** 用户说「深入研究 vLLM 的调度器实现」（单对象）
- **THEN** 主 agent 派 deep-search 或 fast-search，不派 wide-search
