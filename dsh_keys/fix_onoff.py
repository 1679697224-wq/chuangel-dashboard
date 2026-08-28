# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
pairs = [
 ("徐州彭城店", 87.87, 306.62, 103.12, 291.37),
 ("无锡店", 82.86, 218.13, 74.47, 226.52),
 ("连云港店", 86.31, 213.28, 93.28, 206.31),
 ("太原店", 44.43, 112.50, 64.21, 92.71),
 ("宿州店", 41.34, 115.06, 31.91, 124.50),
 ("镇江店", 36.99, 96.86, 28.97, 104.88),
 ("运城店", 40.52, 117.43, 42.18, 115.77),
 ("日照店", 29.37, 85.87, 29.74, 85.50),
 ("徐州宝龙店", 15.95, 52.77, 23.46, 45.26),
 ("苏家屯店", 16.50, 53.64, 12.17, 57.97),
]
ok = True
for st, o1, f1, n1, n2 in pairs:
    old = "off:%.2f, on:%.2f }," % (f1, o1)
    new = "off:%.2f, on:%.2f }," % (n2, n1)
    if old not in src:
        print("MISS", st, old)
        ok = False
    else:
        src = src.replace(old, new)
        print("ok", st)
io.open(P, 'w', encoding='utf-8').write(src)
print("DONE", ok)
