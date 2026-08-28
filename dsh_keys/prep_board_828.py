# -*- coding: utf-8 -*-
"""预计算看板所有数值（API口径 8/1-27）"""
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

F = json.load(open(ROOT + '/api_fill_828.json', encoding='utf-8'))
B = {}

# ===== 门店同比（API 2025 vs 2026 8/1-27）=====
a26 = defaultdict(float); a25 = defaultdict(float)
for o in json.load(open(ROOT + '/sales_raw_20260828.json', encoding='utf-8')):
    pt = o.get('payTime') or o.get('consignTime') or ''
    d = pt[:10]
    if d.startswith('2026-08') and d[8:10] <= '27':
        p, pf, st = classify(o.get('shopName', ''))
        if p == 'APR': a26[st] += num(o.get('payment', 0))
for o in json.load(open(ROOT + '/sales_raw_202508.json', encoding='utf-8')):
    tno = str(o.get('tradeNo', ''))
    d = tno[2:10] if len(tno) >= 10 else ''
    if re.match(r'^\d{8}$', d) and d.startswith('202508') and d[6:8] <= '27':
        p, pf, st = classify(o.get('shopName', ''))
        if p == 'APR': a25[st] += num(o.get('payment', 0))
B['store_yoy'] = {}
for st, v in F['sales']['apr_store'].items():
    l = a25.get(st, 0)
    B['store_yoy'][st] = round((v['amount'] - l) / l * 100, 1) if l else None
print('== 门店同比 ==', B['store_yoy'])

# ===== 库存：API 现存量分类与仓位 =====
inv = json.load(open(ROOT + '/inventory_raw_0828.json', encoding='utf-8'))
cat = defaultdict(lambda: {'amount': 0.0, 'qty': 0.0})
wh = defaultdict(lambda: {'amount': 0.0, 'qty': 0.0})
for r in inv:
    q = num(r.get('currentQuantity', 0)); c = num(r.get('costPrice', 0))
    amt = q * c
    gno = str(r.get('goodsNo', ''))
    if 'SHURE' in gno.upper() or '舒尔' in str(r.get('goodsName', '')):
        cat['舒尔']['amount'] += amt; cat['舒尔']['qty'] += q
    elif re.match(r'^(iPhone|Mac|iPad|Watch|A[0-9]|MW|MU|MY|MT|ML|MQ|M[QRSTUVWXY]|IP)', gno) or 'iPhone' in gno or 'MacBook' in gno or 'iPad' in gno or 'Watch' in gno:
        cat['苹果主机/配件']['amount'] += amt; cat['苹果主机/配件']['qty'] += q
    else:
        cat['其他/3PP']['amount'] += amt; cat['其他/3PP']['qty'] += q
    wn = str(r.get('warehouseName', ''))
    wh[wn]['amount'] += amt; wh[wn]['qty'] += q
B['inv_cat'] = {k: round(v['amount']/10000, 2) for k, v in cat.items()}
B['inv_total'] = sum(v['amount'] for v in wh.values())
B['inv_wh'] = {k: round(v['amount']/10000, 2) for k, v in sorted(wh.items(), key=lambda x: -x[1]['amount'])}
print('== 库存合计 ==', round(B['inv_total']/10000, 2), '万')
print('== 分类 ==', B['inv_cat'])
print('== 仓位TOP12 ==')
for k, v in list(B['inv_wh'].items())[:12]:
    print('  ', k[:34], v, '万')

# ===== 舒尔 =====
B['jd'] = F['jd_shure']
B['tm'] = F['tm_shure']
B['tm_conv'] = round(F['tm_shure']['orders'] / F['tm_shure']['uv'] * 100, 2) if F['tm_shure']['uv'] else 0
print('== 京东舒尔 ==', B['jd'])
print('== 天猫日报 ==', B['tm'], '转化', B['tm_conv'])

# ===== 日销（8/20-27）=====
B['trend'] = {d: round(F['sales']['daily'].get(d, 0)/10000, 2) for d in
              ['2026-08-20','2026-08-21','2026-08-22','2026-08-23','2026-08-24','2026-08-25','2026-08-26','2026-08-27']}
print('== 日销 ==', B['trend'])

json.dump(B, open(ROOT + '/board_prep_828.json', 'w'), ensure_ascii=False, indent=1)
print('saved board_prep_828.json')
