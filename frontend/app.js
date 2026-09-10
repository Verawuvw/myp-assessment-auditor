// MYP Assessment Auditor — 前端上传逻辑
// 通过表单 POST 调用后端 /api/audit 接口。

// 前端与后端不同源（前端 3000 端口，后端 8000 端口），因此显式指向后端地址。
// 生成的完整接口地址为：http://127.0.0.1:8000/api/audit
const API_BASE = "http://127.0.0.1:8000";

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
