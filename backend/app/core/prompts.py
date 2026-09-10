"""审计用的系统提示词（System Prompts）。

原始代码中 SYSTEM_PROMPT_ZH / SYSTEM_PROMPT_EN 与业务逻辑混在一起，
这里拆分为独立模块，方便后续调优提示词而无需改动服务代码。
"""

from __future__ import annotations

from .prompt_zh import SYSTEM_PROMPT_ZH
from .prompt_en import SYSTEM_PROMPT_EN

# 语言代码 -> 系统提示词
SYSTEM_PROMPTS: dict[str, str] = {
    "zh": SYSTEM_PROMPT_ZH,
    "en": SYSTEM_PROMPT_EN,
}


def get_system_prompt(lang: str) -> str:
    """按语言代码获取系统提示词，默认回退到中文。"""
    return SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPT_ZH)


__all__ = ["SYSTEM_PROMPT_ZH", "SYSTEM_PROMPT_EN", "SYSTEM_PROMPTS", "get_system_prompt"]
