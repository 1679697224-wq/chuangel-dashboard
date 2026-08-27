#!/bin/bash
# 每日自动抓取客流并更新看板
# 用法: ./run_daily.sh [YYYY/MM/DD 结束日期]   （默认：月初 ~ 昨天）
cd "$(dirname "$0")"

BEGIN=$(date +%Y/%m/01)
END=$(date -v-1d +%Y/%m/%d 2>/dev/null || date +%Y/%m/%d)

if [ -n "$1" ]; then END="$1"; fi

echo "===== $(date '+%Y-%m-%d %H:%M:%S') 开始抓取 $BEGIN ~ $END =====" | tee -a data/daily.log

node fetch_flow.js "$BEGIN" "$END" 2>&1 | tee -a data/daily.log
FLOW_OK=${PIPESTATUS[0]}

if [ $FLOW_OK -ne 0 ]; then
  echo "❌ 抓取失败（可能是验证码），请人工处理 captcha_manual.png" | tee -a data/daily.log
  exit 1
fi

node fill_dashboard.js 2>&1 | tee -a data/daily.log

echo "===== 完成 =====" | tee -a data/daily.log
