# -*- coding: utf-8 -*-
"""聚合 v2：销售→板块/平台/APR门店（按支付时间），库存→金额口径"""
import json, re
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

def norm_shop(s):
    return re.sub(r'^\[[0-9]{3}\]', '', str(s)).strip().rstrip('*').strip()
def norm_wh(s):
    return re.sub(r'^\[[0-9]{3}\]', '', str(s)).strip()

# 渠道映射（接受 2+ 列）
shop_map = {}
for row in xlsx_sheets(ROOT + '/销售渠道匹配和发货仓库匹配.xlsx')['销售渠道匹配'][1:]:
    if row and row[0]:
        k = norm_shop(row[0])
        l1 = row[1] if len(row) > 1 else ''
        l2 = row[2] if len(row) > 2 else ''
        l3 = row[3] if len(row) > 3 else ''
        shop_map[k] = {'l1': l1, 'l2': l2, 'l3': l3}

def classify(shop):
    n = norm_shop(shop)
    m = shop_map.get(n)
    if not m:
        for k, v in shop_map.items():
            if k and (k in n or n in k):
                m = v; break
    l1 = (m or {}).get('l1', '') or ''
    l2 = (m or {}).get('l2', '') or ''
    l3 = (m or {}).get('l3', '') or ''
    # 板块
    if 'APR' in l1 or 'APR' in n:
        plate = 'APR'
    elif l1.startswith('苹果'):
        plate = 'Apple电商'
    elif l1.startswith('舒尔') or '舒尔' in l2:
        plate = 'Shure电商'
    elif '3PP' in l1:
        plate = '3PP'
    elif '分销' in l1 or '分销' in l2 or '（分销' in n or '(分销' in n:
        plate = '分销'
    elif '天羽乐购' in n:
        plate = '天羽乐购'
    else:
        plate = '其他'
    # 平台
    if l2:
        platform = l2
    elif '羽通' in n: platform = '京东羽通'
    elif '啟韬' in n and '舒尔' not in n: platform = '苏宁啟韬'
    elif '响誉' in n: platform = '响誉-天猫'
    elif '舒尔' in n: platform = '舒尔'
    elif '天猫' in n: platform = '天猫'
    elif '京东' in n: platform = '京东'
    else: platform = n
    store = l3 or (n if plate == 'APR' else '')
    return plate, platform, store

# ============ 销售 ============
trades = json.load(open(ROOT + '/sales_raw_202608.json', encoding='utf-8'))
S = {'total_orders': 0, 'total_amount': 0.0, 'by_day': defaultdict(lambda: [0, 0.0]),
     'by_plate': defaultdict(lambda: [0, 0.0]), 'by_platform': defaultdict(lambda: [0, 0.0]),
     'by_apr_store': defaultdict(lambda: [0, 0.0]), 'by_shop': defaultdict(lambda: [0, 0.0])}
for t in trades:
    pay = (t.get('payTime') or t.get('consignTime') or '')[:10]
    amt = float(t.get('payment') or 0)
    shop = t.get('shopName') or ''
    plate, platform, store = classify(shop)
    S['total_orders'] += 1; S['total_amount'] += amt
    S['by_day'][pay][0] += 1; S['by_day'][pay][1] += amt
    S['by_plate'][plate][0] += 1; S['by_plate'][plate][1] += amt
    S['by_platform'][platform][0] += 1; S['by_platform'][platform][1] += amt
    if plate == 'APR' and store:
        S['by_apr_store'][store][0] += 1; S['by_apr_store'][store][1] += amt
    S['by_shop'][norm_shop(shop)][0] += 1; S['by_shop'][norm_shop(shop)][1] += amt

# ============ 库存（金额口径） ============
wh_map = {}
for row in xlsx_sheets(ROOT + '/销售渠道匹配和发货仓库匹配.xlsx')['发货仓库匹配'][1:]:
    if row and row[0]:
        wh_map[norm_wh(row[0])] = {'pos': row[1] if len(row) > 1 else '', 'area': row[2] if len(row) > 2 else '', 'prod': row[3] if len(row) > 3 else ''}

