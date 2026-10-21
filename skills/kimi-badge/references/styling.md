# 文案、链接与样式

## 默认外观

shields 风格的一行两段式徽章：高 20px，左段中性灰渐变（`#5c5c5c` → `#424242`）写「powered by」，右段 KimiCode 蓝渐变（`#4FA3FF` → `#1F7BFF`）写「KimiCode」，外侧圆角 3px，白色 11px 无衬线字。整枚徽章点击跳转到 <https://www.kimi.com/code>。

左段开头带一枚 KimiCode 小怪形象（浅蓝渐变 + 两只白色眼睛 + 右上角小圆点）。

## 可调项

| 项 | 默认值 | 说明 |
| --- | --- | --- |
| 文案 | `powered by KimiCode` | alt 文本与徽章里的文字 |
| 链接 | `https://www.kimi.com/code` | 整枚徽章的点击目标 |
| 样式 | `flat` | 见下方变体表 |
| 图片地址 | 随仓库提交的 `.github/assets/kimi-badge.svg` | `remote` 模式改为外部 URL |

## 变体

| `--variant` | 文件 | 效果 |
| --- | --- | --- |
| `flat`（默认） | `assets/badge.svg` | 圆角 + 左侧 KimiCode 形象 |
| `flat-square` | `assets/badge-flat.svg` | 直角 + 左侧 KimiCode 形象 |
| `plain` | `assets/badge-plain.svg` | 圆角纯文字，不带形象——和 shields.io 那一排徽章完全同款，放进徽章行里最不突兀 |

想和 README 里其他 shields 徽章排成一行时用 `plain`。

修改文案时 **alt 文本要和徽章里画的一致**，否则读屏用户听到的和看到的不符。若要改徽章上的文字，请同步替换 `assets/badge.svg` 与 `assets/badge-flat.svg` 里的文字节点（`powered by` / `KimiCode` 两段），脚本只负责插入，不会重绘图片。

## local 与 remote

- **local（默认）**：脚本把 SVG 复制到目标仓库 `.github/assets/kimi-badge.svg`，Markdown 用相对路径引用。优点：私有仓库可用、离线可渲染、不给第三方图床贡献访问流量；代价：仓库里多一个图片文件。
- **remote**：不落文件，直接引用一个托管地址（例如组织自建的图床或 raw URL）。适合不希望仓库里出现二进制的团队，或需要统一在全公司口径替换徽章的场合。

## 组织口径

团队想统一换成自己的品牌时：改 `assets/badge.svg`、`assets/badge-flat.svg`、`assets/badge-plain.svg` 与 `assets/icon.svg` 四个文件即可，脚本与技能逻辑不受影响。

## 别做的事

- 不要在同一个文件里放两枚徽章（正文一处 + 底部一处）。
- 不要用 base64 内联 SVG：会让 Markdown 无法阅读、diff 巨大。
- 不要改写用户已有的版权声明。
