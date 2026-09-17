#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全仓 Markdown 相对链接可达性检查 —— 教程索引终检的机械化部分。

为什么需要它
------------
`docs/lessons/README.md` §11 与 issue #11 都要求「全仓相对链接检查通过」。
课程完成度校验（`check-lessons.py`）只看单课内部的契约，不看跨文件链接；
课号重排（2026-09-17 由连续数字改为层前缀）之后，旧路径会静默留在一堆
索引和溯源文档里，编辑器和 GitHub 都不会报错。这个脚本把那一层补上。

判定的范围
----------
`docs/**/*.md` + `CONTEXT.md` + `README.md` + `AGENTS.md` + `notebook/README.md`。
只判**相对路径**链接：跳过 `http(s)://`、`mailto:`、纯锚点 `#...`、`data:`。

已知的解析细节
--------------
- 支持 Markdown 的尖括号写法 `[text](<path with spaces>)`——本仓库的论文阅读材料
  文件名含全角冒号（`UniPert-G2CP：…`），必须用这种写法才不会被解析成 URL scheme。
  早期版本漏了这一条，会把 5 条**真实可达**的链接误报为断链。
- 目标存在性判断用 `Path.exists()`，目录或文件都算通过。

退出码：0 = 全部可达；1 = 存在断链。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

# 仓库根：脚本位于 <root>/scripts/，向上两级
ROOT = Path(__file__).resolve().parent.parent

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

SCAN_GLOBS = (
    "docs/**/*.md",
    "CONTEXT.md",
    "README.md",
    "AGENTS.md",
    "notebook/README.md",
)

SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "data:")


def main() -> int:
    targets: list[Path] = []
    for pat in SCAN_GLOBS:
        targets.extend(sorted(ROOT.glob(pat)))

    missing: list[tuple[Path, int, str, Path]] = []
    n_links = 0
    n_files = 0

    for src in targets:
        if not src.is_file():
            continue
        n_files += 1
        try:
            text = src.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = src.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in LINK_RE.finditer(line):
                raw = m.group(1).strip()
                # Markdown 尖括号写法：含空格或全角冒号的路径
                if raw.startswith("<") and raw.endswith(">"):
                    raw = raw[1:-1].strip()
                if raw.startswith(SKIP_PREFIXES):
                    continue
                path_part = raw.split("#", 1)[0]
                if not path_part:
                    continue
                n_links += 1
                dest = (src.parent / unquote(path_part)).resolve()
                if not dest.exists():
                    missing.append((src, lineno, raw, dest))

    print(f"扫描文件 {n_files} 个 ｜ 相对链接 {n_links} 条 ｜ 断链 {len(missing)} 条")
    print("=" * 78)
    for src, lineno, raw, dest in missing:
        try:
            rel = src.relative_to(ROOT)
        except ValueError:
            rel = src
        print(f"X {rel}:{lineno}\n    指向 {raw}\n    解析为 {dest}")
    if not missing:
        print("全部可达。")
    print("=" * 78)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