inv = json.load(open(ROOT + '/inventory_raw.json', encoding='utf-8'))
I = {'total_amount': 0.0, 'total_qty': 0, 'by_pos': defaultdict(float), 'by_area': defaultdict(float),
     'by_wh': defaultdict(lambda: [0.0, 0]), 'by_product_kw': defaultdict(float)}
def prod_kw(name):
    n = str(name or '')
    if 'iphone' in n.lower() or 'ipad' in n.lower() or 'macbook' in n.lower() or 'imac' in n.lower() or 'watch' in n.lower():
        return '苹果主机'
    if '舒尔' in n: return '舒尔'
    if 'demo' in n.lower(): return '演示机'
    if 'applecare' in n.lower() or '碎屏' in n or '服务' in n: return '服务类'
    if '配件' in n or 'case' in n.lower() or '笔' in n or '键盘' in n or '鼠标' in n or '妙控' in n: return '原装配件'
    return '其他'
for r in inv:
    qty = float(r.get('currentQuantity') or 0)
    cost = float(r.get('costPrice') or 0)
    amt = qty * cost
    I['total_amount'] += amt; I['total_qty'] += qty
    w = norm_wh(r.get('warehouseName') or '')
    wm = wh_map.get(w, {})
    I['by_pos'][wm.get('pos', '未匹配')] += amt
    I['by_area'][wm.get('area', '未匹配')] += amt
    I['by_wh'][w][0] += amt; I['by_wh'][w][1] += qty
    I['by_product_kw'][prod_kw(r.get('goodsName') or '')] += amt

def d2d(d): return {k: v for k, v in sorted(d.items())}

out = {
    'sales': {
        'period': '2026-08-01~2026-08-26', 'by_paytime': True,
        'total_orders': S['total_orders'], 'total_amount': round(S['total_amount'], 2),
        'avg_ticket': round(S['total_amount'] / S['total_orders'], 2) if S['total_orders'] else 0,
        'by_day': d2d({k: {'orders': v[0], 'amount': round(v[1], 2)} for k, v in S['by_day'].items()}),
        'by_plate': d2d({k: {'orders': v[0], 'amount': round(v[1], 2)} for k, v in S['by_plate'].items()}),
        'by_platform': d2d({k: {'orders': v[0], 'amount': round(v[1], 2)} for k, v in S['by_platform'].items()}),
        'by_apr_store': d2d({k: {'orders': v[0], 'amount': round(v[1], 2)} for k, v in S['by_apr_store'].items()}),
    },
    'inventory': {
        'total_amount': round(I['total_amount'], 2), 'total_qty': int(I['total_qty']),
        'by_pos': d2d({k: round(v, 2) for k, v in I['by_pos'].items()}),
        'by_area': d2d({k: round(v, 2) for k, v in I['by_area'].items()}),
        'by_product_kw': d2d({k: round(v, 2) for k, v in I['by_product_kw'].items()}),
        'top_wh': d2d({k: {'amount': round(v[0], 2), 'qty': v[1]} for k, v in sorted(I['by_wh'].items(), key=lambda x: -x[1][0])[:12]}),
    },
}
json.dump(out, open(ROOT + '/agg_summary.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('=== 销售（8月1-26，按支付时间）===')
print('单数', out['sales']['total_orders'], '金额', out['sales']['total_amount'], '客单价', out['sales']['avg_ticket'])
print('板块:', json.dumps(out['sales']['by_plate'], ensure_ascii=False))
print('平台:', json.dumps(out['sales']['by_platform'], ensure_ascii=False))
print('APR门店:', json.dumps(out['sales']['by_apr_store'], ensure_ascii=False))
print()
print('=== 库存（金额=数量×成本价）===')
print('总额', out['inventory']['total_amount'], '件数', out['inventory']['total_qty'])
print('仓位:', json.dumps(out['inventory']['by_pos'], ensure_ascii=False))
print('区域:', json.dumps(out['inventory']['by_area'], ensure_ascii=False))
print('品类关键词:', json.dumps(out['inventory']['by_product_kw'], ensure_ascii=False))
