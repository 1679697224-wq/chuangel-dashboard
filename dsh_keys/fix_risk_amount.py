# -*- coding: utf-8 -*-
import io, re
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding="utf-8").read()
def fix(m):
    return 'age:%d, amount:%.2f, brand:' % (int(m.group(1)), float(m.group(2)) / 10000.0)
new, n = re.subn(r'age:(\d+), amount:([\d.]+), brand:', fix, src)
print('替换处数:', n)
io.open(P, "w", encoding="utf-8").write(new)