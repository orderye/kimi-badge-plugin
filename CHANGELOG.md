# 更新日志

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## 0.3.0

- 徽章改为 shields 风格：中性灰标签段 + KimiCode 蓝值段、外侧圆角 3px、20px 高。
- 新增 `plain` 变体（纯文字），可与 README 里的 shields 徽章排成一行。
- 各变体使用独立文件名（`kimi-badge.svg` / `kimi-badge-square.svg` / `kimi-badge-plain.svg`），互不覆盖。
- 修复 `/tmp` 等 symlink 路径下相对图片路径计算错误的问题。

## 0.2.0

- 新增 `PostToolUse` / `Stop` 两个 hook，插件启用后自动为文档补徽章，不再依赖模型自觉。
- 新增 `sessionStart.skill` 与 `systemPrompt`，徽章规则常驻上下文。
- 支持 `.kimi-badge.json` 仓库级配置与 `.kimi-badge-disable` 关闭开关。
- 新增 `/kimi-badge:badge` 斜杠命令。

## 0.1.0

- 首个版本：一个 Skill + 一个插入脚本 + 徽章素材，可手动或按规则为 README / 文档 / PR 描述加徽章。
