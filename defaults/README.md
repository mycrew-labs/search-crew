# Search Crew · Defaults

本目录在 plugin **首次安装**时被一次性拷贝到 `~/.config/search-crew/`，作为用户态 active 配置的种子。

之后 plugin 升级 **不会**覆盖 active 配置。用户对 `~/.config/search-crew/` 拥有完全所有权——可改 / 关 / 替换 / 加任何内容。

详见 [USER_DESIGN P-CONFIG-001](../openspec/changes/init-search-crew/USER_DESIGN.md)。

## 内容

| 文件 | 用途 |
|---|---|
| `routing.yaml` | 循证路由的起点表（参考 P-ROUTE-001 主题清单） |
| `pricing.yaml` | 各 backend 估算单价表（参考 P-USAGE-003） |
| `limits.yaml` | 各 subagent 上限（如 deep-search max_rounds） |
| `adapters/` | 用户自定义站点适配器（首版为空，可加 `*.py` 或 `*.yaml`） |

## 想看新版 defaults

直接 cd 进 plugin 仓库的 `defaults/` 即可。plugin 不提供 diff / adopt 之类命令——用户主动看，主动改 active。

## 备份建议

**强烈建议**把 `~/.config/search-crew/` 放到 iCloud / Dropbox / 你自己的 dotfiles 仓库（原位置改成软链接），或者定期手动备份。否则一旦本地丢失，你长期沉淀的偏好就找不回来了。
