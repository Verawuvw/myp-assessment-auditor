"""核心审计服务：封装 OpenAI 调用。

逻辑抽取自 myp_audit.py 的 ``make_client`` 与 ``analyze_task``，
并组合 PDF 抽取与语言检测，向上层暴露单一入口 ``audit_pdf_bytes``。
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI

from ..core.config import Settings, load_settings
from ..core.prompts import get_system_prompt
from .language import resolve_output_language
from .pdf import extract_text_from_bytes


class AuditError(RuntimeError):
    """审计流程中可预期的业务错误。"""


class MissingApiKeyError(AuditError):
    """未配置 OPENAI_API_KEY。"""


@dataclass
class AuditResult:
    """一次审计的完整结果。"""

    pdf_name: str
    language: str
    model: str
    report: str
    task_text: str


def make_client(settings: Settings | None = None) -> OpenAI:
    """创建 OpenAI 客户端。优先使用传入的 settings，否则读取环境变量。"""
    settings = settings or load_settings()
    if not settings.openai_api_key:
        raise MissingApiKeyError(
            "未找到 OPENAI_API_KEY。请设置环境变量后重试，例如：\n"
            '  export OPENAI_API_KEY="你的密钥"'
        )
    kwargs: dict[str, str] = {"api_key": settings.openai_api_key}
    base_url = settings.openai_base_url or os.getenv("OPENAI_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def analyze_task(
    client: OpenAI,
    model: str,
    pdf_name: str,
    task_text: str,
    output_lang: str,
) -> str:
    """调用模型对任务文本做概念性理解审计，返回 Markdown 报告。"""
    if output_lang == "en":
        system_prompt = get_system_prompt("en")
        user_content = (
            "Please audit the following MYP assessment task.\n"
            f"File name: {pdf_name}\n\n"
            f"Task text:\n{task_text}"
        )
    else:
        system_prompt = get_system_prompt("zh")
        user_content = (
            "请审核以下 MYP 评估任务。\n"
            f"文件名：{pdf_name}\n\n"
            f"任务文本：\n{task_text}"
        )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )
    content = response.choices[0].message.content
    if not content:
        raise AuditError("AI 没有返回分析内容。")
    return content.strip()


def audit_pdf_bytes(
    data: bytes,
    pdf_name: str = "<upload>",
    lang: str = "auto",
    model: str | None = None,
    client: OpenAI | None = None,
    settings: Settings | None = None,
) -> AuditResult:
    """端到端审计上传的 PDF 字节流。"""
    settings = settings or load_settings()
    model = model or settings.openai_model

    task_text = extract_text_from_bytes(data, source=pdf_name)
    output_lang = resolve_output_language(lang, task_text)
    client = client or make_client(settings)
    report = analyze_task(client, model, pdf_name, task_text, output_lang)

    return AuditResult(
        pdf_name=pdf_name,
        language=output_lang,
        model=model,
        report=report,
        task_text=task_text,
    )


def audit_pdf_path(
    pdf_path: str,
    lang: str = "auto",
    model: str | None = None,
    client: OpenAI | None = None,
    settings: Settings | None = None,
) -> AuditResult:
    """便利方法：审计磁盘上的 PDF 文件（供 CLI / 脚本使用）。"""
    from pathlib import Path

    path = Path(pdf_path)
    return audit_pdf_bytes(
        path.read_bytes(),
        pdf_name=path.name,
        lang=lang,
        model=model,
        client=client,
        settings=settings,
    )


__all__ = [
    "AuditError",
    "MissingApiKeyError",
    "AuditResult",
    "make_client",
    "analyze_task",
    "audit_pdf_bytes",
    "audit_pdf_path",
]
