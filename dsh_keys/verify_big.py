# -*- coding: utf-8 -*-
import re, io, subprocess, os
P = '/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html'
src = io.open(P, encoding='utf-8').read()
m = re.search(r'<script>(.*)</script>', src, re.S)
io.open('/tmp/dash_check.js','w',encoding='utf-8').write(m.group(1))
print('script len:', len(m.group(1)))
print('综合转化率卡剩余:', src.count("kpiCard('综合转化率'"))
print('演示数据:', src.count('演示数据'))
print('待接入null返回:', src.count("return '待接入'"), '| 未接入null返回:', src.count("return '未接入'"))
print('3PP部门:', src.count("id:'pp3'"))