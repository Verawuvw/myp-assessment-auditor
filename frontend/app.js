// MYP Assessment Auditor — 前端上传逻辑
// 通过表单 POST 调用后端 /api/audit 接口。

/**
 * 解析后端 API 基地址（不带尾斜杠），优先级从高到低：
 *
 * 1. 显式覆盖：设置 <meta name="myp-api-base" content="https://api.example.com">
 *    或在本脚本之前设置 window.MYP_API_BASE —— 适合前后端跨域部署到不同域名。
 * 2. 本地开发自动探测：前端跑在 3000/5173 等非 8000 端口（或直接以 file:// 打开）时，
 *    自动指向本机后端 http://127.0.0.1:8000。
 * 3. 默认：相对路径（同源）—— 即 "/api/audit"。
 *    这是 Vercel 线上部署的默认行为：前后端同域，无需 CORS。
 */
function resolveApiBase() {
  // 1) 运行时显式覆盖
  if (typeof window !== "undefined") {
    if (window.MYP_API_BASE) return String(window.MYP_API_BASE).replace(/\/+$/, "");
    const meta = document.querySelector('meta[name="myp-api-base"]');
    if (meta && meta.content) return meta.content.replace(/\/+$/, "");
  }

  // 2) 本地开发自动探测：前端与后端不同端口时指向本机后端
  if (typeof window !== "undefined" && window.location) {
    const { protocol, hostname, port } = window.location;
    const isLocalHost = hostname === "localhost" || hostname === "127.0.0.1";
    const isFileProtocol = protocol === "file:";
    if (isFileProtocol) return "http://127.0.0.1:8000";
    if (isLocalHost && port && port !== "8000") return "http://127.0.0.1:8000";
  }

  // 3) 默认同源（相对路径），适用于 Vercel 线上
  return "";
}

const API_BASE = resolveApiBase();
const API_ENDPOINT = `${API_BASE}/api/audit`;

const form = document.getElementById("audit-form");
const fileInput = document.getElementById("file-input");
const langSelect = document.getElementById("lang-select");
const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");
const resultCard = document.getElementById("result-card");
const reportEl = document.getElementById("report");
const copyBtn = document.getElementById("copy-btn");

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function setBusy(busy) {
  submitBtn.disabled = busy;
  submitBtn.textContent = busy ? "审计中…" : "开始审计";
}

function validateFile(file) {
  if (!file) return "请先选择一个 PDF 文件。";
  if (!file.name.toLowerCase().endsWith(".pdf")) return "仅支持 PDF 文件。";
  return null;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const file = fileInput.files[0];
  const error = validateFile(file);
  if (error) {
    setStatus(error, true);
    return;
  }

  const body = new FormData();
  body.append("file", file);
  body.append("lang", langSelect.value);

  setBusy(true);
  setStatus("正在上传并分析，请稍候…");
  resultCard.classList.add("hidden");

  try {
    const response = await fetch(API_ENDPOINT, { method: "POST", body });
    const payload = await response.json().catch(() => null);

    if (!response.ok) {
      const detail =
        (payload && (payload.detail || payload.message)) ||
        `请求失败（HTTP ${response.status}）`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }

    reportEl.textContent = payload.report || "（未返回报告内容）";
    resultCard.classList.remove("hidden");
    setStatus(`完成：${payload.file_name}，语言：${payload.language}`);
  } catch (err) {
    setStatus(`出错：${err.message}`, true);
  } finally {
    setBusy(false);
  }
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(reportEl.textContent || "");
    setStatus("报告已复制到剪贴板。");
  } catch {
    setStatus("复制失败，请手动选择文本。", true);
  }
});
