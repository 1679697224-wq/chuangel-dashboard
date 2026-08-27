# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding="utf-8").read()

def rep(src, old, new, name):
    n = src.count(old)
    if n == 0:
        print("MISS", name)
        return src
    print("ok", name, "x", n)
    return src.replace(old, new)

src = rep(src, "'线下 22.4% / 线上 2.8%'", "'线下/线上转化率待接入'", "转化率副标x2")
src = rep(src, "<b>¥5,860万</b>", "<b>¥'+INV_BIZ.total_amount.toFixed(0)+'万</b>", "合计库存x3")

io.open(P, "w", encoding="utf-8").write(src)
print("done")