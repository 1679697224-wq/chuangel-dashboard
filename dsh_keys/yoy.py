# -*- coding: utf-8 -*-
import json, re
from collections import defaultdict

def load(p):
    return json.load(open(p, encoding='utf-8'))

def norm_shop(s):
    return re.sub(r'^\[[0-9]{3}\]', '', str(s)).strip().rstrip('*').strip()

def classify(shop):
    n = norm_shop(shop)
    if 'APR' in n: return 'APR'
    if '羽通' in n or '啟韬' in n or '响誉' in n: return 'Apple电商'
    if '舒尔' in n: return 'Shure电商'
    if '信创' in n or '分销' in n: return '3PP/分销'
    return '其他'

for year, path in [(2025, '/Users/lili/Desktop/deepseek harness/吉客云数据/sales_raw_202508.json'),
                   (2026, '/Users/lili/Desktop/deepseek harness/吉客云数据/sales_raw_202608.json')]:
    t = load(path)
    tot = 0.0
    byc = defaultdict(float)
    for x in t:
        p = float(x.get('payment') or 0)
        tot += p
        byc[classify(x.get('shopName') or '')] += p
    print(f'{year}-08: 单数 {len(t)} | 实付 {round(tot,2)} | 板块 {dict((k, round(v,2)) for k,v in byc.items())}')

y25 = sum(float(x.get('payment') or 0) for x in load('/Users/lili/Desktop/deepseek harness/吉客云数据/sales_raw_202508.json'))
y26 = sum(float(x.get('payment') or 0) for x in load('/Users/lili/Desktop/deepseek harness/吉客云数据/sales_raw_202608.json'))
print()
print('同比(实付口径):', round((y26 - y25) / y25 * 100, 1), '%')
