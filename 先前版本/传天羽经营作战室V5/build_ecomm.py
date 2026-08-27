#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从吉客云拉取电商网店订单，按平台（京东羽通/苏宁啟韬/舒尔各平台）聚合 → ecomm_platform.json
用法: python3 build_ecomm.py [天数]  默认近7天
"""
import sys, os, json, time, ssl
from datetime import datetime, timedelta

# 跳过 SSL 证书验证（本地原型工具，MCP 端点证书不受信）
ssl._create_default_https_context = ssl._create_unverified_context

BASE = os.path.expanduser("~/.openclaw/workspace/scripts")
sys.path.insert(0, BASE)
from daily_jky_report import mcp_call

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecomm_platform.json")

def normalize_platform(shop):
    s = str(shop or "")
    if "羽通" in s:
        return "京东羽通"
    if "啟韬" in s or "启韬" in s:
        return "苏宁啟韬"
    if "舒尔" in s:
        if "天猫" in s:
            return "舒尔·天猫"
        if "京东" in s:
            return "舒尔·京东"
        return "舒尔·其他"
    if "天猫" in s:
        return "天猫·其他"
    if "京东" in s:
        return "京东·其他"
    if "抖音" in s:
        return "抖音"
    return "其他"

def fetch_orders(ds):
    orders = []
    page = 0
    while page < 300:
        r = mcp_call("getShopOrderLiseInfo", {
            "pageIndex": str(page), "pageSize": "10",
            "fields": "tradeOnline.tradeNo,tradeOnline.payment,tradeOnline.shopName,tradeOnline.createTime",
            "createTimeBegin": f"{ds} 00:00:00", "createTimeEnd": f"{ds} 23:59:59",
        })
        if not r:
            break
        batch = r if isinstance(r, list) else r.get("tradeOnlineList", [])
        if not batch:
            break
        orders.extend(batch)
        if len(batch) < 10:
            break
        page += 1
        time.sleep(0.15)
    return orders

def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    data = {}
    today = datetime.now()
    for i in range(days):
        ds = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        print(f"拉取 {ds} ...", flush=True)
        orders = fetch_orders(ds)
        day = {}
        for o in orders:
            p = normalize_platform(o.get("shopName"))
            pay = float(o.get("payment") or 0)
            d = day.setdefault(p, {"amount": 0.0, "orders": 0})
            d["amount"] += pay
            d["orders"] += 1
        data[ds] = {k: {"amount": round(v["amount"], 2), "orders": v["orders"]} for k, v in day.items()}
        print(f"  {ds}: {len(orders)}单", flush=True)
    with open(OUT, "w") as f:
        json.dump({"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "days": data}, f, ensure_ascii=False, indent=1)
    print("完成 →", OUT)

if __name__ == "__main__":
    main()
