#!/bin/bash
# 本地端到端验证脚本：确认 index.py 同时提供 API 与静态前端。
set -uo pipefail

# 脚本位于 <repo>/scripts/，因此仓库根目录是上一级
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

PORT=8126
PY="$REPO_ROOT/backend/.venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "找不到虚拟环境解释器：$PY"
  echo "请先在 backend/ 下创建 .venv 并安装依赖。"
  exit 1
fi

pkill -f "uvicorn index:app" 2>/dev/null
sleep 1

"$PY" -m uvicorn index:app --port "$PORT" > /tmp/vtest_final.log 2>&1 &
SERVER_PID=$!

# 等待服务就绪
for _ in $(seq 1 30); do
  if curl -s --max-time 2 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "=== API: /api/health ==="
curl -s --max-time 10 "http://127.0.0.1:$PORT/api/health"; echo

echo "=== Static: / ==="
curl -s --max-time 10 -o /tmp/root.html -w 'status=%{http_code} type=%{content_type}\n' "http://127.0.0.1:$PORT/"

echo "=== Static: /app.js ==="
curl -s --max-time 10 -o /dev/null -w 'status=%{http_code} type=%{content_type}\n' "http://127.0.0.1:$PORT/app.js"

echo "=== Static: /styles.css ==="
curl -s --max-time 10 -o /dev/null -w 'status=%{http_code} type=%{content_type}\n' "http://127.0.0.1:$PORT/styles.css"

echo "=== API: /api/audit (GET, 期望 405 或 404) ==="
curl -s --max-time 10 -o /dev/null -w 'status=%{http_code}\n' "http://127.0.0.1:$PORT/api/audit"

echo "=== API: POST /api/audit 无文件（期望 422 校验错误，证明路由可达） ==="
curl -s --max-time 20 -o /tmp/audit_missing.json -w 'status=%{http_code}\n' \
  -X POST "http://127.0.0.1:$PORT/api/audit"
cat /tmp/audit_missing.json; echo

echo "=== API: POST /api/audit 非 PDF（期望 400 类型错误） ==="
echo "not a pdf" > /tmp/not_a_pdf.txt
curl -s --max-time 30 -o /tmp/audit_badtype.json -w 'status=%{http_code}\n' \
  -X POST "http://127.0.0.1:$PORT/api/audit" \
  -F "file=@/tmp/not_a_pdf.txt;filename=bad.pdf;type=application/pdf"
cat /tmp/audit_badtype.json; echo

echo "=== API: /docs (OpenAPI UI) ==="
curl -s --max-time 10 -o /dev/null -w 'status=%{http_code} type=%{content_type}\n' "http://127.0.0.1:$PORT/docs"

echo "=== / 返回内容首行 ==="
head -2 /tmp/root.html

# 可选：真实审计端到端测试（存在 ../test_task.pdf 时执行）
REAL_PDF="$REPO_ROOT/../test_task.pdf"
if [ -f "$REAL_PDF" ]; then
  echo "=== API: POST /api/audit 真实 PDF 端到端 ==="
  curl -s --max-time 120 -o /tmp/audit_real.json -w 'status=%{http_code}\n' \
    -X POST "http://127.0.0.1:$PORT/api/audit" \
    -F "file=@$REAL_PDF" -F "lang=auto"
  "$PY" - <<'PYEOF'
import json
try:
    with open("/tmp/audit_real.json", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "report" in data:
        print("file_name =", data.get("file_name"))
        print("language  =", data.get("language"))
        print("model     =", data.get("model"))
        print("report len=", len(data.get("report") or ""))
        print("report head:", (data.get("report") or "")[:120].replace("\n", " "))
    else:
        print("响应（非报告）:", json.dumps(data, ensure_ascii=False)[:300])
except Exception as exc:
    print("解析响应失败:", exc)
PYEOF
else
  echo "=== 跳过真实 PDF 测试（未找到 $REAL_PDF） ==="
fi

kill "$SERVER_PID" 2>/dev/null
wait "$SERVER_PID" 2>/dev/null
echo "=== 完成 ==="
