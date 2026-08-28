# -*- coding: utf-8 -*-
"""更新看板数据对象：API 实付 8/1-27 口径"""
import json, io, re, sys
from collections import defaultdict
sys.path.insert(0, '/Users/lili/Desktop/deepseek harness/dsh_keys')

ROOT = "/Users/lili/Desktop/deepseek harness/吉客云数据"
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
F = json.load(open(ROOT + '/api_fill_828.json', encoding='utf-8'))
B = json.load(open(ROOT + '/board_prep_828.json', encoding='utf-8'))
S = F['sales']

def wan(v): return round(v / 10000, 2)

# 2025 每日
t25 = json.load(open(ROOT + '/sales_raw_202508.json', encoding='utf-8'))
d25 = defaultdict(float)
for o in t25:
    tno = str(o.get('tradeNo', ''))
    d = tno[2:10] if len(tno) >= 10 else ''
    if re.match(r'^\d{8}$', d) and d.startswith('202508'):
        d25[d[6:8]] += float(o.get('payment') or 0)
TR = ['21', '22', '23', '24', '25', '26', '27']
trend_sales = [wan(S['daily'].get('2026-08-' + d, 0)) for d in TR]
trend_last = [round(d25[d] / 10000, 2) for d in TR]

gross = 66.21 + 54.09 + 21.87 - 1.61 + 3.31
company_sales = wan(sum(v['amount'] for v in S['plate'].values()))
gpm = round(gross / company_sales * 100, 2)
ds = int(company_sales * 10000 / 29.2); dg = int(gross * 10000 / 29.2)
aov = int(company_sales * 10000 / 6755)
on = round((company_sales - 1350.79) / company_sales * 100, 1); off = round(100 - on, 1)
month_sales = int(company_sales * 10000)

REPS = []
def R(old, new, expect=1, name=''):
    REPS.append((old, new, expect, name))

# ---------- COMPANY ----------
old_c = """const COMPANY = {
  day:{ sales:1092138, target:2347055, gross:47603, gpm:4.36, feeRate:null, cvr:null, aov:4395, d7:null, w0:null, yoy:45.8, onlineShare:56.3, offlineShare:43.7 },
  week:{ sales:7535752, target:16195890, gross:328461, gpm:4.36, feeRate:null, cvr:null, aov:4395, d7:null, w0:null, yoy:45.8, onlineShare:56.3, offlineShare:43.7 },
  month:{ sales:31890428, target:68534000, gross:1390009, gpm:4.36, feeRate:null, cvr:null, aov:4395, d7:null, w0:null, yoy:45.8, onlineShare:56.3, offlineShare:43.7 }
};"""
new_c = """const COMPANY = {
  day:{ sales:%d, target:2347055, gross:%d, gpm:%.2f, feeRate:null, cvr:null, aov:%d, d7:null, w0:null, yoy:47.6, onlineShare:%.1f, offlineShare:%.1f },
  week:{ sales:%d, target:16195890, gross:%d, gpm:%.2f, feeRate:null, cvr:null, aov:%d, d7:null, w0:null, yoy:47.6, onlineShare:%.1f, offlineShare:%.1f },
  month:{ sales:%d, target:68534000, gross:%d, gpm:%.2f, feeRate:null, cvr:null, aov:%d, d7:null, w0:null, yoy:47.6, onlineShare:%.1f, offlineShare:%.1f }
};""" % (ds, dg, gpm, aov, on, off, int(ds * 6.9), int(dg * 6.9), gpm, aov, on, off, month_sales, int(gross * 10000), gpm, aov, on, off)
R(old_c, new_c, 1, 'COMPANY')

