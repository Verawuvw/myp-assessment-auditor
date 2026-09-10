"""报告语言检测。

逻辑抽取自 myp_audit.py 的 ``detect_task_language`` /
``resolve_output_language``，保持行为一致。
"""

from __future__ import annotations

VALID_LANGS = {"zh", "en"}


def detect_task_language(text: str) -> str:
    """依据中日韩字符与拉丁字母的数量判断任务语言。"""
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    latin = sum(1 for ch in text if ("A" <= ch <= "Z") or ("a" <= ch <= "z"))
    return "zh" if cjk >= max(latin, 1) else "en"


def resolve_output_language(lang: str, task_text: str) -> str:
    """把请求中的 lang 参数转换为实际输出语言。

    lang 为 ``zh``/``en`` 时强制使用；否则（``auto``/``None`` 等）自动检测。
    """
    if lang in VALID_LANGS:
        return lang
    return detect_task_language(task_text)


__all__ = ["VALID_LANGS", "detect_task_language", "resolve_output_language"]
