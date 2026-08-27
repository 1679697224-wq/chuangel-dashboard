# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding="utf-8").read()
n = src.count("<td>${p.acs}%</td>")
print('acs表单元格出现次数:', n)
src = src.replace("<td>${p.acs}%</td>", "<td>${p.acs!=null?p.acs+'%':'待接入'}</td>")
io.open(P, "w", encoding="utf-8").write(src)
print('done')