"""应用配置。

集中管理从环境变量读取的设置，避免业务代码散落 os.getenv 调用。
后续扩展（数据库、鉴权、多模型等）都可在此处继续添加。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# backend/ 目录（本文件位于 backend/app/core/config.py）
BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


def _load_dotenv(path: Path) -> None:
    """加载 .env 文件到环境变量（已存在的真实环境变量优先，不覆盖）。

    优先使用 python-dotenv；若未安装则回退到一个简单的内置解析器，
    保证在最小依赖环境下也能工作。
    """
    if not path.is_file():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(path, override=False)
        return
    except ImportError:
        pass

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


# 在读取任何配置之前加载 .env
_load_dotenv(ENV_FILE)


def _split_csv(value: str) -> list[str]:
    """把逗号分隔的环境变量解析为列表。"""
    return [item.strip() for item in value.split(",") if item.strip()]


def _default_max_upload_bytes() -> int:
    """计算默认的上传体积上限。

    Vercel Serverless Functions 对请求体有约 4.5 MB 的硬性限制，超过会在到达
    FastAPI 之前就被平台拒绝，因此线上环境把默认值收紧到 4 MB，给出友好报错。
    本地开发（未设置 ``VERCEL`` 环境变量）仍使用 20 MB。
    """
    if os.getenv("VERCEL"):
        return 4 * 1024 * 1024
    return 20 * 1024 * 1024


@dataclass(frozen=True)
class Settings:
    """运行时配置（来源于环境变量，带合理默认值）。"""

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    # 单次请求允许上传的最大文件体积（字节）
    max_upload_bytes: int = field(default_factory=_default_max_upload_bytes)
    # CORS 允许的来源，"*" 表示全部放行（开发环境默认值）
    cors_origins: list[str] = field(default_factory=lambda: ["*"])

    @property
    def has_api_key(self) -> bool:
        return bool(self.openai_api_key)


def load_settings() -> Settings:
    """从环境变量构建 Settings 实例。每次请求读取，方便测试时动态修改。"""
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        max_upload_bytes=int(
            os.getenv("MYP_MAX_UPLOAD_BYTES", str(_default_max_upload_bytes()))
        ),
        cors_origins=_split_csv(os.getenv("MYP_CORS_ORIGINS", "*")),
    )


settings = load_settings()
