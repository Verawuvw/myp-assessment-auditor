"""Vercel 部署入口（FastAPI 零配置后端）。

Vercel 的 Python runtime 会在仓库根目录查找名为 ``app`` 的 FastAPI/ASGI 实例，
支持的文件名包括 ``app.py`` / ``index.py`` / ``server.py`` / ``main.py`` /
``wsgi.py`` / ``asgi.py``。本文件命名为 ``index.py`` 并被 Vercel 识别为入口后，
**所有请求**（含 ``/`` 与静态资源）都会交给这个 app 处理。

因此这里做两件事：

1. 复用 ``backend/main.py`` 中已有的 FastAPI 应用（含 CORS、``/api/health``、
   ``/api/audit`` 路由），保证线上线下行为一致；
2. 挂载静态前端目录，使 ``/`` 返回上传界面。

由于 Vercel 会把完整原始路径（例如 ``/api/audit``）原样交给 app，
无需任何 rewrite，前端使用相对路径 ``/api/audit`` 即可同源调用。
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.staticfiles import StaticFiles

# 仓库根目录与 backend/ 目录（本文件位于仓库根）
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"

# 让 `import main` 与 `import app.*` 都能解析到 backend/ 下的真实代码
for path in (str(BACKEND_DIR), str(REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from main import app  # noqa: E402  （复用现有 FastAPI 应用）

# 静态前端目录（仓库内唯一副本，避免 frontend/ 与 public/ 双份维护）
_STATIC_DIR = REPO_ROOT / "frontend"

if _STATIC_DIR.is_dir():
    # html=True 让 "/" 自动返回 index.html。
    # 注意：mount 在最后，不会覆盖前面已注册的 /api/* 路由。
    app.mount(
        "/",
        StaticFiles(directory=str(_STATIC_DIR), html=True),
        name="static",
    )

__all__ = ["app"]
