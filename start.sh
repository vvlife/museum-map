#!/bin/sh
# 博物馆世界地图 - 一键启动
cd "$(dirname "$0")"
if pgrep -f "python3 server.py" > /dev/null; then
  echo "✅ 服务器已在运行: http://localhost:8765/"
else
  nohup python3 server.py > server.log 2>&1 &
  sleep 2
  echo "🚀 服务器已启动: http://localhost:8765/"
fi
