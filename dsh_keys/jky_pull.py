# -*- coding: utf-8 -*-
"""吉客云全量拉取：8月销售(按支付时间) + 当前库存，套用桌面映射表聚合"""
import json, time, hashlib, urllib.request, urllib.parse
from datetime import datetime, timedelta
from collections import defaultdict

from jky_real import call, signed_body, APPKEY

OUT = "/Users/lili/Desktop/deepseek harness/吉客云数据"

def pull_sales(start, end):
    """按发货时间窗口拉销售（7天窗口），scrollId 翻页"""
    trades = []
    scroll = ""
    for _ in range(300):
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
            print("  拉取异常:", str(e)[:120], r[:200])
            break
        time.sleep(0.12)
    return trades

def pull_inventory():
    rows = []
    max_id = "0"
    for _ in range(2000):
        biz = {"pageIndex": 0, "pageSize": 200, "maxQuantityId": max_id}
        r = call("erp.stockquantity.get", biz)
        try:
            d = json.loads(r)
            data = d["result"]["data"]
            batch = data.get("goodsStockQuantity") or []
            rows.extend(batch)
            if not batch:
                break
            max_id = str(batch[-1].get("quantityId") or max_id)
            if len(batch) < 200:
                break
        except Exception as e:
            print("库存异常:", str(e)[:120], r[:200])
            break
        time.sleep(0.12)
    return rows

if __name__ == "__main__":
    print("== 拉取 8 月销售 ==")
    all_trades = []
    start = datetime(2026, 8, 1)
    end = datetime.now()
    cur = start
    while cur < end:
        win_end = min(cur + timedelta(days=6), end)
        print(f"窗口 {cur.date()} ~ {win_end.date()} ...", flush=True)
        trades = pull_sales(cur, win_end)
        print(f"  得到 {len(trades)} 单", flush=True)
        all_trades.extend(trades)
        cur = win_end + timedelta(days=1)

    with open(OUT + "/sales_raw_202608.json", "w", encoding="utf-8") as f:
        json.dump(all_trades, f, ensure_ascii=False, indent=1)
    print("销售原始单数:", len(all_trades))

    print("== 拉取库存 ==")
    inv = pull_inventory()
    with open(OUT + "/inventory_raw.json", "w", encoding="utf-8") as f:
        json.dump(inv, f, ensure_ascii=False, indent=1)
    print("库存SKU-仓记录数:", len(inv))
