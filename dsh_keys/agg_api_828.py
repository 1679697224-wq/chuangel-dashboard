# -*- coding: utf-8 -*-
"""聚合 API 销售(实付8/1-27) + 库存现存量 + 客流4 + 舒尔日报"""
import json, re, sys
from collections import defaultdict
from datetime import datetime, timedelta
sys.path.insert(0, '/Users/lili/Desktop/deepseek harness/dsh_keys')
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT = "/Users/lili/Desktop/deepseek harness/吉客云数据"
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
EPOCH = datetime(1899, 12, 30)

def xlsx_sheets(path):
    z = ZipFile(path)
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    relmap = {rel.get('Id'): ('xl/' + rel.get('Target') if not rel.get('Target').startswith('/') else rel.get('Target')[1:]) for rel in rels}
    ss = []
    try:
        sst = ET.fromstring(z.read('xl/sharedStrings.xml'))
        ss = [''.join(t.text or '' for t in si.findall('.//m:t', NS)) for si in sst.findall('m:si', NS)]
    except KeyError:
        pass
    out = {}
    for sheet in wb.findall('m:sheets/m:sheet', NS):
        name = sheet.get('name')
        rid = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        target = relmap.get(rid, '')
        rows = []
        if target in z.namelist():
            root = ET.fromstring(z.read(target))
            for row in root.findall('.//m:row', NS):
                cells = []
                for c in row.findall('m:c', NS):
                    t = c.get('t'); v = c.find('m:v', NS); isel = c.find('m:is', NS)
                    if t == 's' and v is not None: val = ss[int(v.text)]
                    elif v is not None: val = v.text
                    elif isel is not None: val = ''.join(x.text or '' for x in isel.findall('.//m:t', NS))
                    else: val = ''
                    cells.append(str(val).strip())
                if any(cells): rows.append(cells)
        out[name] = rows
    return out

def norm_shop(s):
    s = str(s).strip()
    if s.startswith('[') and ']' in s:
        s = s.split(']', 1)[1]
    return s.strip().rstrip('*').strip()

shop_map = {}
for row in xlsx_sheets(ROOT + '/销售渠道匹配和发货仓库匹配.xlsx')['销售渠道匹配'][1:]:
    if row and row[0]:
        shop_map[norm_shop(row[0])] = {'l1': row[1] if len(row) > 1 else '', 'l2': row[2] if len(row) > 2 else '', 'l3': row[3] if len(row) > 3 else ''}

def classify(shop):
    n = norm_shop(shop)
    m = shop_map.get(n)
    if not m:
        for k, v in shop_map.items():
            if k and (k in n or n in k): m = v; break
    l1 = (m or {}).get('l1', '') or ''
    l2 = (m or {}).get('l2', '') or ''
    l3 = (m or {}).get('l3', '') or ''
    if 'APR' in l1 or 'APR' in n: plate = 'APR'
    elif l1.startswith('苹果') or '羽通' in n or '啟韬' in n or '响誉' in n: plate = 'Apple电商'
    elif l1.startswith('舒尔') or '舒尔' in n: plate = 'Shure电商'
    elif '3PP' in l1: plate = '3PP'
    elif '分销' in l1 or '分销' in n: plate = '分销'
    elif '天羽乐购' in n: plate = '天羽乐购'
    else: plate = '其他'
    if l2: platform = l2
    elif '羽通' in n: platform = '羽通-京东'
    elif '啟韬' in n and '舒尔' not in n: platform = '啟韬-苏宁'
    elif '响誉' in n: platform = '响誉-天猫'
    elif '舒尔' in n: platform = '舒尔-天猫'
    else: platform = n
    store = l3 or (n if plate == 'APR' else '')
    return plate, platform, store

def num(x):
    try: return float(x)
    except Exception: return 0.0

