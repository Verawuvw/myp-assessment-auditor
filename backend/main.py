#!/usr/bin/env python3
"""MYP Auditor 后端入口。

启动方式（在 ``backend`` 目录下）：
    uvicorn main:app --reload --port 8000
或：
    python main.py

接口文档：http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes.audit import router as audit_router
from app.core.config import load_settings

app = FastAPI(
    title="MYP Assessment Auditor",
    description="对 IB MYP summative assessment 任务 PDF 进行概念性理解审计。",
    version=__version__,
)

_settings = load_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router)


@app.get("/api/health", tags=["system"], summary="健康检查")
async def health() -> dict[str, object]:
    """返回服务状态与必要配置是否就绪。"""
    settings = load_settings()
    return {
        "status": "ok",
        "version": __version__,
        "model": settings.openai_model,
        "api_key_configured": settings.has_api_key,
    }


def main() -> None:
    """以脚本方式启动开发服务器。"""
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
