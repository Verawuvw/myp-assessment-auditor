"""PDF 文本抽取服务。

逻辑抽取自 myp_audit.py 的 ``extract_pdf_text``，并扩展了一个可直接
处理上传字节流的版本 ``extract_text_from_bytes``，便于 Web 接口复用。
"""

from __future__ import annotations

import io
from pathlib import Path

from pypdf import PdfReader


class PdfExtractionError(ValueError):
    """PDF 无法解析或未提取到文本时抛出。"""


def _build_combined_text(pages: list[str], source: str) -> str:
    combined = "\n\n".join(pages).strip()
    if not combined:
        raise PdfExtractionError(
            f"未能从 PDF 提取到文本（可能是扫描件）：{source}"
        )
    return combined


def _iter_page_texts(reader: PdfReader) -> list[str]:
    pages: list[str] = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"--- 第 {i} 页 ---\n{text.strip()}")
    return pages


def extract_pdf_text(pdf_path: str | Path) -> str:
    """从磁盘上的 PDF 文件抽取文本。"""
    path = Path(pdf_path)
    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # pypdf 会抛出多种解析异常
        raise PdfExtractionError(f"无法读取 PDF：{path}（{exc}）") from exc
    return _build_combined_text(_iter_page_texts(reader), str(path))


def extract_text_from_bytes(data: bytes, source: str = "<upload>") -> str:
    """从内存中的 PDF 字节流抽取文本（用于上传接口）。"""
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise PdfExtractionError(f"无法解析上传的 PDF：{source}（{exc}）") from exc
    return _build_combined_text(_iter_page_texts(reader), source)


__all__ = ["PdfExtractionError", "extract_pdf_text", "extract_text_from_bytes"]
