# Capability: config-lifecycle

`~/.config/search-crew/` 作为唯一 runtime 配置真相的全生命周期管理：seed、读取、pending 学习、Stop hook 提示、onboarding 备份引导。

## 适用 P- 行为

- [P-CONFIG-001](../../USER_DESIGN.md) 配置真相与生命周期 + onboarding 备份提示
- [P-LEARN-001](../../USER_DESIGN.md) Pending 学习区 + Stop hook 自动提示

## 行为描述

### 目录布局

```
~/.config/search-crew/
├── routing.yaml                          # 路由起点表，对应 defaults/routing.yaml
├── adapters/                             # 用户态适配器
│   ├── *.py                              # 代码型
│   └── *.yaml                            # 配置型
├── limits.yaml                           # 各 subagent 上限（如 deep-search max_rounds）
├── pending/
│   ├── routing/<timestamp>-<slug>.yaml
│   ├── adapters/<timestamp>-<slug>.yaml
│   └── _meta.json
└── backup-info.md                        # seed 时写入：备份建议 + 命令示例
```

### 生命周期

1. **首次安装**：`on-install.sh` 调 `seed_user_config.py`；如果 `~/.config/search-crew/` 不存在 → 把 plugin `defaults/` 整个拷贝过去；如果已存在 → 跳过
2. **运行时**：所有 subagent / skill 脚本调 `lib/config.py:load_active_config()`，永不直接读 plugin 内置 `defaults/`
3. **运行时兜底 seed**：`load_active_config()` 入口处检测目录是否存在，不存在则即时 seed（防止用户跳过 install hook）
4. **plugin 升级**：不动 active；defaults 仅作为参考，用户想看自己 cd 进 plugin 仓库

### Pending 学习

- AI 写新路由 / 新适配器候选 → `pending/{routing,adapters}/<timestamp>-<slug>.yaml`
- subagent 用到 pending 项时，产物里必须标注「来自 pending，未确认」
- Stop hook（`stop_hook.py`）扫 pending 数 N：
  - N > 0 → 输出提示给用户：「这次调研产生了 N 条候选规则，是否要……」
  - 用户回「晋升 / 丢弃 / 暂留」→ 主 agent 调对应工具完成

### Onboarding 引导

`/setup` 首次运行时**必须**醒目提示用户：

> `~/.config/search-crew/` 是你长期沉淀的配置。**强烈建议**：
> 1. 把它放到 iCloud / Dropbox / 你自己的 dotfiles 仓库，原位置改成软链接；或
> 2. 定期手动备份。
>
> 否则一旦丢失，你长期沉淀的偏好就找不回来了。

提示文本同步写入 `~/.config/search-crew/backup-info.md`（让用户随时能查）。

## 不变量

- runtime **永不**直接读 plugin 内置 defaults（seed 时除外）
- AI **永不**直接修改 active 内容；要建议改动 → 写 pending
- seed 是幂等的，多次触发不覆盖已有内容
- Stop hook 是 pending 晋升的**唯一**自动交互入口；不强制用户记任何命令
