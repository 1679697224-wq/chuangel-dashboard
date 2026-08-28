# -*- coding: utf-8 -*-
"""全量刷新：合并两份销售明细账(8/1-27) + 客流4 + 舒尔日报828"""
import json, re, io
from collections import defaultdict
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta

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
def xdate(v):
    try:
        return (EPOCH + timedelta(days=float(v))).strftime('%Y-%m-%d')
    except Exception:
        return ''

def read_sales_xlsx(path):
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
    sheet = wb.find('m:sheets/m:sheet', NS)
    rid = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
    root = ET.fromstring(z.read(relmap.get(rid, '')))
    rows = []
    for row in root.findall('.//m:row', NS):
        cells = {}
        for c in row.findall('m:c', NS):
            t = c.get('t'); v = c.find('m:v', NS); isel = c.find('m:is', NS)
            ref = c.get('r', '')
            col = ''.join(ch for ch in ref if ch.isalpha())
            if t == 's' and v is not None: val = ss[int(v.text)]
            elif v is not None: val = v.text
            elif isel is not None: val = ''.join(x.text or '' for x in isel.findall('.//m:t', NS))
            else: val = ''
            cells[col] = val
        rows.append(cells)
    return rows

# ===== 合并两份销售明细账（去重 by 订单+货品）=====
PAID = {'已完成', '发货在途', '待发货-已递交'}
lines = {}
for path in [ROOT + '/销售单明细账.xlsx', '/Users/lili/Downloads/销售单明细账828.xlsx']:
    for c in read_sales_xlsx(path)[1:]:
        d = xdate(c.get('Z', ''))
        if not ('2026-08-01' <= d <= '2026-08-27'): continue
        st = str(c.get('AB', '') or '').strip()
        if st not in PAID and st != '待审核': continue
        key = (c.get('C', ''), c.get('D', ''))
        sp = str(c.get('R', '')).strip()
        sp = sp.split('(')[0].strip().split('（')[0].strip()
        lines[key] = {
            'channel': c.get('A', ''), 'order': c.get('C', ''), 'goods_no': c.get('D', ''),
            'qty': num(c.get('I', 0)), 'amount': num(c.get('J', 0)), 'profit': num(c.get('L', 0)),
            'pay_time': d, 'goods_class': c.get('AE', ''), 'salesperson': sp, 'status': st,
            'brand': c.get('B', '')
        }
print('合并后行数:', len(lines), '| 单数:', len(set(l['order'] for l in lines.values())))

json.dump(list(lines.values()), open(ROOT + '/sales_lines_828.json', 'w'), ensure_ascii=False)

# ===== 聚合 =====
plate = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'orders': set(), 'audit': 0.0})
platform = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'orders': set()})
aprst = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'orders': set(), 'on': 0.0, 'off': 0.0})
daily = defaultdict(float)
person = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'orders': set(), 'on': 0.0, 'off': 0.0, 'store': '', 'host': 0.0, 'pp': 0.0})
for ln in lines.values():
    amt, profit, qty = ln['amount'], ln['profit'], ln['qty']
    p, pf, st = classify(ln['channel'])
    plate[p]['amount'] += amt; plate[p]['profit'] += profit; plate[p]['qty'] += qty
    plate[p]['orders'].add(ln['order'])
    if ln['status'] == '待审核': plate[p]['audit'] += amt
    platform[pf]['amount'] += amt; platform[pf]['profit'] += profit
    platform[pf]['orders'].add(ln['order'])
    daily[ln['pay_time']] += amt
    gc = ln['goods_class']
    is_host = ('iPhone' in gc) or ('Mac' in gc) or ('iPad' in gc) or ('Watch' in gc)
    if p == 'APR':
        aprst[st]['amount'] += amt; aprst[st]['profit'] += profit; aprst[st]['qty'] += qty
        aprst[st]['orders'].add(ln['order'])
        if pf == 'APR-线上': aprst[st]['on'] += amt
        else: aprst[st]['off'] += amt
    sp = ln['salesperson']
    if sp:
        person[sp]['amount'] += amt; person[sp]['profit'] += profit; person[sp]['qty'] += qty
        person[sp]['orders'].add(ln['order'])
        person[sp]['store'] = st or p
        if is_host: person[sp]['host'] += qty
        else: person[sp]['pp'] += qty
        if p == 'APR':
            if pf == 'APR-线上': person[sp]['on'] += amt
            else: person[sp]['off'] += amt

F = {}
F['plate'] = {k: {'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2), 'qty': round(v['qty'], 1),
                  'orders': len(v['orders']), 'margin': round(v['profit']/v['amount']*100, 2) if v['amount'] else 0,
                  'avg_ticket': round(v['amount']/len(v['orders']), 2) if v['orders'] else 0}
              for k, v in plate.items()}
F['apr_store'] = {k: dict({'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2),
                           'qty': round(v['qty'], 1), 'orders': len(v['orders']),
                           'margin': round(v['profit']/v['amount']*100, 2) if v['amount'] else 0,
                           'avg_ticket': round(v['amount']/len(v['orders']), 2) if v['orders'] else 0},
                          on=round(v['on'], 2), off=round(v['off'], 2))
                  for k, v in aprst.items()}
F['platform'] = {k: {'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2), 'orders': len(v['orders']),
                     'margin': round(v['profit']/v['amount']*100, 2) if v['amount'] else 0}
                 for k, v in sorted(platform.items(), key=lambda x: -x[1]['amount'])}
F['daily'] = {k: round(v, 2) for k, v in sorted(daily.items())}
F['salesperson'] = {k: {'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2), 'qty': round(v['qty'], 1),
                        'orders': len(v['orders']), 'on': round(v['on'], 2), 'off': round(v['off'], 2),
                        'store': v['store'], 'host': round(v['host'], 1), 'pp': round(v['pp'], 1)}
                    for k, v in sorted(person.items(), key=lambda x: -x[1]['amount'])}
F['audit_total'] = round(sum(v['audit'] for v in plate.values()), 2)
F['total_paid'] = round(sum(v['amount'] for v in plate.values()), 2)

print()
print('== 板块(8/1-27 分摊后) ==')
for k, v in F['plate'].items():
    print(' ', k, round(v['amount']/10000, 2), '万 毛利', round(v['profit']/10000, 2), '万 毛利率', v['margin'], '单', v['orders'])
print('== 公司合计 ==', round(F['total_paid']/10000, 2), '万 (待审核', round(F['audit_total']/10000, 2), ')')
print('== 平台 ==')
for k, v in F['platform'].items():
    print(' ', k, round(v['amount']/10000, 2), '万', v['margin'], '%')
print('== 门店 ==')
for k, v in F['apr_store'].items():
    print(' ', k, round(v['amount']/10000, 2), '万', v['margin'], '% 单', v['orders'])
print('== 销售员 TOP5 ==')
for k, v in list(F['salesperson'].items())[:5]:
    print(' ', k, round(v['amount']/10000, 2), '万')
print('== 8/27 日销 ==', F['daily'].get('2026-08-27'))
json.dump(F, open(ROOT + '/fill_data_828.json', 'w'), ensure_ascii=False, indent=1)
print('saved fill_data_828.json')
