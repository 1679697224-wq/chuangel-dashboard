# -*- coding: utf-8 -*-
import json
from jky_real import call, signed_body, APPKEY
from datetime import datetime, timedelta

biz = {
    "fields": "tradeId,tradeNo,tradeStatus,shopName,warehouseName,consignTime,payTime,seller,goodsDetail,subTradeId,goodsNo,goodsName,sellCount,shareFavourableFee,shareFavourableAfterFee,payment",
    "pageSize": 3,
    "startConsignTime": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
    "endConsignTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}
r = call("oms.trade.fullinfoget", biz)
try:
    d = json.loads(r)
    trades = d["result"]["data"]["trades"]
    print("返回单数:", len(trades))
    if trades:
        t = trades[0]
        print("== 订单级字段 ==")
        for k, v in t.items():
            if not isinstance(v, (dict, list)):
                print(f"  {k} = {v}")
        print("== goodsDetail[0] ==")
        if t.get("goodsDetail"):
            for k, v in t["goodsDetail"][0].items():
                if not isinstance(v, (dict, list)):
                    print(f"  {k} = {v}")
except Exception as e:
    print("解析失败:", e)
    print(r[:300])
