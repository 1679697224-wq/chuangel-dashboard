# -*- coding: utf-8 -*-
"""最终聚合：销售(导出表·分摊后金额/毛利/按付款时间) + 库存(导出表·剔虚拟/欧瑞特=舒尔天猫)"""
import json, re, datetime
from collections import defaultdict
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT = "/Users/lili/Desktop/deepseek harness/吉客云数据"
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

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

def norm_shop(s): return re.sub(r'^\[[0-9]{3}\]', '', str(s)).strip().rstrip('*').strip()
def norm_wh(s): return re.sub(r'^\[[0-9]{3}\]', '', str(s)).strip()

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
    elif '分销' in l1 or '（分销' in n or '(分销' in n: plate = '分销'
    elif '天羽乐购' in n: plate = '天羽乐购'
    else: plate = '其他'
    if l2: platform = l2
    elif '羽通' in n: platform = '京东羽通'
    elif '啟韬' in n and '舒尔' not in n: platform = '苏宁啟韬'
    elif '响誉' in n: platform = '响誉-天猫'
    elif '舒尔' in n: platform = '舒尔'
    else: platform = n
    store = l3 or (n if plate == 'APR' else '')
    return plate, platform, store

# ===== 销售 =====
lines = json.load(open(ROOT + '/sales_lines_export.json', encoding='utf-8'))
S = {'orders': set(), 'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'lines': 0,
     'by_plate': defaultdict(lambda: {'orders': set(), 'amount': 0.0, 'profit': 0.0, 'qty': 0.0}),
     'by_platform': defaultdict(lambda: {'orders': set(), 'amount': 0.0, 'profit': 0.0, 'qty': 0.0}),
     'by_apr': defaultdict(lambda: {'orders': set(), 'amount': 0.0, 'profit': 0.0, 'qty': 0.0}),
     'by_day': defaultdict(float)}
for l in lines:
    pay = (l['pay_time'] or l['order_time'] or '')[:10]
    if not pay.startswith('2026-08'):
        continue
    plate, platform, store = classify(l['channel'])
    S['orders'].add(l['order']); S['amount'] += l['amount']; S['profit'] += l['profit']
    S['qty'] += l['qty']; S['lines'] += 1
    S['by_day'][pay] += l['amount']
    b = S['by_plate'][plate]; b['orders'].add(l['order']); b['amount'] += l['amount']; b['profit'] += l['profit']; b['qty'] += l['qty']
    p = S['by_platform'][platform]; p['orders'].add(l['order']); p['amount'] += l['amount']; p['profit'] += l['profit']; p['qty'] += l['qty']
    if plate == 'APR' and store:
        a = S['by_apr'][store]; a['orders'].add(l['order']); a['amount'] += l['amount']; a['profit'] += l['profit']; a['qty'] += l['qty']

def row(d):
    o = len(d['orders']); return {'orders': o, 'amount': round(d['amount'], 2),
        'profit': round(d['profit'], 2),
        'margin': round(d['profit'] / d['amount'] * 100, 2) if d['amount'] else 0,
        'avg_ticket': round(d['amount'] / o, 2) if o else 0, 'qty': round(d['qty'], 2)}

sales_out = {
    'period': '2026-08-01~26',
    'total': row(S),
    'by_plate': {k: row(v) for k, v in sorted(S['by_plate'].items())},
    'by_platform': {k: row(v) for k, v in sorted(S['by_platform'].items())},
    'by_apr_store': {k: row(v) for k, v in sorted(S['by_apr'].items())},
    'by_day': {k: round(v, 2) for k, v in sorted(S['by_day'].items())},
}
json.dump(sales_out, open(ROOT + '/sales_agg.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ===== 库存 =====
wh_map = {}
for row in xlsx_sheets(ROOT + '/销售渠道匹配和发货仓库匹配.xlsx')['发货仓库匹配'][1:]:
    if row and row[0]:
        wh_map[norm_wh(row[0])] = {'pos': row[1] if len(row) > 1 else '', 'area': row[2] if len(row) > 2 else ''}

inv = json.load(open(ROOT + '/inventory_export.json', encoding='utf-8'))
I = {'amount': 0.0, 'qty': 0.0, 'rows': 0, 'by_pos': defaultdict(float), 'by_area': defaultdict(float),
     'by_plate_wh': defaultdict(lambda: [0.0, 0.0]), 'by_wh': defaultdict(lambda: [0.0, 0.0])}
for r_ in inv:
    amt = r_['amount']; qty = r_['qty']
    I['amount'] += amt; I['qty'] += qty; I['rows'] += 1
    w = norm_wh(r_['wh'])
    wm = wh_map.get(w, {})
    pos = wm.get('pos', '未匹配'); area = wm.get('area', '未匹配')
    I['by_pos'][pos] += amt
    I['by_area'][area] += amt
    I['by_wh'][w][0] += amt; I['by_wh'][w][1] += qty
    # 欧瑞特仓 = 舒尔天猫
    if '欧瑞特' in w:
        plate_wh = 'Shure电商(欧瑞特=舒尔天猫)'
    elif area == '门店仓':
        plate_wh = 'APR门店仓'
    else:
        plate_wh = pos + '/' + area
    I['by_plate_wh'][plate_wh][0] += amt; I['by_plate_wh'][plate_wh][1] += qty

inv_out = {
    'total_amount': round(I['amount'], 2), 'total_qty': round(I['qty'], 2), 'rows': I['rows'],
    'by_pos': {k: round(v, 2) for k, v in sorted(I['by_pos'].items())},
    'by_area': {k: round(v, 2) for k, v in sorted(I['by_area'].items())},
    'by_plate_wh': {k: {'amount': round(v[0], 2), 'qty': round(v[1], 2)} for k, v in sorted(I['by_plate_wh'].items())},
    'top_wh': {k: {'amount': round(v[0], 2), 'qty': round(v[1], 2)} for k, v in sorted(I['by_wh'].items(), key=lambda x: -x[1][0])[:12]},
}
json.dump(inv_out, open(ROOT + '/inventory_agg.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('=== 销售(8月, 分摊后金额, 按付款时间) ===')
t = sales_out['total']
print(f"单数 {t['orders']} | 销售额 {t['amount']} | 毛利 {t['profit']} | 毛利率 {t['margin']}% | 客单价 {t['avg_ticket']} | 件数 {t['qty']}")
print('板块:', json.dumps(sales_out['by_plate'], ensure_ascii=False))
print('平台:', json.dumps(sales_out['by_platform'], ensure_ascii=False))
print('APR门店:', json.dumps(sales_out['by_apr_store'], ensure_ascii=False))
print()
print('=== 库存(剔除虚拟, 金额=库存金额列) ===')
print(f"金额 {inv_out['total_amount']} | 数量 {inv_out['total_qty']}")
print('仓位:', json.dumps(inv_out['by_pos'], ensure_ascii=False))
print('区域:', json.dumps(inv_out['by_area'], ensure_ascii=False))
print('板块仓:', json.dumps(inv_out['by_plate_wh'], ensure_ascii=False))
