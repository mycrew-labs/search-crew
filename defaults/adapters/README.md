# 用户自定义站点适配器

本目录在首次安装时为空。你可以在这里加自己的适配器：

## 配置型（YAML，零代码）

```yaml
# example.com.yaml
site: example.com
search_url: "https://example.com/search?q={query}"
result_selector:
  list: ".result-item"        # CSS 选择器
  title: "h3 a"
  url: "h3 a@href"
  snippet: ".excerpt"
```

由 `lib/sites/_yaml_adapter.py` 通用驱动。适合简单的静态搜索页。

## 代码型（Python）

```python
# example_com.py
SITE = "example.com"

def search(query: str, max_results: int = 10, **_):
    """返回 normalize_result(...) 列表。"""
    ...
```

适合需要复杂逻辑（认证 / 分页 / JSON API）的站点。

## 加载优先级

```
plugin 内置代码型适配器
    → 用户态代码型（本目录 *.py）
    → 用户态 YAML 配置型（本目录 *.yaml）
```

同 host 后者覆盖前者。

## 实现新适配器时

按 USER_DESIGN P-AGENT-003 的强建议：

1. 先去 GitHub 搜对应站点的现成抓取实现
2. 同时用 fast-search 搜博客 / 教程上的查询模式
3. 找到参考实现后改写 / 移植
4. 没有现成参考时再自己猜接口

参照他人代码请遵守源仓库许可证；适配器顶部注释里 SHOULD 注明来源 + 改写程度。
