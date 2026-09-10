#!/usr/bin/env python3
"""命令行入口（可选）。

复用 backend 的核心逻辑，从本机 PDF 生成审计报告，方便脚本化调用。

在 ``backend`` 目录下运行：
    export OPENAI_API_KEY="你的密钥"
    python cli.py ../test_task.pdf
    python cli.py ../test_task.pdf --lang zh --save
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from app.services.auditor import AuditError, MissingApiKeyError, audit_pdf_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="对 MYP 评估任务 PDF 运行概念性理解审计。")
    parser.add_argument("pdf", help="待审计的 PDF 文件路径")
    parser.add_argument(
        "--lang",
        choices=["auto", "zh", "en"],
        default="auto",
        help="报告语言：auto=跟随任务语言（默认），zh=中文，en=英文",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="模型名称（默认读取 OPENAI_MODEL 环境变量，再回退 gpt-4o-mini）",
    )
    parser.add_argument("--save", action="store_true", help="保存为 <pdf>.audit.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.pdf).expanduser().resolve()

    if not pdf_path.is_file():
        print(f"错误：文件不存在：{pdf_path}", file=sys.stderr)
        return 1

    try:
        result = audit_pdf_path(str(pdf_path), lang=args.lang, model=args.model)
    except MissingApiKeyError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except AuditError as exc:
        print(f"失败：{exc}", file=sys.stderr)
        return 1

    print(result.report)
    if args.save:
        out_path = pdf_path.with_suffix(".audit.md")
        out_path.write_text(result.report + "\n", encoding="utf-8")
        print(f"\n已保存：{out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
