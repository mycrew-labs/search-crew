# Capability: search-toolkit

供 subagent 调用的搜索 / 抓取 / 站点 API / 路由 / 产物组织工具包，Python 实现，stdlib 优先零依赖。

## 适用 P- 行为

- [P-FALLBACK-001](../../USER_DESIGN.md) API key 可选，未配置返回 fallback marker
- [P-DATA-001](../../USER_DESIGN.md) / [P-OUTPUT-001](../../USER_DESIGN.md) 产物组织（wiki INDEX、ranking、关键词、附件 hash）
- [P-ROUTE-001](../../USER_DESIGN.md) 路由起点表落地（ROUTING.md + routing.yaml）
- [P-CONFIG-001](../../USER_DESIGN.md) 运行时仅读 active 配置
- [P-LEARN-001](../../USER_DESIGN.md) Stop hook 入口
- [P-AGENT-003](../../USER_DESIGN.md) 站点适配器实现 + 用户扩展点
- [P-EVIDENCE-001](../../USER_DESIGN.md) EvidenceWriter 提供 anchor 写盘契约

## 行为描述

### 入口脚本

| 脚本 | 职责 | 输出 |
|---|---|---|
| `search.py` | 通用搜索（Jina / Serper / WebSearch fallback） | JSON `{ results, backend, fallback }` |
| `fetch.py` | URL → markdown（Jina Reader / WebFetch fallback） | `{ url, markdown, source }` 或 `WEBFETCH_FALLBACK` |
| `site_search.py` | 站点搜索（API 适配器优先；`--list-adapters` 列出） | JSON `{ results, adapter, fallback }` |
| `check_backends.py` | 报告所有 backend / Chrome / MCP / `~/.config/search-crew/` 状态 | JSON |
| `seed_user_config.py` | 首次拷贝 defaults 到 `~/.config/search-crew/`，幂等 + flock | exit 0 |
| `stop_hook.py` | Stop 事件触发，扫 pending 输出提示 | hook 消息 |

### Lib

| 模块 | 职责 |
|---|---|
| `lib/__init__.py` | `BackendError`、`normalize_result`、`emit`、`env` |
| `lib/_http.py` | stdlib `urllib` JSON / text 封装，统一超时、错误分类 |
| `lib/jina.py` | Jina Search + Reader |
| `lib/serper.py` | Serper.dev，含中英文自动识别 |
| `lib/sites/__init__.py` | 注册表 + Algolia 索引清单 |
| `lib/sites/{github,mdn,algolia,readthedocs,pypi,npm}.py` | 站点适配器 |
| `lib/sites/_yaml_adapter.py` | YAML 驱动的配置型适配器（用户态零代码扩展） |
| `lib/config.py` | `load_active_config()` / `load_pending()` |
| `lib/runtime.py` | `get_session_id()` 按 T-SESSION-001 优先级 |
| `lib/output.py` | `EvidenceWriter` + INDEX.md 模板 + 关键词头部 + 附件 hash 写盘 |

### 路由

- `ROUTING.md` 用人类可读 markdown 描述循证四步（不允许 AI 自行放宽）+ 路由起点表（AI 可在 TECH 层迭代）
- `defaults/routing.yaml` 是程序化等价版（subagent 读这份）
- 用户改 `~/.config/search-crew/routing.yaml` 覆盖 defaults
- 新发现的路由由 AI 写到 `~/.config/search-crew/pending/routing/`

### 失败约定

| 情形 | 行为 |
|---|---|
| Backend HTTP 错误 | 抛 `BackendError`，进程退出 1，stderr 写说明 |
| 无可用 backend（key 全空 + 内置 fallback 也不可达） | 进程退出 0，stdout `{ "fallback": "WEBSEARCH_FALLBACK" }` |
| 站点适配器 miss | 进程退出 0，stdout `{ "adapter": null, "hint": "use fetch or MCP" }` |

## 不变量

- 全部入口脚本使用 Python 3.13 stdlib，不引入第三方依赖（含 `requests`）
- JSON 结构所有 backend 一致：`{ title, url, snippet, extra }`
- runtime **永不**直接读 plugin 内置 `defaults/`（除 seed 时）；只读 `~/.config/search-crew/`
- 用户态自定义适配器加载顺序：plugin 内置代码型 → 用户态代码型 → 用户态 YAML 配置型，同 host 后者覆盖前者
