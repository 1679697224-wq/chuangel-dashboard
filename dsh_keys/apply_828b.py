# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, name=''):
    REPS.append((old, new, name))

cur = {
'徐州彭城店': "{ name:'徐州彭城店', sales:436.12, task:340, pm:3.46, profit:15.08, flow:20804, conv:4.58, apt:4576, inv:140.6, d7:null, yoy:112.7, rate:128.3, off:315.58, on:120.54 },",
'无锡店': "{ name:'无锡店', sales:333.39, task:380, pm:3.03, profit:10.09, flow:12303, conv:6.22, apt:4358, inv:121.8, d7:null, yoy:67.8, rate:87.7, off:234.83, on:98.56 },",
'连云港店': "{ name:'连云港店', sales:310.07, task:340, pm:3.27, profit:10.14, flow:8913, conv:8.12, apt:4283, inv:155.3, d7:null, yoy:113.7, rate:91.2, off:203.89, on:106.18 },",
'太原店': "{ name:'太原店', sales:174.34, task:210, pm:2.24, profit:3.90, flow:3584, conv:11.44, apt:4252, inv:83.5, d7:null, yoy:79.1, rate:83.0, off:96.14, on:78.21 },",
'宿州店': "{ name:'宿州店', sales:175.69, task:180, pm:3.29, profit:5.78, flow:6455, conv:6.60, apt:4124, inv:97.3, d7:null, yoy:32.1, rate:97.6, off:130.17, on:45.52 },",
'镇江店': "{ name:'镇江店', sales:150.74, task:240, pm:4.42, profit:6.66, flow:8248, conv:4.84, apt:3778, inv:78.7, d7:null, yoy:23.6, rate:62.8, off:109.37, on:41.37 },",
'运城店': "{ name:'运城店', sales:155.45, task:170, pm:3.14, profit:4.89, flow:6528, conv:6.10, apt:3906, inv:95.9, d7:null, yoy:157.9, rate:91.4, off:108.30, on:47.16 },",
'日照店': "{ name:'日照店', sales:118.02, task:80, pm:1.37, profit:1.62, flow:2545, conv:10.37, apt:4471, inv:79.1, d7:null, yoy:86.2, rate:147.5, off:84.67, on:33.35 },",
'徐州宝龙店': "{ name:'徐州宝龙店', sales:73.43, task:100, pm:2.82, profit:2.07, flow:2024, conv:9.68, apt:3746, inv:77.2, d7:null, yoy:17.4, rate:73.4, off:48.37, on:25.06 },",
'苏家屯店': "{ name:'苏家屯店', sales:84.17, task:140, pm:2.49, profit:2.10, flow:3510, conv:5.95, apt:4027, inv:92.7, d7:null, yoy:-5.1, rate:60.1, off:62.16, on:22.00 }"
}
newv = {
'徐州彭城店': "394.49,340,3.54,13.96,21321,4.11,4576,120.2,116.0",
'无锡店': "300.99,380,3.28,9.87,12685,5.53,4358,74.8,79.2",
'连云港店': "299.59,340,3.29,9.86,9285,7.52,4283,132.6,88.1",
'太原店': "156.93,210,2.32,3.64,3709,9.87,4252,86.1,74.7",
'宿州店': "156.40,180,3.21,5.02,6701,5.73,4124,46.0,86.9",
'镇江店': "133.85,240,4.50,6.02,8617,4.34,3778,29.3,55.8",
'运城店': "157.95,170,2.95,4.66,6666,5.70,3906,185.8,92.9",
'日照店': "115.24,80,1.34,1.54,2610,9.73,4471,103.3,144.1",
'徐州宝龙店': "68.72,100,2.91,2.00,2118,8.55,3746,25.3,68.7",
'苏家屯店': "70.14,140,2.44,1.71,3652,5.23,4027,7.4,50.1"
}
onoff = {
'徐州彭城店': (87.87, 306.62), '无锡店': (82.86, 218.13), '连云港店': (86.31, 213.28),
'太原店': (44.43, 112.50), '宿州店': (41.34, 115.06), '镇江店': (36.99, 96.86),
'运城店': (40.52, 117.43), '日照店': (29.37, 85.87), '徐州宝龙店': (15.95, 52.77),
'苏家屯店': (16.50, 53.64)
}
for st, o in cur.items():
    v = newv[st].split(',')
    sales, task, pm, profit, fl, conv, apt, yoy, rate = v
    onW, offW = onoff[st]
    R(o, "{ name:'%s', sales:%s, task:%s, pm:%s, profit:%s, flow:%s, conv:%s, apt:%s, inv:0, d7:null, yoy:%s, rate:%s, off:%.2f, on:%.2f }," % (st, sales, task, pm, profit, fl, conv, apt, yoy, rate, offW, onW), 'store:'+st)

R("""const BUSINESS_ROWS = [
  { name:'APR（整体）', code:'APR', sales:688842, gross:21345, gpm:3.10, cvr:6.33, feeRate:null, inv:1442.6, d7:null, yoy:72.8, note:'10 家门店 · 含线上线下' },
  { name:'京东羽通（Apple 电商）', code:'AE', sales:145332, gross:14418, gpm:9.92, cvr:null, feeRate:null, inv:264.0, d7:null, yoy:89.2, note:'苹果电商 · 京东' },
  { name:'苏宁啟韬（Apple 电商）', code:'AE', sales:220880, gross:5478, gpm:2.48, cvr:null, feeRate:null, inv:103.5, d7:null, yoy:89.2, note:'苹果电商 · 苏宁' },
  { name:'天猫舒尔', code:'SH', sales:24709, gross:7489, gpm:30.31, cvr:0.88, feeRate:null, inv:137.3, d7:null, yoy:15.5, note:'吉客云自动' },
  { name:'京东舒尔（平台日报）', code:'SH', sales:25592, gross:0, gpm:null, cvr:3.12, feeRate:null, inv:92.2, d7:null, yoy:null, note:'平台日报 · 手工' }
];""",
"""const BUSINESS_ROWS = [
  { name:'APR（整体）', code:'APR', sales:635037, gross:0, gpm:3.57, cvr:5.70, feeRate:null, inv:987, d7:null, yoy:120.2, note:'10 家门店 · 含线上线下' },
  { name:'京东羽通（Apple 电商）', code:'AE', sales:12541, gross:0, gpm:5.07, cvr:null, feeRate:null, inv:232, d7:null, yoy:89.2, note:'苹果电商 · 京东' },
  { name:'苏宁啟韬（Apple 电商）', code:'AE', sales:22039, gross:0, gpm:2.48, cvr:null, feeRate:null, inv:86, d7:null, yoy:89.2, note:'苹果电商 · 苏宁' },
  { name:'天猫舒尔', code:'SH', sales:20754, gross:0, gpm:30.31, cvr:0.90, feeRate:null, inv:135, d7:null, yoy:15.5, note:'吉客云 API 实付' },
  { name:'京东舒尔（平台日报）', code:'SH', sales:26417, gross:0, gpm:null, cvr:3.11, feeRate:null, inv:92, d7:null, yoy:null, note:'平台日报 · 手工' }
];""", 'BUSINESS_ROWS')

ok = True
for old, new, name in REPS:
    n = src.count(old)
    if n != 1:
        print('MISS[%s]: %d' % (name, n))
        ok = False
    else:
        src = src.replace(old, new)
        print('ok[%s]' % name)
io.open(P, 'w', encoding='utf-8').write(src)
print('DONE ok =', ok)
