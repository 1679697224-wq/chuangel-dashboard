# -*- coding: utf-8 -*-
"""测试 fullinfoget 是否返回 goodsDetail(分摊后金额/成本)"""
import json, sys
sys.path.insert(0, '/Users/lili/Desktop/deepseek harness/dsh_keys')
from jky_real import call
from datetime import datetime, timedelta

end = datetime.now()
start = end - timedelta(days=3)
biz = {
    "fields": "tradeId,tradeNo,tradeStatus,shopName,warehouseName,consignTime,payTime,seller,payment,goodsDetail,goodsNo,goodsName,sellCount,shareFavourableFee,shareFavourableAfterFee,sumPayment,goodsAmount,shareOrderAmount",
    "pageSize": 3,
    "startConsignTime": start.strftime("%Y-%m-%d %H:%M:%S"),
    "endConsignTime": end.strftime("%Y-%m-%d %H:%M:%S"),
}
r = call("oms.trade.fullinfoget", biz)
print(r[:2500])
