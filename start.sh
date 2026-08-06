#!/bin/sh
# 世界博物馆地图 · 一键启动（服务器 + 公网隧道）
cd "$(dirname "$0")"

if pgrep -f "python3 server.py" > /dev/null; then
  echo "✅ 服务器已在运行"
else
  nohup python3 server.py > server.log 2>&1 &
  sleep 2
  echo "🚀 服务器已启动: http://localhost:8765/"
fi

if pgrep -f "nokey@localhost.run" > /dev/null; then
  echo "✅ 公网隧道已在运行"
else
  echo "🌐 正在建立公网隧道..."
  nohup ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
    -R 80:localhost:8765 nokey@localhost.run > tunnel.log 2>&1 &
  sleep 15
  URL=$(grep -o "https://[a-z0-9.]*\.lhr\.life" tunnel.log | head -1)
  echo "🌍 公网地址: ${URL:-获取中，请查看 tunnel.log}"
fi
