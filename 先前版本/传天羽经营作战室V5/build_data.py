#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建看板V2数据：从 brief_web 的吉客云抓取数据生成 data.json
含：环比/上周同日/达成率预测/毛利毛利率等计算
"""
import json, os
from datetime import datetime, timedelta

BASE = os.path.expanduser("~/.openclaw/workspace/brief_web")
V2 = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(V2, "data.json")

def load(name):
    with open(os.path.join(BASE, name)) as f:
        return json.load(f)

def fmt_wan(v):
    """元 -> 万字符串"""
    return round(v / 10000, 1)

def pct(v):
    return round(v * 100, 1)

jky = load("jky_sales.json")
hist = load("jky_sales_history.json")
apr = load("apr_data.json")
inv = load("inventory.json")

today = jky["date"]  # 2026-08-11
today_dt = datetime.strptime(today, "%Y-%m-%d")
yest_dt = today_dt - timedelta(days=1)
lastwk_dt = today_dt - timedelta(days=7)
yest = yest_dt.strftime("%Y-%m-%d")
lastwk = lastwk_dt.strftime("%Y-%m-%d")

# ---------- 历史序列（近14天，补全） ----------
dates = sorted(hist.keys())
series = []
for d in dates:
    t = hist[d]["total"]
    ch = hist[d].get("channel", {})
    st = hist[d].get("stores", {})
    series.append({
        "date": d, "amount_wan": fmt_wan(t["amount"]), "orders": t["orders"],
        "channel": {k: {"amount_wan": fmt_wan(v["amount"]), "orders": v["orders"]} for k, v in ch.items()},
        "stores": st,
    })

# 今日（实时部分日）
today_total = jky["total"]
today_wan = fmt_wan(today_total["amount"])
today_orders = today_total["orders"]

def chan(d):
    return hist.get(d, {}).get("channel", {})

# 昨日 / 上周同日 对比
y_ch = chan(yest)
lw_ch = chan(lastwk)
def chan_sum(ch):
    return sum(v["amount"] for v in ch.values())

yest_total = hist.get(yest, {}).get("total", {})
lastwk_total = hist.get(lastwk, {}).get("total", {})

def chg(cur, prev):
    if not prev:
        return None
    return round((cur - prev) / prev * 100, 1)

# 渠道结构（今日 + 昨日环比 + 上周同日环比）
# 命名统一：羽通｜京东 / 啟韬｜苏宁 / Shure电商 / APR门店 / 3PP拓展（公司店铺名在前，平台在后）
PLATFORM_MAP = {"京东羽通": "羽通｜京东", "苏宁啟韬": "啟韬｜苏宁", "舒尔·天猫": "Shure·天猫", "舒尔·京东": "Shure·京东", "舒尔·其他": "Shure·其他", "天猫·其他": "天猫·其他", "京东·其他": "京东·其他"}
# 先加载电商分平台数据（供渠道拆分）
ecomm_platform = {}
if os.path.exists(os.path.join(V2, "ecomm_platform.json")):
    with open(os.path.join(V2, "ecomm_platform.json")) as f:
        ecomm_platform = json.load(f)

channels_today = []
for name, v in jky["channel"].items():
    if name == "Apple电商":
        # 用分平台数据拆分（ecomm_platform，取最新一天）；若无当天分平台数据则回退为聚合值
        ep_days = ecomm_platform.get("days", {}) if ecomm_platform else {}
        ep_today = ep_days.get(today, {}) if ep_days else {}
        if not ep_today:
            amt = v["amount"]
            channels_today.append({
                "name": "Apple电商",
                "amount_wan": fmt_wan(amt),
                "orders": v["orders"],
                "pct": round(amt / today_total["amount"] * 100, 1) if today_total["amount"] else 0,
                "yest_chg": None,
                "lastwk_chg": None,
            })
            continue
        for pname, pv in sorted(ep_today.items(), key=lambda x: -x[1]["amount"]):
            if pname.startswith("舒尔") or pname.startswith("Shure"):
                continue  # Shure 单独渠道，不混入 Apple 电商
            amt = pv["amount"]
            channels_today.append({
                "name": PLATFORM_MAP.get(pname, pname),
                "amount_wan": fmt_wan(amt),
                "orders": pv["orders"],
                "pct": round(amt / today_total["amount"] * 100, 1) if today_total["amount"] else 0,
                "yest_chg": None,
                "lastwk_chg": None,
            })
        continue
    amt = v["amount"]
    if name == "舒尔电商":
        name = "Shure电商"
    if name == "3PP拓展渠道":
        name = "3PP渠道"
    yv = y_ch.get(name, {}).get("amount")
    lv = lw_ch.get(name, {}).get("amount")
    channels_today.append({
        "name": name,
        "amount_wan": fmt_wan(amt),
        "orders": v["orders"],
        "pct": round(amt / today_total["amount"] * 100, 1) if today_total["amount"] else 0,
        "yest_chg": chg(amt, yv),
        "lastwk_chg": chg(amt, lv),
    })
# 固定顺序：APR门店 → Apple电商(羽通/啟韬) → Shure电商 → 3PP渠道 → 其他
CH_ORDER = ["APR门店", "Apple电商", "羽通｜京东", "啟韬｜苏宁", "Shure电商", "Shure·天猫", "Shure·京东", "Shure·其他", "3PP渠道"]
channels_today.sort(key=lambda x: (CH_ORDER.index(x["name"]) if x["name"] in CH_ORDER else 99, -x["amount_wan"]))

# 门店今日（合并 * 后缀线上店）
store_map = {}
for k, v in jky["stores"].items():
    key = k.replace("*", "").strip()
    if key not in store_map:
        store_map[key] = {"orders": 0, "amount": 0}
    store_map[key]["orders"] += v["orders"]
    store_map[key]["amount"] += v["amount"]

stores_today = sorted(
    [{"name": k, "amount_wan": fmt_wan(v["amount"]), "orders": v["orders"]}
     for k, v in store_map.items()],
    key=lambda x: -x["amount_wan"]
)

# ---------- APR 月度 ----------
monthly = apr["monthly"]
apr_sales = sum(v["sales"] for v in monthly.values())
apr_profit = sum(v["profit"] for v in monthly.values())
apr_orders = sum(v["orders"] for v in monthly.values())
apr_traffic = sum(v["traffic"] for v in monthly.values())
apr_conv = apr_orders / apr_traffic if apr_traffic else 0
apr_pm = apr_profit / apr_sales if apr_sales else 0
apr_task = sum(v["task"] for v in monthly.values())
apr_rate = apr_sales / apr_task if apr_task else 0

# 时间进度（8月已过天数 / 31）
days_passed = 10  # monthly 截至 8/10
time_progress = days_passed / 31

# 达成率预测：日均销售 * 31
daily_avg = apr_sales / days_passed
forecast_month_end = daily_avg * 31
forecast_rate = forecast_month_end / apr_task if apr_task else 0

stores_monthly = []
for name, v in monthly.items():
    stores_monthly.append({
        "name": name, "sales": round(v["sales"], 1), "task": v["task"],
        "rate": round(v["rate"] * 100, 1), "profit": round(v["profit"], 2),
        "pm": round(v["pm"] * 100, 2), "traffic": v["traffic"],
        "orders": v["orders"], "conv": round(v["conv"] * 100, 1),
        "apt": round(v["apt"] * 100, 1), "acs": round(v["acc"] * 100, 1),
        "pp": round(v["pp"] * 100, 1),
    })
stores_monthly.sort(key=lambda x: -x["sales"])

# 门店达成率预测
for s in stores_monthly:
    s["forecast"] = round(s["sales"] / days_passed * 31, 1)
    s["forecast_rate"] = round(s["forecast"] / s["task"] * 100, 1)

# 销售员
# 销售员：花名册全员接入（含无销售数据人员，显示待更新）
# 先加载花名册
roster = {}
if os.path.exists(os.path.join(V2, "roster.json")):
    with open(os.path.join(V2, "roster.json")) as f:
        roster = json.load(f)
salespersons = sorted(apr["salespersons"], key=lambda x: -x["sales"])
sp_out = []
rank = 0
for sp in salespersons:
    rank += 1
    sp_out.append({
        "rank": rank,
        "name": sp["name"], "store": sp["store"], "pos": sp.get("pos", ""),
        "task": sp.get("task"),
        "sales": sp["sales"], "rate": round(sp["rate"] * 100, 1),
        "offline": sp["offline"], "online": sp["online"],
        "pp_sales": sp.get("pp_sales"),
        "pp_rate": round(sp.get("pp_rate", 0) * 100, 1),
        "profit": sp["profit"], "profit_rank": sp.get("profit_rank"),
        "profit_rate": round(sp.get("profit_rate", 0) * 100, 1),
        "offline_profit_rate": round(sp.get("offline_profit_rate", 0) * 100, 1),
        "acs": round(sp.get("acs", 0) * 100, 1),
        "high_sell": round(sp.get("high_sell", 0) * 100, 1),
        "pp_amount_pct": round(sp.get("pp_amount_pct", 0) * 100, 1),
        "host_qty": sp.get("host_qty"), "pp_qty": sp.get("pp_qty"),
        })
# 花名册在册但暂无销售数据（新入职/未录单）→ 追加在最后
roster_names = list(roster.keys())
existing_names = {s["name"] for s in sp_out}
for name in roster_names:
    if name in existing_names:
        continue
    rank += 1
    rp = roster.get(name, {})
    sp_out.append({
        "rank": rank,
        "name": name, "store": rp.get("store", ""), "pos": rp.get("pos", ""),
        "task": None, "sales": 0, "rate": 0, "offline": 0, "online": 0,
        "pp_sales": 0, "pp_rate": 0, "profit": 0, "profit_rank": None,
        "profit_rate": 0, "offline_profit_rate": 0, "acs": 0, "high_sell": 0,
        "pp_amount_pct": 0, "host_qty": 0, "pp_qty": 0, "no_sales": True,
    })

# 客流序列（8月各日，从 apr daily）
traffic_series = []
for d in sorted(apr.get("daily", {}).keys()):
    pass
# daily 是单日数据，key 是门店；不做日序列，用月度客流

# ---------- 库存 ----------
inv_cats = sorted(inv["by_category"].items(), key=lambda x: -x[1])[:10]
inv_cat_out = [{"name": k, "qty": v} for k, v in inv_cats]
inv_wh = sorted(inv["by_warehouse"].items(), key=lambda x: -x[1])[:8]
inv_wh_out = [{"name": k, "qty": v} for k, v in inv_wh]
other_qty = inv["by_category"].get("其他", 0)
other_pct = round(other_qty / inv["total_qty"] * 100, 2)

# ---------- 电商（模拟补充部分） ----------
ecomm = jky["ecomm"]
apple_ec = ecomm.get("Apple电商", {})
shure_ec = ecomm.get("舒尔电商", {})

# 合并：库存（商务分析表）+ APR产品结构（销售分析表）+ 花名册 + 竞品 + 电商分平台
with open(os.path.join(V2, "inv_data.json")) as f:
    inv_biz = json.load(f)
with open(os.path.join(V2, "apr_struct.json")) as f:
    apr_struct = json.load(f)
with open(os.path.join(V2, "roster.json")) as f:
    roster = json.load(f)
with open(os.path.join(V2, "compete.json")) as f:
    compete = json.load(f)
compete_compare = {}
if os.path.exists(os.path.join(V2, "compete_compare.json")):
    with open(os.path.join(V2, "compete_compare.json")) as f:
        compete_compare = json.load(f)

data = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "today": today,
    "today_fetch_note": "今日为吉客云实时部分数据（截至抓取时间）",
    "today_total": {"amount_wan": today_wan, "orders": today_orders},
    "yesterday": {"date": yest, "amount_wan": fmt_wan(yest_total.get("amount", 0))},
    "lastweek": {"date": lastwk, "amount_wan": fmt_wan(lastwk_total.get("amount", 0))},
    "chg_vs_yest": chg(today_total["amount"], yest_total.get("amount", 0)),
    "chg_vs_lastwk": chg(today_total["amount"], lastwk_total.get("amount", 0)),
    "series": series,
    "channels": channels_today,
    "stores_today": stores_today,
    "apr": {
        "sales": round(apr_sales, 1), "task": apr_task, "rate": round(apr_rate * 100, 1),
        "profit": round(apr_profit, 2), "pm": round(apr_pm * 100, 2),
        "orders": apr_orders, "traffic": apr_traffic,
        "conv": round(apr_conv * 100, 1),
        "time_progress": round(time_progress * 100, 1),
        "gap": round((apr_rate - time_progress) * 100, 1),
        "forecast_month_end": round(forecast_month_end, 1),
        "forecast_rate": round(forecast_rate * 100, 1),
        "stores": stores_monthly,
        "salespersons": sp_out,
    },
    "inventory": {
        "fetched_at": inv["fetched_at"], "total_skus": inv["total_skus"],
        "total_qty": inv["total_qty"], "by_category": inv_cat_out,
        "by_warehouse": inv_wh_out, "other_qty": other_qty, "other_pct": other_pct,
    },
    "ecomm": {
        "apple": {"amount_wan": fmt_wan(apple_ec.get("amount", 0)), "orders": apple_ec.get("orders", 0)},
        "shure": {"amount_wan": fmt_wan(shure_ec.get("amount", 0)), "orders": shure_ec.get("orders", 0)},
    },
    "inventory_biz": inv_biz,
    "apr_struct": apr_struct,
    "roster": roster,
    "compete": compete,
    "compete_compare": compete_compare,
    "ecomm_platform": ecomm_platform,
    "pm_note": "APR毛利率 3.54% 为含线上/线下综合口径（吉客云）；不含线上口径约3.1%（待财务确认），客流为线下实抓口径",
    "task_note": "APR月目标¥2180万为公司下发口径，任务指标以每月正式下发为准",
}

with open(OUT, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print("data.json 生成完成:", OUT)
print("今日:", today, "金额(万):", today_wan, "环比昨日:", data["chg_vs_yest"], "%")
print("APR月销(万):", apr_sales, "毛利(万):", round(apr_profit,2), "毛利率%:", round(apr_pm*100,2))
print("达成率%:", round(apr_rate*100,1), "时间进度%:", round(time_progress*100,1))
print("预测月末(万):", round(forecast_month_end,1), "预测达成率%:", round(forecast_rate*100,1))
