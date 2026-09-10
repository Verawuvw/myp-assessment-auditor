"""审计接口路由：POST /api/audit。

接收上传的 PDF 文件，返回概念性理解审计报告。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ...core.config import load_settings
from ...services.auditor import (
    AuditError,
    MissingApiKeyError,
    audit_pdf_bytes,
)
from ...services.language import VALID_LANGS
from ...services.pdf import PdfExtractionError

router = APIRouter(prefix="/api", tags=["audit"])

PDF_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",
    "binary/octet-stream",
}


def _validate_pdf_upload(file: UploadFile, data: bytes) -> None:
    """校验上传文件的类型与体积。"""
    settings = load_settings()

    filename = (file.filename or "").lower()
    is_pdf_name = filename.endswith(".pdf")
    # 允许部分浏览器/客户端使用通用 octet-stream，但文件名需为 .pdf
    if not is_pdf_name:
        raise HTTPException(
            status_code=400,
            detail="仅支持 PDF 文件，请上传扩展名为 .pdf 的文件。",
        )

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in PDF_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型：{file.content_type}，仅支持 PDF。",
        )

    if not data:
        raise HTTPException(status_code=400, detail="上传的文件为空。")

    if len(data) > settings.max_upload_bytes:
        max_mb = settings.max_upload_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大允许 {max_mb:.0f} MB。",
        )


@router.post("/audit", summary="对上传的 MYP 评估任务 PDF 进行审计")
async def audit(
    file: UploadFile = File(..., description="MYP 评估任务 PDF 文件"),
    lang: str = Form("auto", description="报告语言：auto / zh / en"),
    model: Optional[str] = Form(None, description="可选，覆盖默认模型"),
):
    """接收 PDF 上传并返回审计报告。

    表单字段：
    - ``file``：待审计的 PDF
    - ``lang``：``auto``（默认，跟随任务语言）/ ``zh`` / ``en``
    - ``model``：可选，覆盖后端默认模型
    """
    normalized_lang = (lang or "auto").strip().lower()
    if normalized_lang not in VALID_LANGS | {"auto"}:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的 lang 参数：{lang}，可选值为 auto / zh / en。",
        )

    data = await file.read()
    _validate_pdf_upload(file, data)

    try:
        result = audit_pdf_bytes(
            data,
            pdf_name=file.filename or "<upload>",
            lang=normalized_lang,
            model=model,
        )
    except MissingApiKeyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PdfExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AuditError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "file_name": result.pdf_name,
        "language": result.language,
        "model": result.model,
        "report": result.report,
        # 保留抽取文本，方便前端调试与后续功能扩展
        "task_text": result.task_text,
    }
