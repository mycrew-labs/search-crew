# 扩展 Search Crew

## 三种常见扩展

### 1. 新增通用搜索 backend（如 Brave Search / Tavily）

适合：你想接入一个新的"通用搜索引擎"类型 API。

步骤：

1. 在 `skills/search-toolkit/scripts/lib/` 加新模块（如 `brave.py`），仿照 `jina.py` / `serper.py` 写：
   - `is_available()` 检查环境变量
   - `search(query, *, max_results, language) -> list[normalize_result]`
   - 所有 HTTP 请求经 `lib/_http.py` 的 `request_json` / `request_text`（含 `backend=`、`endpoint=` 用于打点）
2. 改 `scripts/search.py` 把新 backend 加入路由（`--prefer` 选项 + 默认顺序）
3. 在 `defaults/pricing.yaml` 加单价表
4. （可选）在 `.env.example` / README 文档化新环境变量

### 2. 新增站点适配器（用户态，不动 plugin）

**推荐方式**——零侵入，跟随 plugin 升级不丢失。

#### 方式 A：YAML 配置型（零代码）

适合：站点搜索是简单的 `GET https://site.com/search?q=...` + 静态 HTML 列表。

在 `~/.config/search-crew/adapters/<site>.yaml`：

```yaml
site: example.com
search_url: "https://example.com/search?q={query}"
result_selector:
  list: ".result-item"        # 每条结果的 CSS class
  title: "h3 a"               # 在每条 list 内查标题
  url: "h3 a@href"            # @href 取属性
  snippet: ".excerpt"
```

selector 子集见 `lib/sites/_yaml_adapter.py` 注释。复杂站点用方式 B。

#### 方式 B：代码型（Python）

适合：需要认证 / 分页 / JSON API / 复杂解析。

在 `~/.config/search-crew/adapters/<name>.py`：

```python
"""复制 / 改写自 https://github.com/<某人的现成实现>，遵守原仓库 LICENSE。"""

from typing import Any

SITE = "example.com"


def search(query: str, max_results: int = 10, **_: Any) -> list[dict[str, Any]]:
    # ... 你的实现
    return [
        {"title": "...", "url": "...", "snippet": "...", "extra": {...}},
        ...
    ]
```

**强建议**（USER_DESIGN P-AGENT-003）：动手写前**先**去 GitHub / 搜索引擎查现成实现，参照而不是闭门造车。

### 3. 新增站点适配器（plugin 内置）

需要：你的适配器对所有 Search Crew 用户都有价值，想随 plugin 分发。

步骤：

1. 在 `skills/search-toolkit/scripts/lib/sites/` 加模块（`SITE = "<host>"` + `search(...)`）
2. 在 `lib/sites/__init__.py` 的 `BUILTIN_REGISTRY` 注册
3. 写测试 → PR

如果是 Algolia DocSearch 站点：

1. 在浏览器开发者工具抓站点的 `app_id` / `api_key` / `index_name`
2. 加进 `lib/sites/__init__.py` 的 `ALGOLIA_INDEXES`
3. 不需要写代码

## 未来候选 backend / 适配器（B-005 之后）

不在当前 change 范围内，欢迎以后单起 change 加入：

- arxiv（学术）
- semantic-scholar
- google-patents
- clinicaltrials.gov
- pubmed
- HackerNews（Algolia）
- 知乎（间接，需走浏览器 MCP）

## 修改路由起点

直接改 `~/.config/search-crew/routing.yaml`：

- 加 / 删主题
- 把 hard_rule: true 关掉（变成强建议）
- 调主题对应的起点站

升级 plugin 不影响。

## 修改 cost 单价

直接改 `~/.config/search-crew/pricing.yaml`。`last_updated` 字段记得顺手改。

## 自定义 subagent 上限

`~/.config/search-crew/limits.yaml`：

- `deep_search.max_rounds`：deep-search 最多跑几轮
- `deep_search.per_round_breadth`：每轮并行派几个
- `fast_search.max_results`：每次抓多少结果
- 等

## 写新 OpenSpec change

任何会改变对外行为的扩展（新 P-* 行为、改变 USER_DESIGN）都建议走 OpenSpec：

1. `openspec/changes/<change-id>/proposal.md`：动机、范围、非目标
2. `openspec/changes/<change-id>/USER_DESIGN.md`：新 P-* 行为台账（**需用户确认**）
3. `openspec/changes/<change-id>/TECH.md`：技术决策 T-*
4. `openspec/changes/<change-id>/design.md`：临时设计推演
5. `openspec/changes/<change-id>/tasks.md`：执行 + 验证清单
6. `openspec/changes/<change-id>/capabilities/<name>/spec.md`：能力 spec

参考已有的 `init-search-crew` / `add-usage-tracking` 两个 change 的目录结构。
