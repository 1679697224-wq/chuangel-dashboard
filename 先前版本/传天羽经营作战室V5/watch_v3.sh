#!/bin/bash
# 看板V3 守护脚本：检测 8003 端口无响应则自动重启
# 用法：nohup bash watch_v3.sh > /tmp/v3_watch.log 2>&1 &
APP_DIR="/Users/siri/Desktop/APR项目/看板V3_老板反馈版"
PY="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"

while true; do
  # 检查端口是否有监听
  if ! lsof -i :8003 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "$(date '+%F %T') 端口未监听，重启服务" >> /tmp/v3_watch.log
    pkill -9 -f "app.py" 2>/dev/null
    sleep 1
    cd "$APP_DIR" && nohup "$PY" app.py > /tmp/v3_app.log 2>&1 &
    sleep 3
  else
    # 端口在监听但可能不响应，做一次 HTTP 探测
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:8003/ 2>/dev/null)
    if [ "$code" != "200" ]; then
      echo "$(date '+%F %T') HTTP 探测失败(code=$code)，重启服务" >> /tmp/v3_watch.log
      pkill -9 -f "app.py" 2>/dev/null
      sleep 1
      cd "$APP_DIR" && nohup "$PY" app.py > /tmp/v3_app.log 2>&1 &
      sleep 3
    fi
  fi
  sleep 30
done
