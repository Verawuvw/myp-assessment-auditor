#!/usr/bin/env python3
"""轻量 JS 语法自检：剥离注释与字符串后校验括号是否配平。

在未安装 Node.js 的环境下，用于粗略验证 app.js 结构完整。
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET = REPO_ROOT / "frontend" / "app.js"

PAIRS = {")": "(", "]": "[", "}": "{"}
OPENERS = "([{"
CLOSERS = ")]}"


def strip_comments_and_strings(src: str) -> str:
    """去掉 //、/* */ 注释以及字符串字面量，返回剩余代码。"""
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
        elif ch == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                i += 1
            i += 2
        elif ch in "\"'`":
            quote = ch
            i += 1
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == quote:
                    i += 1
                    break
                i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def check_balance(code: str) -> tuple[bool, str]:
    stack: list[str] = []
    for idx, ch in enumerate(code):
        if ch in OPENERS:
            stack.append(ch)
        elif ch in CLOSERS:
            if not stack:
                return False, f"多余的闭合符号 {ch!r}（偏移 {idx}）"
            top = stack.pop()
            if top != PAIRS[ch]:
                return False, f"括号不匹配：{top!r} 与 {ch!r}（偏移 {idx}）"
    if stack:
        return False, f"未闭合的括号：{''.join(stack)}"
    return True, "括号配平"


def main() -> int:
    if not TARGET.is_file():
        print(f"找不到目标文件：{TARGET}")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    code = strip_comments_and_strings(src)
    ok, message = check_balance(code)
    print(f"[{'OK' if ok else 'FAIL'}] {TARGET.name}: {message}")

    checks = {
        "包含 resolveApiBase 函数": "function resolveApiBase()" in src,
        "使用相对/动态 API 基地址": "const API_BASE = resolveApiBase();" in src,
        "仍有 127.0.0.1 硬编码": "127.0.0.1" in src,
    }
    for label, passed in checks.items():
        print(f"[{'是' if passed else '否'}] {label}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
