# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
old = "<b>¥'+INV_BIZ.total_amount.toFixed(0)+'万</b>"
new = "<b>¥${INV_BIZ.total_amount.toFixed(0)}万</b>"
n = src.count(old)
print('破损处数:', n)
src = src.replace(old, new)
io.open(P, 'w', encoding='utf-8').write(src)
print('已修复')