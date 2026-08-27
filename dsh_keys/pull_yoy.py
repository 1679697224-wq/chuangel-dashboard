# -*- coding: utf-8 -*-
"""拉去年8月销售(按发货窗口)并聚合同比"""
import json, time, re
from datetime import datetime, timedelta
from collections import defaultdict
from jky_real import call

def pull(start, end):
    trades = []
    scroll = ""
    for _ in range(300):
        biz = {
            "fields": "tradeId,tradeNo,tradeStatus,shopName,payTime,payment",
            "pageSize": 200,
            "startConsignTime": start.strftime("%Y-%m-%d %H:%M:%S"),
            "endConsignTime": end.strftime("%Y-%m-%d %H:%M:%S"),
            "scrollId": scroll,
        }
        r = call("oms.trade.fullinfoget", biz)
        try:
            d = json.loads(r)
            data = d["result"]["data"]
            batch = data.get("trades") or []
            trades.extend(batch)
            scroll = data.get("scrollId") or ""
            if not batch or not scroll:
                break
        except Exception:
            break
        time.sleep(0.1)
    return trades

def norm_shop(s):
    return re.sub(r'^\[[0-9]{3}\]', '', str(s)).strip().rstrip('*').strip()

all_t = []
cur = datetime(2025, 8, 1)
end = datetime(2025, 8, 27)
while cur < end:
    we = min(cur + timedelta(days=6), end)
    t = pull(cur, we)
    print(f'窗口 {cur.date()}~{we.date()}: {len(t)} 单')
    all_t.extend(t)
    cur = we + timedelta(days=1)

json.dump(all_t, open('/Users/lili/Desktop/deepseek harness/吉客云数据/sales_raw_202508.json', 'w', encoding='utf-8'), ensure_ascii=False)
total = sum(float(x.get('payment') or 0) for x in all_t)
print('2025-08 单数:', len(all_t), '| 金额(实付):', round(total, 2))
