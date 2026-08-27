# -*- coding: utf-8 -*-
"""聚合：销售→渠道/门店，库存→仓位/品类；输出 吉客云数据/agg_*.json"""
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
    s = re.sub(r'^\[[0-9]{3}\]', '', str(s)).strip()
    s = s.rstrip('*').strip()
    return s

def norm_wh(s):
    return re.sub(r'^\[[0-9]{3}\]', '', str(s)).strip()

# 1) 销售渠道匹配
shop_map = {}
for row in xlsx_sheets(ROOT + '/销售渠道匹配和发货仓库匹配.xlsx')['销售渠道匹配'][1:]:
    if len(row) >= 5 and row[0]:
        shop_map[norm_shop(row[0])] = {'l1': row[1], 'l2': row[2], 'l3': row[3], 'l4': row[4]}

# 2) 仓库匹配
wh_map = {}
for row in xlsx_sheets(ROOT + '/销售渠道匹配和发货仓库匹配.xlsx')['发货仓库匹配'][1:]:
    if len(row) >= 4 and row[0]:
        wh_map[norm_wh(row[0])] = {'pos': row[1], 'area': row[2], 'prod': row[3]}

# 3) 产品线匹配：产品编码 -> 产品分类
prod_map = {}
for row in xlsx_sheets(ROOT + '/产品线与门店匹配数据表.xlsx')['产品线'][1:]:
    if len(row) >= 5 and row[2]:
        prod_map[row[2]] = row[4]  # 产品编码 -> 产品分类(苹果主机/原装配件...)

# ============ 销售聚合 ============
trades = json.load(open(ROOT + '/sales_raw_202608.json', encoding='utf-8'))
def channel_of(shop):
    n = norm_shop(shop)
    if n in shop_map:
        return shop_map[n]
    for k, v in shop_map.items():
        if k and (k in n or n in k):
            return v
    return {'l1': '其他', 'l2': '其他', 'l3': n, 'l4': n}

sales = {'total_orders': 0, 'total_amount': 0.0, 'by_day': defaultdict(lambda: {'orders': 0, 'amount': 0.0}),
         'by_channel': defaultdict(lambda: {'orders': 0, 'amount': 0.0}),
         'by_store': defaultdict(lambda: {'orders': 0, 'amount': 0.0}),
         'by_shop': defaultdict(lambda: {'orders': 0, 'amount': 0.0})}
for t in trades:
    pay = t.get('payTime') or t.get('consignTime') or ''
    amt = float(t.get('payment') or 0)
    day = pay[:10]
    shop = t.get('shopName') or ''
    ch = channel_of(shop)
    l3 = ch['l3'] or norm_shop(shop)
    sales['total_orders'] += 1
    sales['total_amount'] += amt
    sales['by_day'][day]['orders'] += 1
    sales['by_day'][day]['amount'] += amt
    sales['by_channel'][ch['l1']]['orders'] += 1
    sales['by_channel'][ch['l1']]['amount'] += amt
    sales['by_store'][l3]['orders'] += 1
    sales['by_store'][l3]['amount'] += amt
    sales['by_shop'][norm_shop(shop)]['orders'] += 1
    sales['by_shop'][norm_shop(shop)]['amount'] += amt

# ============ 库存聚合 ============
inv = json.load(open(ROOT + '/inventory_raw.json', encoding='utf-8'))
inv_agg = {'total_qty': 0, 'total_sku_wh': len(inv), 'by_warehouse_pos': defaultdict(float),
           'by_area': defaultdict(float), 'by_product': defaultdict(float), 'by_wh_name': defaultdict(float)}
for r in inv:
    qty = float(r.get('currentQuantity') or 0)
    inv_agg['total_qty'] += qty
    w = norm_wh(r.get('warehouseName') or '')
    wm = wh_map.get(w, {})
    inv_agg['by_warehouse_pos'][wm.get('pos', '未匹配')] += qty
    inv_agg['by_area'][wm.get('area', '未匹配')] += qty
    gn = r.get('goodsNo') or ''
    inv_agg['by_product'][prod_map.get(gn, '其他/未匹配')] += qty
    inv_agg['by_wh_name'][w] += qty

def d2d(d):
    return {k: v for k, v in sorted(d.items())}

out = {
    'sales': {
        'total_orders': sales['total_orders'],
        'total_amount': round(sales['total_amount'], 2),
        'avg_ticket': round(sales['total_amount'] / sales['total_orders'], 2) if sales['total_orders'] else 0,
        'by_day': d2d({k: dict(v) for k, v in sales['by_day'].items()}),
        'by_channel': d2d({k: dict(v) for k, v in sales['by_channel'].items()}),
        'by_store': d2d({k: dict(v) for k, v in sales['by_store'].items()}),
        'by_shop': d2d({k: dict(v) for k, v in sales['by_shop'].items()}),
    },
    'inventory': {
        'total_qty': round(inv_agg['total_qty'], 2),
        'total_sku_warehouse': inv_agg['total_sku_wh'],
        'by_warehouse_pos': d2d({k: round(v, 2) for k, v in inv_agg['by_warehouse_pos'].items()}),
        'by_area': d2d({k: round(v, 2) for k, v in inv_agg['by_area'].items()}),
        'by_product': d2d({k: round(v, 2) for k, v in inv_agg['by_product'].items()}),
        'top_warehouses': d2d({k: round(v, 2) for k, v in sorted(inv_agg['by_wh_name'].items(), key=lambda x: -x[1])[:15]}),
    },
}
json.dump(out, open(ROOT + '/agg_summary.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('=== 销售(8月, 按支付时间) ===')
print('单数:', out['sales']['total_orders'], '| 销售额:', out['sales']['total_amount'], '| 客单价:', out['sales']['avg_ticket'])
print('渠道:', json.dumps(out['sales']['by_channel'], ensure_ascii=False))
print('门店TOP:', json.dumps(dict(sorted(out['sales']['by_store'].items(), key=lambda x: -x[1]['amount'])[:12]), ensure_ascii=False))
print('=== 库存 ===')
print('总件数:', out['inventory']['total_qty'], '| SKU-仓记录:', out['inventory']['total_sku_warehouse'])
print('仓位:', json.dumps(out['inventory']['by_warehouse_pos'], ensure_ascii=False))
print('品类:', json.dumps(out['inventory']['by_product'], ensure_ascii=False))
