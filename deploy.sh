#!/bin/sh
# 重建静态版并部署到 surge.sh（国内可达公网）
cd "$(dirname "$0")"
python3 build_static.py
. /tmp/surge_env.sh
surge --project docs --domain musea-orbis.surge.sh
rm -f docs/CNAME
