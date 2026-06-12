# 我的菜谱 🍳

手机端友好的个人菜谱网站，支持对话式添加菜谱和 AI 图片生成。

## 技术栈

- **前端**: Vite + React 19 + TypeScript + Tailwind CSS v4
- **后端**: Python 3 + FastAPI + SQLAlchemy + SQLite
- **图片生成**: ComfyUI API（异步文生图）
- **菜谱 AI**: MiMo v2 Pro（对话生成菜谱）

## 快速启动

### 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 配置环境变量
uvicorn app.main:app --reload --port 8000
```

API 文档：http://localhost:8000/docs

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:5173

## 功能

- 菜谱卡片展示（手机端自适应布局）
- 分类筛选 & 搜索
- 添加/编辑/删除菜谱
- 收藏功能
- 图片上传 & AI 图片生成
- **对话式添加菜谱**：输入菜名，AI 自动生成做法
- **菜谱知识库**：内置 12+ 常见中式菜肴
- **ComfyUI 文生图**：为菜谱生成配套美食图片

## 配置

环境变量在 `backend/.env` 中配置：

```env
# ComfyUI 图片生成
COMFYUI_API_URL=http://47.93.230.201:6677
COMFYUI_API_KEY=xsk_xxx

# AI 菜谱生成
RECIPE_AI_API_URL=https://token-plan-sgp.xiaomimimo.com/v1
RECIPE_AI_API_KEY=tp-xxx
RECIPE_AI_MODEL=mimo-v2-pro
```

## 文档

- [需求文档](docs/requirements.md) — 完整功能清单、API 设计、数据模型