# ===== 销售（API 实付 8/1-27）=====
trades = json.load(open(ROOT + '/sales_raw_20260828.json', encoding='utf-8'))
plate = defaultdict(lambda: {'amount': 0.0, 'orders': 0})
platform = defaultdict(lambda: {'amount': 0.0, 'orders': 0})
aprst = defaultdict(lambda: {'amount': 0.0, 'orders': 0, 'on': 0.0, 'off': 0.0})
daily = defaultdict(float)
person = defaultdict(lambda: {'amount': 0.0, 'orders': 0, 'on': 0.0, 'off': 0.0, 'store': ''})
for o in trades:
    pt = o.get('payTime', '')
    if not (pt.startswith('2026-08') and pt[8:10] <= '27'): continue
    amt = num(o.get('payment', 0))
    p, pf, st = classify(o.get('shopName', ''))
    plate[p]['amount'] += amt; plate[p]['orders'] += 1
    platform[pf]['amount'] += amt; platform[pf]['orders'] += 1
    daily[pt[:10]] += amt
    if p == 'APR':
        aprst[st]['amount'] += amt; aprst[st]['orders'] += 1
        if pf == 'APR-线上': aprst[st]['on'] += amt
        else: aprst[st]['off'] += amt
    sp = re.sub(r'(.*)', '', o.get('seller', '') or '').strip()
    if sp:
        person[sp]['amount'] += amt; person[sp]['orders'] += 1
        person[sp]['store'] = st or p
        if p == 'APR':
            if pf == 'APR-线上': person[sp]['on'] += amt
            else: person[sp]['off'] += amt

S = {'plate': dict(plate), 'platform': dict(platform), 'apr_store': dict(aprst),
     'daily': dict(sorted(daily.items())), 'person': dict(sorted(person.items(), key=lambda x: -x[1]['amount']))}
print('== 板块(API实付 8/1-27) ==')
tot = 0
for k, v in sorted(S['plate'].items(), key=lambda x: -x[1]['amount']):
    print(' ', k, round(v['amount']/10000, 2), '万', v['orders'], '单')
    tot += v['amount']
print('  合计:', round(tot/10000, 2), '万')
print('== 平台 ==')
for k, v in sorted(S['platform'].items(), key=lambda x: -x[1]['amount']):
    print(' ', k, round(v['amount']/10000, 2), '万')
print('== 门店 ==')
for k, v in sorted(S['apr_store'].items(), key=lambda x: -x[1]['amount']):
    print(' ', k, round(v['amount']/10000, 2), '万', v['orders'], '单')
print('== 销售员TOP8 ==')
for k, v in list(S['person'].items())[:8]:
    print(' ', k, round(v['amount']/10000, 2), '万')
print('== 8/27 日销 ==', round(S['daily'].get('2026-08-27', 0)/10000, 2), '万')

# ===== 库存（API 现存量）=====
inv = json.load(open(ROOT + '/inventory_raw_0828.json', encoding='utf-8'))
print()
print('库存字段样例:', {k: inv[0][k] for k in list(inv[0].keys())[:8]})
wh = defaultdict(lambda: {'qty': 0.0, 'amount': 0.0})
cost_key = 'costPrice' if 'costPrice' in inv[0] else ('costprice' if 'costprice' in inv[0] else None)
print('成本字段:', cost_key)
for r in inv:
    q = num(r.get('currentQuantity', 0))
    c = num(r.get(cost_key, 0)) if cost_key else 0
    wh[r.get('warehouseName', '')]['qty'] += q
    wh[r.get('warehouseName', '')]['amount'] += q * c
tot_inv = sum(v['amount'] for v in wh.values())
print('库存合计金额: %.2f 万' % (tot_inv/10000))
for k, v in sorted(wh.items(), key=lambda x: -x[1]['amount'])[:15]:
    print(' ', k[:30], '数量', round(v['qty']), '金额 %.2f 万' % (v['amount']/10000))
json.dump({'sales': S, 'inventory_wh': dict(wh), 'inventory_total': tot_inv,
           'inventory_raw_count': len(inv)},
          open(ROOT + '/api_agg_828.json', 'w'), ensure_ascii=False, indent=1)
print('saved api_agg_828.json')
