"""端到端冒烟测试：验证 FastAPI 接口与核心服务。

不依赖真实 OPENAI_API_KEY —— 通过注入假的 OpenAI 客户端来验证
PDF 上传 -> 文本抽取 -> 语言检测 -> 报告返回 的完整链路。

运行（在 backend 目录下，且已安装依赖）：
    ./.venv/bin/python smoke_test.py
"""

from __future__ import annotations

import os
import sys
from types import SimpleNamespace

# 在导入 app 之前设置一个假 key，避免缺少 key 导致初始化失败
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from fastapi.testclient import TestClient  # noqa: E402

import app.api.routes.audit as audit_route  # noqa: E402
from app.services import auditor  # noqa: E402
from main import app  # noqa: E402

PDF_PATH = os.path.abspath(
    os.getenv(
        "MYP_TEST_PDF",
        # backend/ -> myp-auditor/ -> 项目根目录，测试 PDF 位于项目根目录
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "test_task.pdf"
        ),
    )
)


class FakeCompletions:
    def __init__(self) -> None:
        self.last_kwargs: dict | None = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        message = SimpleNamespace(content="# 模拟审计报告\n\n该任务属于 Category 2。")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeClient:
    def __init__(self) -> None:
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


def _patch_client(fake: FakeClient) -> None:
    """让 audit_pdf_bytes 内部使用假客户端。"""
    auditor.make_client = lambda *a, **k: fake  # type: ignore[assignment]
    # 路由模块导入了 audit_pdf_bytes，其内部调用的是 auditor.make_client，
    # 因此上面替换即生效。


def main() -> int:
    client = TestClient(app)
    failures: list[str] = []

    if not os.path.isfile(PDF_PATH):
        print(f"找不到测试 PDF：{PDF_PATH}")
        print("可通过环境变量 MYP_TEST_PDF 指定路径。")
        return 2
    print("使用测试 PDF ->", PDF_PATH)

    # 1) 健康检查
    resp = client.get("/api/health")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    print("[1] /api/health ->", body)
    if body.get("status") != "ok":
        failures.append("health 状态异常")

    # 2) 正常审计（注入假客户端）
    fake = FakeClient()
    _patch_client(fake)
    with open(PDF_PATH, "rb") as fh:
        resp = client.post(
            "/api/audit",
            files={"file": ("test_task.pdf", fh, "application/pdf")},
            data={"lang": "zh"},
        )
    print("[2] /api/audit status ->", resp.status_code)
    if resp.status_code != 200:
        failures.append(f"正常审计失败：{resp.status_code} {resp.text}")
    else:
        payload = resp.json()
        print("[2] file_name ->", payload["file_name"])
        print("[2] language  ->", payload["language"])
        print("[2] model     ->", payload["model"])
        print("[2] report[:30] ->", payload["report"][:30].replace(chr(10), " "))
        if payload["language"] != "zh":
            failures.append("lang=zh 未生效")
        if not payload["task_text"].strip():
            failures.append("task_text 为空")
        if not payload["report"].strip():
            failures.append("report 为空")
        used = fake.completions.last_kwargs
        if not used or used.get("model") != "gpt-4o-mini":
            failures.append("默认模型未传递给 OpenAI")

    # 3) 非 PDF 文件应被拒绝
    resp = client.post(
        "/api/audit",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    print("[3] non-pdf status ->", resp.status_code)
    if resp.status_code != 400:
        failures.append(f"非 PDF 应返回 400，实际 {resp.status_code}")

    # 4) 非法 lang 参数应被拒绝
    with open(PDF_PATH, "rb") as fh:
        resp = client.post(
            "/api/audit",
            files={"file": ("test_task.pdf", fh, "application/pdf")},
            data={"lang": "fr"},
        )
    print("[4] bad lang status ->", resp.status_code)
    if resp.status_code != 400:
        failures.append(f"非法 lang 应返回 400，实际 {resp.status_code}")

    print()
    if failures:
        print("FAILURES:")
        for item in failures:
            print(" -", item)
        return 1
    print("ALL_SMOKE_TESTS_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