# ---------- SEGMENTS ----------
apr_d = wan4v = lambda v: round(v / 29.2 / 10000, 0)
aprd = round(S['plate']['APR']['amount'] / 29.2)
aed = round(S['plate']['Apple电商']['amount'] / 29.2)
shd = round(S['plate']['Shure电商']['amount'] / 29.2)
othd = round((S['plate'].get('分销', {}).get('amount', 0) + S['plate'].get('天羽乐购', {}).get('amount', 0) + S['plate'].get('3PP', {}).get('amount', 0)) / 29.2)
gross_d = round(gross * 10000 / 29.2)
old_seg = """const SEGMENTS = [
  { name:'APR（整体）', code:'APR', sales:688842, gross:21345, gpm:3.10, cvr:6.33, feeRate:null, inv:1442.6, d7:null, yoy:72.8, onlineShare:30.7, offlineShare:69.3, note:'10 家门店 · 含线上线下整体' },
  { name:'Apple 电商', code:'AE', sales:367479, gross:18294, gpm:4.98, cvr:null, feeRate:null, inv:367.5, d7:null, yoy:89.2, onlineShare:100, offlineShare:0, note:'啟韬(苏宁)+羽通(京东)·其余 3.7 万未细分',
    stores:[
      { name:'苏宁旗舰店（啟韬）', sales:220880, gross:5478, gpm:2.48, cvr:null, feeRate:null, inv:103.5, d7:null, yoy:null, src:'吉客云自动' },
      { name:'京东旗舰店（羽通）', sales:145332, gross:14418, gpm:9.92, cvr:null, feeRate:null, inv:264.0, d7:null, yoy:null, src:'吉客云自动' }
    ] },
  { name:'Shure 电商', code:'SH', sales:24708, gross:7489, gpm:30.31, cvr:null, feeRate:null, inv:229.5, d7:null, yoy:15.5, onlineShare:100, offlineShare:0, note:'天猫72.15(吉客云)+京东74.73(日报)另计',
    stores:[
      { name:'天猫旗舰店', sales:24709, gross:7489, gpm:30.31, cvr:0.88, feeRate:null, inv:137.3, d7:null, yoy:15.5, src:'吉客云自动' },
      { name:'京东旗舰店（另计）', sales:24726, gross:0, gpm:null, cvr:3.12, feeRate:null, inv:92.2, d7:null, yoy:null, src:'平台日报·手工' }
    ] },
  { name:'分销/其他', code:'OTH', sales:11108, gross:475, gpm:4.27, cvr:null, feeRate:null, inv:0, d7:null, yoy:-88.9, onlineShare:0, offlineShare:100, note:'分销 + 天羽乐购' }
];"""
new_seg = """const SEGMENTS = [
  { name:'APR（整体）', code:'APR', sales:%d, gross:%d, gpm:3.57, cvr:5.70, feeRate:null, inv:987, d7:null, yoy:%.1f, onlineShare:%.1f, offlineShare:%.1f, note:'10 家门店 · 含线上线下整体' },
  { name:'Apple 电商', code:'AE', sales:%d, gross:0, gpm:5.07, cvr:null, feeRate:null, inv:318, d7:null, yoy:89.2, onlineShare:100, offlineShare:0, note:'啟韬(苏宁)+羽通(京东) 实付口径' },
  { name:'Shure 电商', code:'SH', sales:%d, gross:0, gpm:30.31, cvr:null, feeRate:null, inv:135, d7:null, yoy:15.5, onlineShare:100, offlineShare:0, note:'天猫(API实付)+京东(日报)另计' },
  { name:'分销/其他', code:'OTH', sales:%d, gross:0, gpm:0, cvr:null, feeRate:null, inv:0, d7:null, yoy:null, onlineShare:0, offlineShare:100, note:'分销+天羽乐购+3PP' }
];""" % (aprd, gross_d, B['store_yoy'].get('徐州彭城店', 0) or 0, on, off, aed, shd, othd)
R(old_seg, new_seg, 1, 'SEGMENTS')

print('SEGMENTS new:', aprd, gross_d, aed, shd, othd)
print('COMPANY: ds=%d dg=%d gpm=%.2f aov=%d on=%.1f' % (ds, dg, gpm, aov, on))
print('trend:', trend_sales, trend_last)

ok = True
for old, new, expect, name in REPS:
    n = src.count(old)
    if n != expect:
        print('MISS/COUNT[%s]: expected %d, got %d' % (name, expect, n))
        ok = False
    else:
        src = src.replace(old, new)
        print('ok  [%s]' % name)
io.open(P, 'w', encoding='utf-8').write(src)
print('PART1 done, ok =', ok)
