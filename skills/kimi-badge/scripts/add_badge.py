#!/usr/bin/env python3
"""把「powered by KimiCode」徽章插入 Markdown 文档，插入过程幂等。

用法:
    python3 add_badge.py README.md
    python3 add_badge.py docs/guide.md --position bottom
    python3 add_badge.py README.md --mode remote --image-url https://.../badge.svg
    python3 add_badge.py README.md --dry-run

仓库根目录查找顺序: --repo-root > 向上查找 .git/.kimi-badge.json/.kimi-badge-disable > 文件所在目录。
"""

import argparse
import json
import os
import re
import shutil
import sys

PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ASSETS_DIR = os.path.join(PLUGIN_ROOT, "assets")

MARKER = "<!-- kimi-badge -->"
ASSET_BASENAME = "kimi-badge.svg"
DISABLE_FILE = ".kimi-badge-disable"
CONFIG_FILE = ".kimi-badge.json"

DEFAULT_LABEL = "powered by KimiCode"
DEFAULT_LINK = "https://www.kimi.com/code"
DEFAULT_ASSET_DIR = os.path.join(".github", "assets")
VARIANTS = {
    "flat": ("badge.svg", "kimi-badge.svg"),
    "flat-square": ("badge-flat.svg", "kimi-badge-square.svg"),
    "plain": ("badge-plain.svg", "kimi-badge-plain.svg"),
}


def find_repo_root(start, explicit=None):
    if explicit:
        return os.path.abspath(explicit)
    current = os.path.abspath(start)
    while True:
        for marker in (".git", CONFIG_FILE, DISABLE_FILE):
            if os.path.exists(os.path.join(current, marker)):
                return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.abspath(start)
        current = parent


def load_config(repo_root):
    path = os.path.join(repo_root, CONFIG_FILE)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        print("! 忽略无法解析的 %s: %s" % (CONFIG_FILE, exc))
        return {}
    return data if isinstance(data, dict) else {}


def badge_is_present(text):
    if MARKER in text:
        return True
    return ASSET_BASENAME in text


def insert_after_heading(lines):
    for index, line in enumerate(lines):
        if re.match(r"^#\s+\S", line):
            return index + 1
    return None


def render_block(label, link, image_ref):
    return [MARKER, "[![%s](%s)](%s)" % (label, image_ref, link)]


def insert_block(lines, block, position, is_readme):
    lines = list(lines)
    if position == "top":
        new_lines = list(block)
        if lines:
            while lines and not lines[0].strip():
                lines.pop(0)
            new_lines.append("")
            new_lines.extend(lines)
        return new_lines

    if position == "bottom":
        new_lines = [line.rstrip() for line in lines]
        while new_lines and not new_lines[-1]:
            new_lines.pop()
        if new_lines:
            new_lines.append("")
        new_lines.extend(block)
        return new_lines

    anchor = insert_after_heading(lines) if is_readme else None
    if anchor is None:
        anchor = 0
    head = lines[:anchor]
    tail = lines[anchor:]

    while head and not head[-1].strip():
        head.pop()
    if head:
        head.append("")
    head.extend(block)
    if tail:
        while tail and not tail[0].strip():
            tail.pop(0)
        head.append("")
    head.extend(tail)
    return head


def copy_asset(repo_root, asset_rel, variant, dry_run):
    source_name = VARIANTS[variant][0]
    source = os.path.join(ASSETS_DIR, source_name)
    if not os.path.isfile(source):
        print("! 找不到徽章素材: %s" % source)
        return None
    target = os.path.join(repo_root, asset_rel)
    if os.path.isfile(target) and not dry_run:
        try:
            if open(target, "rb").read() == open(source, "rb").read():
                return target
        except OSError:
            pass
    if dry_run:
        print("  [dry-run] 将写入徽章文件 %s" % target)
        return target
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.copyfile(source, target)
    print("  已写入徽章文件 %s" % target)
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description="给 Markdown 文档添加 KimiCode 徽章")
    parser.add_argument("files", nargs="+", help="要处理的 Markdown 文件")
    parser.add_argument("--repo-root", default=None, help="仓库根目录（默认自动查找）")
    parser.add_argument("--mode", choices=("local", "remote"), default=None, help="local=随仓库提交 SVG，remote=引用外部 URL")
    parser.add_argument("--position", choices=("auto", "top", "bottom"), default=None, help="徽章落位，默认 auto")
    parser.add_argument("--label", default=None, help="徽章文案，默认「powered by KimiCode」")
    parser.add_argument("--link", default=None, help="徽章点击跳转地址")
    parser.add_argument("--image-url", default=None, help="remote 模式下的图片地址")
    parser.add_argument("--asset-path", default=None, help="local 模式下的徽章文件相对路径")
    parser.add_argument("--variant", choices=tuple(VARIANTS), default=None, help="徽章样式")
    parser.add_argument("--dry-run", action="store_true", help="只打印将要做的事，不写文件")
    args = parser.parse_args(argv)

    changed = 0
    for raw_path in args.files:
        path = os.path.abspath(raw_path)
        if not os.path.isfile(path):
            print("! 跳过不存在的文件: %s" % raw_path)
            continue

        repo_root = find_repo_root(os.path.dirname(path), args.repo_root)
        config = load_config(repo_root)

        if os.path.exists(os.path.join(repo_root, DISABLE_FILE)) or config.get("disabled"):
            print("- %s: 仓库已关闭徽章（%s），跳过" % (raw_path, DISABLE_FILE))
            continue

        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()

        if badge_is_present(text):
            print("- %s: 已存在徽章，跳过" % raw_path)
            continue

        mode = args.mode or config.get("mode") or "local"
        position = args.position or config.get("position") or "auto"
        label = args.label or config.get("label") or DEFAULT_LABEL
        link = args.link or config.get("link") or DEFAULT_LINK
        variant = args.variant or config.get("variant") or "flat"
        asset_rel = args.asset_path or config.get("assetPath")
        if not asset_rel:
            asset_rel = os.path.join(DEFAULT_ASSET_DIR, VARIANTS[variant][1])
        image_url = args.image_url or config.get("imageUrl") or ""

        is_readme = os.path.basename(path).lower().startswith("readme")
        if position == "auto":
            position = "after-heading" if is_readme else "bottom"

        if mode == "remote":
            if not image_url:
                print("! %s: remote 模式需要 --image-url（或在 %s 里配 imageUrl）" % (raw_path, CONFIG_FILE))
                continue
            image_ref = image_url
        else:
            asset_abs = copy_asset(repo_root, asset_rel, variant, args.dry_run)
            if asset_abs is None:
                continue
            image_ref = os.path.relpath(
                os.path.realpath(asset_abs), os.path.realpath(os.path.dirname(path))
            ).replace(os.sep, "/")

        lines = text.splitlines()
        new_lines = insert_block(lines, render_block(label, link, image_ref), position, is_readme)
        new_text = "\n".join(new_lines) + "\n"

        if args.dry_run:
            print("- %s: [dry-run] 将插入徽章（位置 %s，图片 %s）" % (raw_path, position, image_ref))
        else:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(new_text)
            print("✓ %s: 已添加徽章（位置 %s，图片 %s）" % (raw_path, position, image_ref))
        changed += 1

    if not changed:
        print("没有需要修改的文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
