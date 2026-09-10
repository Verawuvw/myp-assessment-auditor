# MYP Auditor

对 IB MYP summative assessment 任务 PDF 进行「概念性理解审计」（Conceptual
Understanding Audit）的独立产品项目。后端基于 FastAPI，前端提供简洁的上传界面。

## 目录结构

```
myp-auditor/
├── backend/
│   ├── main.py                # FastAPI 入口（含 CORS、健康检查、路由挂载）
│   ├── cli.py                 # 可选命令行入口，复用核心逻辑
│   ├── requirements.txt       # Python 依赖
│   └── app/
│       ├── __init__.py
│       ├── core/              # 框架无关的基础能力
│       │   ├── config.py      # 环境变量配置（Settings）
│       │   ├── prompts.py     # 提示词装配
│       │   ├── prompt_zh.py   # 中文系统提示词
│       │   └── prompt_en.py   # 英文系统提示词
│       ├── services/          # 业务逻辑（抽取自 myp_audit.py）
│       │   ├── pdf.py         # PDF 文本抽取
│       │   ├── language.py    # 报告语言检测
│       │   └── auditor.py     # OpenAI 调用与端到端审计
│       └── api/
│           └── routes/
│               └── audit.py   # POST /api/audit 路由
└── frontend/
    ├── index.html             # 上传界面
    ├── styles.css
    └── app.js                 # 调用 /api/audit
```

## 快速开始

### 1. 安装依赖

```bash
cd myp-auditor/backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

后端启动时会**自动加载** `backend/.env`（已存在的系统环境变量优先，不会被覆盖）。

在 `backend/` 下创建 `.env`：

```dotenv
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
```

也可以直接用系统环境变量（会覆盖 `.env` 中的同名项）：

```bash
export OPENAI_API_KEY="你的密钥"
# 可选：
export OPENAI_BASE_URL="https://api.deepseek.com"  # 兼容的代理/网关地址
export OPENAI_MODEL="deepseek-chat"                # 默认模型
export MYP_MAX_UPLOAD_BYTES="20971520"             # 单文件体积上限（默认 20 MB）
export MYP_CORS_ORIGINS="http://localhost:5173"    # 多个用英文逗号分隔
```

### 3. 启动后端

```bash
uvicorn main:app --reload --port 8000
# 或：python main.py
```

- 接口文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/health>

### 4. 打开前端

直接用浏览器打开 `frontend/index.html` 即可（也可用任意静态服务器托管）。
若前后端不同源，请修改 `frontend/app.js` 中的 `API_BASE` 为后端地址。

## API 说明

### `POST /api/audit`

以 `multipart/form-data` 上传 PDF。

| 字段    | 类型        | 必填 | 说明                                   |
| ------- | ----------- | ---- | -------------------------------------- |
| `file`  | File        | 是   | MYP 评估任务 PDF                       |
| `lang`  | Form string | 否   | `auto`(默认) / `zh` / `en`             |
| `model` | Form string | 否   | 覆盖后端默认模型                       |

示例：

```bash
curl -X POST http://127.0.0.1:8000/api/audit \
  -F "file=@test_task.pdf" \
  -F "lang=auto"
```

成功响应（JSON）：

```json
{
  "file_name": "test_task.pdf",
  "language": "zh",
  "model": "gpt-4o-mini",
  "report": "……Markdown 审计报告……",
  "task_text": "……从 PDF 抽取的文本……"
}
```

错误码：

| 状态码 | 含义                              |
| ------ | --------------------------------- |
| 400    | 文件类型/语言参数不合法、文件为空 |
| 413    | 文件超过体积上限                  |
| 422    | PDF 无法解析或未提取到文本        |
| 502    | 模型未返回内容等上游错误          |
| 503    | 未配置 `OPENAI_API_KEY`           |

## 命令行用法（可选）

```bash
cd myp-auditor/backend
python cli.py ../test_task.pdf --lang zh --save
# 生成 ../test_task.audit.md
```

## 后续扩展建议

- **持久化**：在 `app/services/` 下新增 `storage.py`，把审计记录写入数据库，
  `AuditResult` 已是独立数据类，便于序列化。
- **异步任务**：大文件或长报告可挂到 Celery/RQ，接口返回 job id 轮询结果。
- **多模型/多提示词**：提示词集中在 `app/core/prompts.py`，新增语言或风格只需加一个模块。
- **鉴权与限流**：在 `main.py` 添加 FastAPI 依赖（`Depends`）即可统一注入。
- **前端框架化**：当前为原生实现，可直接替换为 React/Vue，接口契约不变。

## 与原始 `myp_audit.py` 的关系

原始单文件脚本的核心逻辑（PDF 抽取、语言检测、OpenAI 调用、中/英提示词）
已原样抽取到本项目的模块中；原脚本仍可独立使用，本项目为可部署的独立产品形态。
