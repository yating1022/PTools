# P Tools

个人工具集 Web 应用。

## Tech Stack

- **Frontend:** Vue 3 + Vite + TypeScript + Tailwind CSS + Pinia
- **Design:** Solarpunk（太阳朋克）生态未来主义风格
- **Backend:** FastAPI + Python 3.11+ + httpx + SQLAlchemy + MySQL

## Project Structure

```
p/
├── frontend/          # Vue 3 前端
│   ├── src/
│   │   ├── api/       # API 请求封装
│   │   ├── views/     # 页面组件
│   │   ├── stores/    # Pinia 状态管理
│   │   ├── composables/  # 组合式函数
│   │   └── types/     # TypeScript 类型定义
│   └── ...
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/    # 路由层
│   │   ├── services/  # 业务逻辑层
│   │   └── clients/   # 外部 API 客户端
│   └── ...
├── solarpunk-hard-prompt.md  # Solarpunk 设计规范（硬约束）
└── .trellis/          # Trellis 项目管理
```

## Quick Start

### Backend

```bash
cd backend
pip install -e .
# 编辑 config.yaml 填入 token（可选，也可通过前端登录）
python -m app.main
```

后端运行在 `http://localhost:7679`。

### Frontend

```bash
cd frontend
npm install
npm run dev
```

前端运行在 `http://localhost:7678`，自动代理 `/api` 请求至后端。

## Modules

| Module | Path | Description |
|--------|------|-------------|
| 光鸭网盘 | `/tools/gy-netdisk` | 文件管理与云下载（guangyapan.com） |

## Development Guidelines

项目规范见 `.trellis/spec/`：

- **前端规范：** `.trellis/spec/frontend/` — Vue 3 + Solarpunk 设计系统
- **后端规范：** `.trellis/spec/backend/` — FastAPI 分层架构
- **设计系统：** `solarpunk-hard-prompt.md` — 样式硬约束，所有 UI 必须遵守

## Ports

| Service | Port |
|---------|------|
| Frontend (Vite dev) | 7678 |
| Backend (uvicorn) | 7679 |
