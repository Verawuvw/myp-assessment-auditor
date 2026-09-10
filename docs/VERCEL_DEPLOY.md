# MYP Auditor — Vercel 部署指南

本项目在 Vercel 上使用 **单一 FastAPI 应用**同时提供 API 与静态前端：

```
请求 /            -> frontend/index.html（静态前端）
请求 /app.js      -> frontend/app.js
请求 /api/audit   -> FastAPI 的审计接口
请求 /api/health  -> 健康检查
```

## 关键设计

- **入口文件**：仓库根目录的 `index.py`。Vercel 的 Python runtime 会自动在
  根目录查找名为 `app` 的 FastAPI/ASGI 实例（支持的文件名包括 `app.py`、
  `index.py`、`server.py`、`main.py` 等），并把**所有请求**交给它处理。
- **静态前端**：由 `index.py` 通过 `StaticFiles` 挂载 `frontend/` 目录，
  以 `/` 提供上传界面。因此前端与后端**同源**，无需 CORS，前端用相对路径
  `/api/audit` 调用即可。
- **依赖声明**：根目录 `requirements.txt`（Vercel 从项目根读取）。
- **Python 版本**：`.python-version`（当前为 3.12）。
- **函数配置**：`vercel.json`（内存、超时、`/api/*` 禁用缓存）。

> 说明：你的前端是**原生 HTML/CSS/JS**，不是 Next.js，因此不涉及
> `NEXT_PUBLIC_*` 环境变量，也不需要 Node 构建步骤。

## 一、部署前准备（本地）

已完成的改动：

| 文件 | 作用 |
| --- | --- |
| `index.py` | Vercel 入口：复用 `backend/main.py` 的 app 并挂载 `frontend/` |
| `requirements.txt` | 根目录依赖，供 Vercel 安装 |
| `vercel.json` | 函数内存/超时与缓存头配置 |
| `.python-version` | 固定 Python 3.12 |
| `frontend/app.js` | API 地址改为智能解析（同源相对路径 / 本地自动指向 :8000） |
| `backend/app/core/config.py` | 在 Vercel 上把上传上限收紧到 4 MB（平台限制） |

本地验证（可选）：

```bash
cd myp-auditor
./scripts/verify_vercel_entry.sh
```

会依次检查 `/api/health`、`/`、`/app.js`、`/styles.css`、`/docs`，
并在存在 `../test_task.pdf` 时跑一次真实的端到端审计。

## 二、把代码推送到 GitHub

```bash
cd myp-auditor
git add .
git commit -m "chore: add Vercel deployment config (index.py, vercel.json)"
git push origin main
```

## 三、在 Vercel 官网导入仓库

1. 打开 <https://vercel.com/new>（或登录后进入 **Add New… → Project**）。
2. 在 **Import Git Repository** 列表里找到 `Verawuvw/myp-assessment-auditor`。
   - 若列表为空，点击 **Adjust GitHub App Permissions** / **Configure GitHub App**，
     授权 Vercel 访问该仓库后返回即可看到。
3. 点击仓库右侧的 **Import**。

### 项目配置（Configure Project 页面）

| 设置项 | 应填写的值 |
| --- | --- |
| **Project Name** | `myp-assessment-auditor`（或任意，决定默认域名） |
| **Framework Preset** | 选择 **FastAPI**（若下拉中没有，选 **Other**） |
| **Root Directory** | `./`（保持默认；仓库根就是项目根） |
| **Build & Output Settings** | **全部留空 / 保持默认**，不需要 Build Command |
| **Node.js Version** | 无需设置（本项目不使用 Node） |
| **Environment Variables** | 见下一节 |

> **重要**：不要设置 Root Directory 为 `backend`。根目录的 `index.py` 和
> `requirements.txt` 是 Vercel 的识别依据。

## 四、配置环境变量

在 **Configure Project → Environment Variables**（部署后也可在
**Project → Settings → Environment Variables** 修改）添加以下变量。
三个环境都勾选（Production / Preview / Development）：

| 变量名 | 值 | 必填 | 说明 |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | 你的 DeepSeek 密钥 | ✅ 必填 | 未配置时 `/api/audit` 返回 503 |
| `OPENAI_BASE_URL` | `https://api.deepseek.com` | ✅ 必填 | 指向 DeepSeek 兼容接口 |
| `OPENAI_MODEL` | `deepseek-chat` | 推荐 | 默认模型 |
| `MYP_MAX_UPLOAD_BYTES` | `4194304` | 可选 | 上传上限（字节）；Vercel 默认已是 4 MB |
| `MYP_CORS_ORIGINS` | 留空或 `*` | 可选 | 同源部署无需配置 |

> `.env` 文件已通过 `.gitignore` 排除，**不会**被推送到 GitHub；线上只认
> Vercel 仪表盘里配置的环境变量。

填完后点击 **Deploy**，等待约 1–3 分钟完成构建。

## 五、部署后验证

部署成功后 Vercel 会给出类似 `https://myp-assessment-auditor.vercel.app` 的域名。

1. 打开首页 → 应看到上传界面。
2. 打开健康检查：`https://<你的域名>/api/health` → 应返回：

   ```json
   {"status":"ok","version":"0.1.0","model":"deepseek-chat","api_key_configured":true}
   ```

   - 若 `api_key_configured` 为 `false`：环境变量没生效，去
     **Settings → Environment Variables** 检查，**改完必须重新部署**
     （Deployments → 最新部署 → ⋯ → Redeploy）才会生效。
3. 上传一个 PDF，确认能生成审计报告。

## 六、注意事项与已知限制

- **请求体上限约 4.5 MB**：这是 Vercel Serverless Functions 的硬性限制，
  与代码无关。本项目已在 Vercel 环境下把校验上限设为 4 MB，超出会返回明确的
  413 错误。若需支持更大的 PDF，需要改用 Vercel Blob 直传等方案。
- **执行时长**：审计要调用大模型，`vercel.json` 中已设置 `maxDuration: 60`
  （秒）。若报告较长导致超时，可调大该值（需符合你所选套餐的上限）。
- **冷启动**：Serverless 首次请求可能有几秒冷启动，属正常现象。
- **本地开发**：本地仍按原方式运行（后端 :8000、前端 :3000），
  `frontend/app.js` 会自动探测并指向 `http://127.0.0.1:8000`。
