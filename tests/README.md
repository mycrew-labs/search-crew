# Search Crew Tests

零依赖 stdlib `unittest`，跑法（**在仓库根目录**执行）：

```bash
# 全套
python3 -m unittest discover -s tests -t . -p 'test_*.py' -v

# 单个文件
python3 -m unittest tests.test_yaml_parser -v
```

`-t .` 让 discover 走 `tests/__init__.py`，自动把 `skills/search-toolkit/scripts/` 加进
sys.path，让测试代码用 `from lib import ...` 直接 import 业务模块。

## 覆盖矩阵

下表把 [`tasks.md`](../openspec/changes/init-search-crew/tasks.md) 与 [`tasks.md`](../openspec/changes/add-usage-tracking/tasks.md) 的 TC-* 用例与本目录脚本对应。能在本地自动跑的标 **auto**，需要在 Claude Code runtime 内验证的标 **manual**（详见 [`MANUAL.md`](./MANUAL.md)）。

| TC | 来源 | 类型 | 测试 |
|---|---|---|---|
| TC-CMD-001 | init | manual | `MANUAL.md` |
| TC-AGENT-001 | init | manual | `MANUAL.md` |
| TC-AGENT-002 | init | manual | `MANUAL.md` |
| TC-AGENT-003 | init | mixed | adapter 注册自动；端到端 manual |
| TC-ROUTE-001 | init | manual | `MANUAL.md` |
| TC-FALLBACK-001 | init | mixed | search 脚本 fallback 自动；端到端 manual |
| TC-DATA-001 | init | manual | `MANUAL.md` |
| TC-OUTPUT-001 | init | auto | `test_output.py` |
| TC-MCP-001 | init | manual | `MANUAL.md` |
| TC-PARALLEL-001 | init | manual | `MANUAL.md` |
| TC-CONFIG-001 | init | auto | `test_seed.py` |
| TC-LEARN-001 | init | mixed | pending 文件扫描自动；hook 集成 manual |
| TC-UX-001 | init | manual | `MANUAL.md` |
| TC-EVIDENCE-001 | init | manual | `MANUAL.md` |
| TC-USAGE-001 | usage | auto | `test_finalize_usage.py` |
| TC-USAGE-002 | usage | auto | `test_finalize_usage.py` |
| TC-USAGE-003 | usage | auto | `test_pricing.py` |
| TC-USAGE-004 | usage | auto | `test_usage_cli.py` |
| TC-CONTEXT-001 | usage | manual | `MANUAL.md` |
