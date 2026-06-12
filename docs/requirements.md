# 我的菜谱 - 需求文档

## 项目概述

手机端友好的个人菜谱网站，前后端分离的工程化项目。每个菜谱配有图片，支持通过对话方式添加菜谱。菜谱会逐步丰富，有时用户只提供菜名，由 AI 补充完整做法。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vite + React 19 + TypeScript + Tailwind CSS v4 | 响应式手机端优先 |
| 后端 | Python 3 + FastAPI | 轻量高效，自带 Swagger 文档 |
| 数据库 | SQLite + SQLAlchemy | 零配置，个人项目完美选择 |
| 图片生成 | ComfyUI API | 异步文生图，通过后端代理调用 |
| 菜谱 AI | OpenAI 兼容接口 (MiMo v2 Pro) | 对话生成菜谱做法 |

## 功能清单

### 1. 菜谱管理

- **首页展示**：卡片式布局，手机单列 → 平板双列 → 桌面三列
- **分类筛选**：家常菜、汤羹、快手菜、甜品、凉菜、主食、烧烤、饮品
- **搜索**：按菜名模糊搜索
- **添加菜谱**：表单录入（菜名、分类、难度、时间、食材、步骤、小贴士）
- **编辑菜谱**：修改已有菜谱信息
- **删除菜谱**：确认后删除
- **收藏功能**：收藏/取消收藏，收藏列表独立展示

### 2. 图片功能

- **图片上传**：本地拍照或选择图片上传
- **AI 图片生成**：输入菜名，通过 ComfyUI 异步生成美食图片
- **异步流程**：提交生成任务 → 轮询状态 → 完成后展示图片
- **图片显示**：完整显示不裁切（object-contain），卡片和详情页适配

### 3. 对话式添加菜谱

- **聊天界面**：消息气泡列表，用户消息右侧，系统消息左侧
- **菜谱知识库**：内置 12+ 常见中式菜肴，快速匹配
- **AI 生成**：知识库中没有的菜，调用 AI API 智能生成
- **交互流程**：
  1. 用户输入菜名（如「红烧排骨」）
  2. 系统生成菜谱预览（食材 + 做法）
  3. 用户确认 / 修改 / 放弃
  4. 确认后保存到数据库
- **带要求生成**：用户可附加要求（如「宫保鸡丁，花生多放点」）
- **图片生成**：菜谱确认后可一键生成配套图片

## 页面结构

```
底部 Tab 导航：
├── 🏠 首页     — 菜谱卡片列表 + 搜索 + 分类筛选
├── 💬 对话     — 聊天界面添加菜谱
├── ❤️ 收藏     — 收藏的菜谱列表
└── ➕ 添加     — 表单添加菜谱
```

## API 设计

### 菜谱 API

```
GET    /api/recipes              # 菜谱列表（?category=&search=&page=&size=）
GET    /api/recipes/{id}         # 菜谱详情
POST   /api/recipes              # 创建菜谱
PUT    /api/recipes/{id}         # 更新菜谱
DELETE /api/recipes/{id}         # 删除菜谱
POST   /api/recipes/{id}/favorite  # 切换收藏
```

### 分类 API

```
GET    /api/categories           # 分类列表
POST   /api/categories           # 创建分类
```

### 图片 API

```
POST   /api/images/upload        # 上传图片
POST   /api/images/generate      # 同步生成图片（内部调用 ComfyUI）
POST   /api/images/generate-async # 异步生成（返回任务 ID）
GET    /api/images/status/{id}   # 查询生成状态
```

### 对话 API

```
POST   /api/chat                 # 发送消息
请求: { "message": "菜名", "session_id": "xxx" }
响应: { "type": "recipe_preview|confirm|text", "message": "...", "recipe": {...} }
```

## 数据模型

### Recipe（菜谱）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| name | str | 菜名 |
| category_id | int | 外键关联分类 |
| image_url | str | 图片路径 |
| ingredients | str | JSON 字符串存储食材列表 |
| steps | str | JSON 字符串存储步骤列表 |
| difficulty | str | 简单 / 中等 / 较难 |
| cook_time | str | 烹饪时间 |
| tips | str | 小贴士 |
| is_favorite | bool | 是否收藏 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### Category（分类）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| name | str | 分类名 |
| icon | str | 分类图标（emoji） |

## 环境变量配置

```env
# ComfyUI 图片生成
COMFYUI_API_URL=http://47.93.230.201:6677
COMFYUI_API_KEY=xsk_xxx

# AI 菜谱生成（OpenAI 兼容接口）
RECIPE_AI_API_URL=https://token-plan-sgp.xiaomimimo.com/v1
RECIPE_AI_API_KEY=tp-xxx
RECIPE_AI_MODEL=mimo-v2-pro
```

## 项目结构

```
recipe-website/
├── frontend/                      # 前端 React 项目
│   ├── src/
│   │   ├── components/
│   │   │   ├── RecipeCard.tsx     # 菜谱卡片
│   │   │   ├── RecipeDetail.tsx   # 菜谱详情
│   │   │   ├── RecipeForm.tsx     # 添加/编辑表单
│   │   │   ├── CategoryFilter.tsx # 分类筛选
│   │   │   ├── SearchBar.tsx      # 搜索栏
│   │   │   └── ChatPage.tsx       # 对话界面
│   │   ├── api/
│   │   │   └── index.ts           # API 请求封装
│   │   ├── types/
│   │   │   └── recipe.ts          # 类型定义
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                       # 后端 FastAPI 项目
│   ├── app/
│   │   ├── main.py                # FastAPI 入口
│   │   ├── config.py              # 配置管理
│   │   ├── database.py            # 数据库连接
│   │   ├── models/
│   │   │   └── recipe.py          # SQLAlchemy 模型
│   │   ├── schemas/
│   │   │   └── recipe.py          # Pydantic 模型
│   │   ├── routers/
│   │   │   ├── recipes.py         # 菜谱 CRUD
│   │   │   ├── categories.py      # 分类 API
│   │   │   ├── images.py          # 图片上传 & 生成
│   │   │   └── chat.py            # 对话 API
│   │   └── services/
│   │       ├── image_service.py   # ComfyUI 图片生成
│   │       └── recipe_chat.py     # 菜谱知识库 & AI 对话
│   ├── uploads/                   # 图片存储
│   ├── requirements.txt
│   └── .env
│
└── docs/
    └── requirements.md            # 本文档
```

## 快速启动

### 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API 文档：<http://localhost:8000/docs>

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问：<http://localhost:5173>

## 设计风格

- **暖色调主题**：橙色/棕色系，契合美食主题
- **卡片设计**：圆角卡片 + 阴影
- **手机端优先**：底部 Tab 导航，触摸友好
- **图片显示**：object-contain 完整展示，不裁切

## 额外想法

1. 拍照上传 — 手机端直接拍照上传菜谱图片（上传功能已有，可以加 <input capture="camera"> 直接调起相机）
2. 食材购物清单 — 选择要做几道菜，自动合并相同食材，生成购物清单
3. 烹饪日记 — 记录做过的菜和日期，形成做菜历史
4. 分享卡片 — 生成精美菜谱卡片图片，方便分享到朋友圈
5. 语音朗读做法 — 做菜时手不方便，用 Web Speech API 语音播放步骤
