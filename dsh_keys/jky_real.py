# -*- coding: utf-8 -*-
"""吉客云客户端（签名与接口名来自 传天羽AI工作台 已验证实现）"""
import hashlib, json, time, urllib.request, urllib.parse
from datetime import datetime, timedelta

APPKEY = "90871460"
APPSECRET = "4e0ca84911ab48aeb2cccad89587222f"
GATEWAY = "https://open.jackyun.com/open/openapi/do"
VERSION = "v1.0"

def signed_body(method, bizcontent):
    body = {
        "method": method,
        "appkey": APPKEY,
        "version": VERSION,
        "contenttype": "json",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "bizcontent": json.dumps(bizcontent, ensure_ascii=False, separators=(",", ":")),
    }
    secret = APPSECRET
    source = secret + "".join(f"{k}{body[k]}" for k in sorted(body)) + secret
    body["sign"] = hashlib.md5(source.lower().encode()).hexdigest()
    return body

def call(method, bizcontent):
    body = signed_body(method, bizcontent)
    body["contextid"] = str(int(time.time() * 1000))
    data = urllib.parse.urlencode(body).encode("utf-8")
    req = urllib.request.Request(GATEWAY, data=data, headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8", "replace")
    except Exception as e:
        return "EXC:" + str(e)[:200]

if __name__ == "__main__":
    # 1) 销售：近2天发货
    end = datetime.now()
    start = end - timedelta(days=2)
    sales_biz = {
        "fields": "tradeId,tradeNo,tradeStatus,shopName,warehouseName,consignTime,seller,goodsDetail,subTradeId,goodsNo,goodsName,sellCount,shareFavourableFee,shareFavourableAfterFee",
        "pageSize": 5,
        "startConsignTime": start.strftime("%Y-%m-%d %H:%M:%S"),
        "endConsignTime": end.strftime("%Y-%m-%d %H:%M:%S"),
    }
    print('== 销售 oms.trade.fullinfoget ==')
    r = call("oms.trade.fullinfoget", sales_biz)
    print(r[:500])
    print()
    # 2) 库存
    print('== 库存 erp.stockquantity.get ==')
    r2 = call("erp.stockquantity.get", {"pageIndex": 0, "pageSize": 3})
    print(r2[:500])
