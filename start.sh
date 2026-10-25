#!/bin/bash
# ============================================
#   🍳 菜谱网站 - 一键启动脚本（跨平台）
#   新设备：git clone 后直接运行 ./start.sh
#   自动创建 Python 虚拟环境、安装依赖、检查数据
# ============================================
cd "$(dirname "$0")"

BACKEND_PORT=9527
FRONTEND_PORT=5180
ROOT="$PWD"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

# ---------- 清理旧进程 ----------
echo -e "${YELLOW}🔧 清理旧进程...${NC}"
if command -v lsof >/dev/null 2>&1; then
  lsof -ti:$BACKEND_PORT 2>/dev/null | xargs kill 2>/dev/null || true
  lsof -ti:$FRONTEND_PORT 2>/dev/null | xargs kill 2>/dev/null || true
fi
sleep 0.5

# ---------- Python 环境（缺失自动创建） ----------
PY=python3
command -v $PY >/dev/null 2>&1 || PY=python

if [ ! -x "backend/venv/bin/python" ] || ! backend/venv/bin/python -c "import fastapi, uvicorn, sqlalchemy" >/dev/null 2>&1; then
  echo -e "${GREEN}📦 首次运行：创建 Python 虚拟环境并安装依赖（推荐 Python 3.10~3.13）...${NC}"
  rm -rf backend/venv
  $PY -m venv backend/venv || { echo -e "${RED}❌ 创建虚拟环境失败，请先安装 Python 3.10+${NC}"; exit 1; }
  backend/venv/bin/pip install --upgrade pip -q
  backend/venv/bin/pip install -q -r backend/requirements.txt || { echo -e "${RED}❌ 依赖安装失败，请检查网络${NC}"; exit 1; }
fi

# ---------- 数据守卫：数据库必须有数据才启动 ----------
RECIPES=$(backend/venv/bin/python - <<'PYEOF'
import os, sqlite3
path = "backend/recipes.db"
if not os.path.exists(path) or os.path.getsize(path) == 0:
    print(0)
else:
    try:
        print(sqlite3.connect(path).execute("select count(*) from recipes").fetchone()[0])
    except Exception:
        print(0)
PYEOF
)
if [ "${RECIPES:-0}" -eq 0 ] 2>/dev/null; then
  echo -e "${RED}❌ backend/recipes.db 不存在或没有数据，拒绝启动空站点！${NC}"
  echo -e "${RED}   数据库随仓库一起提交，请确认是完整 clone（git lfs / 浅克隆可能缺文件）。${NC}"
  exit 1
fi
echo -e "${GREEN}💾 数据检查通过：${RECIPES} 条菜谱${NC}"

# ---------- 前端依赖（缺失自动安装） ----------
if [ ! -d frontend/node_modules ]; then
  echo -e "${GREEN}📦 安装前端依赖...${NC}"
  (cd frontend && npm install) || { echo -e "${RED}❌ 前端依赖安装失败，请检查 Node.js（需 20+）与网络${NC}"; exit 1; }
fi

# ---------- 启动后端 ----------
echo -e "${GREEN}🚀 启动后端 (port $BACKEND_PORT)...${NC}"
(cd backend && exec ./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT) > /tmp/recipe-backend.log 2>&1 &
BACKEND_PID=$!

# ---------- 启动前端 ----------
echo -e "${GREEN}🚀 启动前端 (port $FRONTEND_PORT)...${NC}"
(cd frontend && exec npm run dev) > /tmp/recipe-frontend.log 2>&1 &
FRONTEND_PID=$!

# ---------- 等待就绪 ----------
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
for i in $(seq 1 30); do
  if curl -s -o /dev/null http://localhost:$BACKEND_PORT/docs 2>/dev/null && \
     curl -s -o /dev/null http://localhost:$FRONTEND_PORT 2>/dev/null; then
    break
  fi
  sleep 1
done

# ---------- 局域网 IP（macOS / Linux 各自尝试） ----------
IP=""
command -v ipconfig >/dev/null 2>&1 && IP=$(ipconfig getifaddr en0 2>/dev/null || true)
if [ -z "$IP" ] && command -v hostname >/dev/null 2>&1; then
  IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi
[ -z "$IP" ] && IP="127.0.0.1"

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  🍳 菜谱网站已启动${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "  ${GREEN}前端:${NC}  http://$IP:$FRONTEND_PORT"
echo -e "  ${GREEN}后端:${NC}  http://$IP:$BACKEND_PORT/docs"
echo ""
echo -e "  ${YELLOW}手机请访问前端地址（需同一 WiFi）${NC}"
echo -e "  ${YELLOW}日志: /tmp/recipe-backend.log /tmp/recipe-frontend.log${NC}"
echo -e "  ${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

cleanup() {
  echo ""
  echo -e "${YELLOW}🛑 正在停止服务...${NC}"
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  if command -v lsof >/dev/null 2>&1; then
    lsof -ti:$BACKEND_PORT 2>/dev/null | xargs kill 2>/dev/null || true
    lsof -ti:$FRONTEND_PORT 2>/dev/null | xargs kill 2>/dev/null || true
  fi
  echo -e "${GREEN}✅ 已停止${NC}"
  exit 0
}
trap cleanup SIGINT SIGTERM

wait
