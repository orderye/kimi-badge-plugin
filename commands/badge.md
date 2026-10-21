---
description: 给指定文档或 PR 描述添加「powered by KimiCode」徽章
---

给 $ARGUMENTS 添加「powered by KimiCode」徽章。

按 kimi-badge 技能的规则执行：优先用 `${KIMI_SKILL_DIR}/scripts/add_badge.py` 插入（幂等，不会重复添加），README 落在第一个一级标题之后，其他文档落在正文末尾；PR 描述请写入临时文件后用 `gh pr edit <PR号> --body-file <临时文件>` 提交。

完成后核对：徽章只出现一次、图片文件真实存在、文档渲染没有被破坏。