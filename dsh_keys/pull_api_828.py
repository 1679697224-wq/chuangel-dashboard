# -*- coding: utf-8 -*-
"""吉客云 API 拉取：销售(8/1-28, 实付) + 库存(现存量)"""
import json, time, re, sys
from datetime import datetime, timedelta
from collections import defaultdict
sys.path.insert(0, '/Users/lili/Desktop/deepseek harness/dsh_keys')
from jky_real import call

ROOT = "/Users/lili/Desktop/deepseek harness/吉客云数据"

def pull_sales(start, end):
    trades = []
    scroll = ""
    for _ in range(400):
        biz = {
            "fields": "tradeId,tradeNo,tradeStatus,shopName,warehouseName,consignTime,payTime,seller,payment",
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
        except Exception as e:
            print('ERR', str(e)[:100], r[:120])
            break
        time.sleep(0.08)
    return trades

print('== 拉销售 8/1-8/28 ==')
all_t = []
cur = datetime(2026, 8, 1)
end = datetime(2026, 8, 28, 23, 59, 59)
while cur < end:
    we = min(cur + timedelta(days=6), end)
    t = pull_sales(cur, we)
    print('  窗口 %s~%s: %d 单' % (cur.date(), we.date(), len(t)))
    all_t.extend(t)
    cur = we + timedelta(days=1)
json.dump(all_t, open(ROOT + '/sales_raw_20260828.json', 'w'), ensure_ascii=False)
print('总单数:', len(all_t))
# 付款时间过滤 8/1-8/27
t27 = [x for x in all_t if x.get('payTime', '').startswith('2026-08') and x['payTime'][8:10] <= '27']
print('付款 8/1-27 单数:', len(t27), '| 实付:', round(sum(float(x.get('payment') or 0) for x in t27), 2))

print()
print('== 拉库存（现存量）==')
inv = []
max_id = 0
for _ in range(600):
    biz = {"pageIndex": 0, "pageSize": 200, "maxQuantityId": max_id}
    r = call("erp.stockquantity.get", biz)
    try:
        d = json.loads(r)
        data = d["result"]["data"]
        rows = data.get("goodsStockQuantity") or data.get("rows") or []
        inv.extend(rows)
        new_max = 0
        for row in rows:
            mq = row.get('maxQuantityId') or row.get('quantityId') or 0
            if mq: new_max = max(new_max, int(mq))
        if not rows or new_max <= max_id:
            break
        max_id = new_max
    except Exception as e:
        print('ERR', str(e)[:100], r[:150])
        break
    time.sleep(0.08)
json.dump(inv, open(ROOT + '/inventory_raw_0828.json', 'w'), ensure_ascii=False)
print('库存行数:', len(inv))
if inv:
    print('字段:', list(inv[0].keys())[:15])
