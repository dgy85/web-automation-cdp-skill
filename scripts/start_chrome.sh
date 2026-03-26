#!/bin/bash
# 启动带远程调试端口的 Chrome

# 配置
DEBUG_PORT=${DEBUG_PORT:-9222}
CHROME_PATH=${CHROME_PATH:-""}
USER_DATA_DIR=${USER_DATA_DIR:-"/tmp/chrome-cdp-profile"}

# 杀掉已有的 chrome 进程
pkill -f "chrome.*remote-debugging-port" 2>/dev/null || true
sleep 1

# 构建启动命令
if [ -n "$CHROME_PATH" ]; then
    CHROME_BIN="$CHROME_PATH"
else
    CHROME_BIN=$(which google-chrome chromium chromium-browser 2>/dev/null | head -1)
fi

if [ -z "$CHROME_BIN" ]; then
    echo "❌ 未找到 Chrome/Chromium"
    exit 1
fi

echo "🔵 启动 Chrome，调试端口: $DEBUG_PORT"

# 启动 Chrome
"$CHROME_BIN" \
    --remote-debugging-port=$DEBUG_PORT \
    --user-data-dir="$USER_DATA_DIR" \
    --no-first-run \
    --no-default-browser-check \
    --disable-popup-blocking \
    --disable-infobars \
    --disable-dev-shm-usage \
    --disable-gpu \
    --window-size=1280,720 \
    --headless=new \
    "$@" &

sleep 2

# 检查是否启动成功
if curl -s "http://127.0.0.1:$DEBUG_PORT/json" > /dev/null 2>&1; then
    echo "✅ Chrome 已启动，调试端口: $DEBUG_PORT"
    echo "🌐 WebSocket: ws://127.0.0.1:$DEBUG_PORT"
    echo "📋 HTTP: http://127.0.0.1:$DEBUG_PORT/json"
else
    echo "❌ Chrome 启动失败"
    exit 1
fi