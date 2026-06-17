#!/bin/bash
# ============================================
#   🍳 菜谱网站 - 一键启动脚本
# ============================================

cd "$(dirname "$0")"

BACKEND_PORT=9527
FRONTEND_PORT=5180

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# 停止旧进程
echo -e "${YELLOW}🔧 清理旧进程...${NC}"
lsof -ti:$BACKEND_PORT 2>/dev/null | xargs kill 2>/dev/null
lsof -ti:$FRONTEND_PORT 2>/dev/null | xargs kill 2>/dev/null
sleep 0.5

# 启动后端
echo -e "${GREEN}🚀 启动后端 (port $BACKEND_PORT)...${NC}"
cd "$PWD/backend"
source venv/bin/activate 2>/dev/null
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > /tmp/recipe-backend.log 2>&1 &
BACKEND_PID=$!
cd "$PWD/.."

# 启动前端
echo -e "${GREEN}🚀 启动前端 (port $FRONTEND_PORT)...${NC}"
cd "$PWD/frontend"
nohup npm run dev > /tmp/recipe-frontend.log 2>&1 &
FRONTEND_PID=$!
cd "$PWD/.."

# 等待服务就绪
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
for i in $(seq 1 15); do
    if curl -s -o /dev/null http://localhost:$BACKEND_PORT/docs 2>/dev/null && \
       curl -s -o /dev/null http://localhost:$FRONTEND_PORT 2>/dev/null; then
        break
    fi
    sleep 1
done

# 获取 IP
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "未知")

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  🍳 菜谱网站已启动${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "  ${GREEN}前端:${NC}  http://$IP:$FRONTEND_PORT"
echo -e "  ${GREEN}后端:${NC}  http://$IP:$BACKEND_PORT/docs"
echo ""
echo -e "  ${YELLOW}手机请访问前端地址（需同一 WiFi）${NC}"
echo -e "  ${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 捕获 Ctrl+C，停止所有服务
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 正在停止服务...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    lsof -ti:$BACKEND_PORT 2>/dev/null | xargs kill 2>/dev/null
    lsof -ti:$FRONTEND_PORT 2>/dev/null | xargs kill 2>/dev/null
    echo -e "${GREEN}✅ 已停止${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# 保持前台运行
wait
