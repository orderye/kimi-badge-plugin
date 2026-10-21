# KimiCode 徽章（kimi-badge）

![powered by KimiCode](assets/badge.svg)

给 Agent 的产出留个署名：新建或更新 README、文档、PR 描述时，自动补上一枚「powered by KimiCode」徽章。

**装上即自动生效**——不需要每次提醒 Agent，也不依赖模型自觉：插件用 `PostToolUse` / `Stop` 两个 hook 在 Agent 写完文档的瞬间就把徽章插进去。

## 安装

在 Kimi Code 里执行：

```
/plugins install https://github.com/orderye/kimi-badge-plugin
```

装完 `/reload`（或开新会话）生效。

也可以从本地目录安装（开发调试用）：

```
/plugins install /path/to/kimi-badge-plugin
```

## 效果

| 目标 | 落位 |
| --- | --- |
| README | 第一个一级标题之后 |
| `docs/**`、设计稿、发布说明 | 正文末尾 |
| PR 描述 | 正文末尾（`gh pr edit --body-file`） |

插入的内容形如：

```markdown
<!-- kimi-badge -->
[![powered by KimiCode](./.github/assets/kimi-badge.svg)](https://www.kimi.com/code)
```

徽章素材是插件内置的本地 SVG，会随仓库一起提交——离线可渲染、私有仓库可用、不会给第三方图床贡献流量。插入过程幂等，重复执行不会叠加。

## 工作原理

| 机制 | 作用 |
| --- | --- |
| `sessionStart.skill` | 每个会话启动就把徽章规则加载进上下文 |
| `systemPrompt` | 系统提示里常驻要求：写文档 / PR 描述必须带徽章 |
| `PostToolUse` hook | Agent 用 Write / Edit 写完 README、docs、CHANGELOG 时，插件当场插入徽章 |
| `Stop` hook | 回合结束前检查本轮动过的文档，漏了提醒补一次（每轮至多一次，不阻塞） |

Agent 仍需自己处理 **PR 描述**——`gh pr edit --body-file` 的正文不是文件，hook 管不到。

hook 一律 fail-open：脚本出错、超时都只放行，不会因为徽章逻辑卡住正常工作。

## 徽章样式

| `--variant` | 文件 | 效果 |
| --- | --- | --- |
| `flat`（默认） | `assets/badge.svg` | 圆角 + 左侧 KimiCode 形象 |
| `flat-square` | `assets/badge-flat.svg` | 直角 + KimiCode 形象 |
| `plain` | `assets/badge-plain.svg` | 纯文字，和 shields.io 徽章行同款 |

shields 风格：20px 高，左段中性灰渐变写「powered by」，右段 KimiCode 蓝渐变写「KimiCode」，外侧圆角 3px，白色 11px 无衬线字。

手动插入：

```bash
python3 skills/kimi-badge/scripts/add_badge.py README.md
python3 skills/kimi-badge/scripts/add_badge.py README.md --variant plain
```

常用参数：`--position top|bottom`、`--mode local|remote`、`--label`、`--link`、`--dry-run`。

## 自定义与关闭

在目标仓库根目录放 `.kimi-badge.json` 改默认值：

```json
{
  "label": "powered by KimiCode",
  "link": "https://www.kimi.com/code",
  "mode": "local",
  "assetPath": ".github/assets/kimi-badge.svg",
  "position": "auto"
}
```

放一个空的 `.kimi-badge-disable` 文件即可整体关闭该仓库的徽章（hook 也不会再提醒）。

## 覆盖范围

自动插入的目标文件：`README*`、`docs/**`、`CHANGELOG.md`、`RELEASE_NOTES.md`。
项目根目录判定顺序：git 仓库根 → 会话当前目录；`node_modules/`、`.git/`、`~/.kimi-code/` 内的路径一律忽略。

## 目录结构

```
kimi-badge-plugin/
├── kimi.plugin.json              # 插件清单（技能 / 命令 / hook / systemPrompt）
├── assets/                       # 徽章与图标 SVG
├── commands/badge.md             # /kimi-badge:badge 斜杠命令
├── hooks/badge-guard.mjs         # PostToolUse 自动插入 + Stop 兜底检查
└── skills/kimi-badge/
    ├── SKILL.md                  # 何时加 / 加在哪 / 怎么加
    ├── references/placement.md   # 分场景落位规则
    ├── references/styling.md     # 文案、链接、样式、自定义
    └── scripts/add_badge.py      # 幂等插入脚本（仅标准库）
```

## 许可

MIT
