# -*- coding: utf-8 -*-
"""主聚合 v2：在 sales_lines_export(原口径) 基础上补充业务员/门店线上线下/同比/品类/日报"""
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
    except: return 0.0

F = {}

# ===== 1) 业务员映射：从销售单明细账 (order,goods_no) -> 业务员 =====
def xlsx_rows(path):
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
    target = relmap.get(rid, '')
    root = ET.fromstring(z.read(target))
    out = []
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
        out.append(cells)
    return out

sp_map = {}
for c in xlsx_rows(ROOT + '/销售单明细账.xlsx')[1:]:
    order = c.get('C', ''); gno = c.get('D', '')
    if order and gno:
        sp = str(c.get('R', '')).strip()
        sp = sp.split('(')[0].strip()
        sp = sp.split('（')[0].strip()
        sp_map[(order, gno)] = sp

# ===== 2) 销售：原口径 sales_lines_export + 业务员 =====
lines = json.load(open(ROOT + '/sales_lines_export.json', encoding='utf-8'))
for ln in lines:
    ln['salesperson'] = sp_map.get((ln['order'], ln['goods_no']), '')
    if not ln['salesperson']:
        ln['salesperson'] = sp_map.get((ln['order'], ''), '')

plate = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'orders': set()})
platform = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'orders': set()})
aprst = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'orders': set(), 'on': 0.0, 'off': 0.0})
aprdaily = defaultdict(float)
apr_struct = defaultdict(float)
person = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'orders': set(), 'on': 0.0, 'off': 0.0, 'store': '', 'host': 0.0, 'pp': 0.0})
for ln in lines:
    amt, profit, qty = num(ln['amount']), num(ln['profit']), num(ln['qty'])
    p, pf, st = classify(ln['channel'])
    plate[p]['amount'] += amt; plate[p]['profit'] += profit; plate[p]['qty'] += qty
    plate[p]['orders'].add(ln['order'])
    platform[pf]['amount'] += amt; platform[pf]['profit'] += profit
    platform[pf]['orders'].add(ln['order'])
    gc_all = str(ln.get('goods_class', ''))
    is_host = ('iPhone' in gc_all) or ('Mac' in gc_all) or ('iPad' in gc_all) or ('Watch' in gc_all)
    if p == 'APR':
        aprst[st]['amount'] += amt; aprst[st]['profit'] += profit; aprst[st]['qty'] += qty
        aprst[st]['orders'].add(ln['order'])
        if pf == 'APR-线上': aprst[st]['on'] += amt
        else: aprst[st]['off'] += amt
        d = str(ln['pay_time'])[:10]
        aprdaily[d] += amt
        if 'iPhone' in gc_all: apr_struct['iPhone'] += amt
        elif 'Mac' in gc_all: apr_struct['Mac'] += amt
        elif 'iPad' in gc_all: apr_struct['iPad'] += amt
        elif 'Watch' in gc_all: apr_struct['Watch'] += amt
        elif 'AirPods' in gc_all: apr_struct['AirPods'] += amt
        else: apr_struct['其他/配件'] += amt
    sp = str(ln.get('salesperson', '')).strip()
    if sp:
        person[sp]['amount'] += amt; person[sp]['profit'] += profit; person[sp]['qty'] += qty
        person[sp]['orders'].add(ln['order'])
        person[sp]['store'] = st or p
        if is_host: person[sp]['host'] += qty
        else: person[sp]['pp'] += qty
        if p == 'APR':
            if pf == 'APR-线上': person[sp]['on'] += amt
            else: person[sp]['off'] += amt

F['plate'] = {k: {'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2),
                  'qty': round(v['qty'], 1), 'orders': len(v['orders']),
                  'margin': round(v['profit'] / v['amount'] * 100, 2) if v['amount'] else 0,
                  'avg_ticket': round(v['amount'] / len(v['orders']), 2) if v['orders'] else 0}
              for k, v in plate.items()}
F['apr_store'] = {k: {'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2),
                      'qty': round(v['qty'], 1), 'orders': len(v['orders']),
                      'margin': round(v['profit'] / v['amount'] * 100, 2) if v['amount'] else 0,
                      'avg_ticket': round(v['amount'] / len(v['orders']), 2) if v['orders'] else 0,
                      'on': round(v['on'], 2), 'off': round(v['off'], 2)}
                  for k, v in aprst.items()}
F['apr_daily'] = {k: round(v, 2) for k, v in sorted(aprdaily.items())}
F['apr_struct'] = {k: round(v, 2) for k, v in apr_struct.items()}
F['salesperson'] = {k: {'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2),
                        'qty': round(v['qty'], 1), 'orders': len(v['orders']),
                        'on': round(v['on'], 2), 'off': round(v['off'], 2), 'store': v['store'],
                        'host': round(v['host'], 1), 'pp': round(v['pp'], 1)}
                    for k, v in sorted(person.items(), key=lambda x: -x[1]['amount'])}
F['platform'] = {k: {'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2), 'orders': len(v['orders']),
                     'margin': round(v['profit'] / v['amount'] * 100, 2) if v['amount'] else 0}
                 for k, v in sorted(platform.items(), key=lambda x: -x[1]['amount'])}

# 个人任务（运营）
pt = xlsx_sheets('/Users/lili/Desktop/销售/APR/202608/个人任务制定.xlsx')['Sheet1']
ptask = {}
for r in pt[1:]:
    if len(r) >= 5 and str(r[1]).strip():
        ptask[str(r[1]).strip()] = {'task': num(r[4]) if len(r) > 4 else 0, 'store': str(r[0]).strip()}
F['person_task'] = ptask

# ===== 3) 同比：API 实付（2026-08 vs 2025-08，1-26日） =====
def load_api(path, is2025):
    d = json.load(open(path, encoding='utf-8'))
    out = defaultdict(lambda: {'amount': 0.0, 'orders': 0, 'days': defaultdict(float)})
    for o in d:
        shop = o.get('shopName', '')
        if is2025:
            tno = str(o.get('tradeNo', ''))
            date = tno[2:10] if len(tno) >= 10 else ''
        else:
            ct = str(o.get('consignTime', '') or '')
            date = ct[:10].replace('-', '')
        if not re.match(r'^\d{8}$', date): continue
        yy, mm, dd = date[:4], date[4:6], date[6:]
        if yy != ('2025' if is2025 else '2026') or mm != '08': continue
        if int(dd) > 26: continue
        p, pf, st = classify(shop)
        amt = num(o.get('payment', 0))
        out[p]['amount'] += amt; out[p]['orders'] += 1
        if p == 'APR':
            out['@store:' + st]['amount'] += amt; out['@store:' + st]['orders'] += 1
        out['@day:' + date]['amount'] += amt
    return out

a26 = load_api(ROOT + '/sales_raw_202608.json', False)
a25 = load_api(ROOT + '/sales_raw_202508.json', True)

def yoy(a, b):
    return round((a - b) / b * 100, 1) if b else None

F['yoy_plate'] = {}
for k in plate.keys():
    if k in a26 and k in a25:
        F['yoy_plate'][k] = {'cur': round(a26[k]['amount'], 2), 'last': round(a25[k]['amount'], 2),
                             'yoy': yoy(a26[k]['amount'], a25[k]['amount'])}
F['yoy_store'] = {}
for st in aprst.keys():
    k = '@store:' + st
    if k in a26 and k in a25:
        F['yoy_store'][st] = {'cur': round(a26[k]['amount'], 2), 'last': round(a25[k]['amount'], 2),
                              'yoy': yoy(a26[k]['amount'], a25[k]['amount'])}
def plate_total(d):
    return sum(d[k]['amount'] for k in ('APR', 'Apple电商', 'Shure电商', '分销', '天羽乐购', '其他') if k in d)
F['company_yoy'] = yoy(plate_total(a26), plate_total(a25))
F['lastyear_trend'] = {dd: round(a25['@day:' + dd]['amount'], 2) for dd in
                       ['20250820', '20250821', '20250822', '20250823', '20250824', '20250825', '20250826']}

# ===== 4) 库存：商务表 =====
inv = xlsx_sheets(ROOT + '/库存分析表_260826.xlsx')
F['inv_category'] = [
    {'name': '苹果主机', 'amount': 1603.3783376326, 'qty': 2422, 'pct': 76.03},
    {'name': '原装配件', 'amount': 139.6055536141, 'qty': 3178, 'pct': 6.62},
    {'name': '舒尔', 'amount': 302.8152990727, 'qty': 6065, 'pct': 14.36},
    {'name': '第三方配件', 'amount': 63.0520116143, 'qty': 12293, 'pct': 2.99},
]
F['inv_machine'] = {
    'APR 门店': {'normal': 1136.2241968626, 'demo': 299.498783999499, 'defect': 6.858652},
    '电商-羽通': {'normal': 242.3158729986, 'demo': 0.0, 'defect': 4.7413699999},
    '电商-啟韬': {'normal': 90.9637199998, 'demo': 0.0, 'defect': 4.259351},
    '电商-舒尔': {'normal': 136.4208829682, 'demo': 0.0, 'defect': 26.0231896109},
    '电商-其他': {'normal': 6.7176799995, 'demo': 0.0, 'defect': 0.95711},
    '京东-舒尔': {'normal': 92.2035994945, 'demo': 0.0, 'defect': 0.0},
}
F['inv_aging'] = {
    '0~30 天': 869.466139999999, '30~60 天': 217.776742, '60~90 天': 57.56853,
    '90~180 天': 351.86624, '180~360 天': 230.19718, '360 天以上': 123.977267,
}
kl = inv['库龄'][1:]
severe_count = 0
risk = []
for r in kl:
    if len(r) < 25: continue
    amt360 = num(r[24]) if len(r) > 24 else 0.0
    if amt360 > 0: severe_count += 1
    age = num(r[10]); amt = num(r[12])
    if age >= 90 and amt > 0:
        risk.append({'age': int(age), 'amount': round(amt, 2), 'brand': r[6] if len(r) > 6 else '',
                     'cat': r[7] if len(r) > 7 else '', 'name': r[2] if len(r) > 2 else '',
                     'qty': int(num(r[11])), 'wh': r[0] if len(r) > 0 else ''})
risk.sort(key=lambda x: -x['amount'])
F['inv_severe_count'] = severe_count
F['inv_risk_top'] = risk[:15]

# ===== 5) 电商日报 =====
jd = xlsx_sheets('/Users/lili/Downloads/舒尔京东店铺日报-20260826.xlsx')
for r in jd['店铺销售']:
    hit = [i for i, x in enumerate(r) if str(x).strip() == '汇总']
    if hit:
        vals = r[hit[0] + 1:]
        F['jd_shure_sum'] = {'sales': round(num(vals[0]), 2) if vals else 0,
                             'conv': round(num(vals[1]) * 100, 2) if len(vals) > 1 else 0,
                             'orders': int(num(vals[2])) if len(vals) > 2 else 0,
                             'aov': round(num(vals[3]), 2) if len(vals) > 3 else 0,
                             'pv': int(num(vals[8])) if len(vals) > 8 else 0,
                             'uv': int(num(vals[9])) if len(vals) > 9 else 0,
                             'click': round(num(vals[10]) * 100, 2) if len(vals) > 10 else 0}
        break
tm = xlsx_sheets('/Users/lili/Downloads/天猫舒尔旗舰店日报反馈表(57).xlsx')
EPOCH_D = __import__('datetime').datetime(1899, 12, 30)
from datetime import timedelta
tm_aug = {'sales': 0.0, 'orders': 0, 'pv': 0, 'uv': 0, 'days': 0}
for r in tm['日报表']:
    if len(r) > 1 and isinstance(r[1], str) and re.match(r'^\d+(\.0+)?$', r[1].strip()):
        try:
            dt = (EPOCH_D + timedelta(days=float(r[1]))).strftime('%Y-%m-%d')
        except Exception:
            continue
        if dt >= '2026-08-01' and dt <= '2026-08-26':
            tm_aug['sales'] += num(r[2]); tm_aug['orders'] += num(r[4])
            tm_aug['pv'] += num(r[10]); tm_aug['uv'] += num(r[11]); tm_aug['days'] += 1
F['tm_shure_aug'] = {k: round(v, 2) for k, v in tm_aug.items()}

json.dump(F, open(ROOT + '/fill_data.json', 'w'), ensure_ascii=False, indent=1)
print('saved fill_data.json')
print()
print('== 板块(分摊后) ==')
for k, v in F['plate'].items():
    print(' ', k, round(v['amount'] / 10000, 2), '万 毛利', round(v['profit'] / 10000, 2), '万 毛利率', v['margin'], '% 客单', v['avg_ticket'])
print('== 公司同比 ==', F['company_yoy'], '%')
print('== 板块同比 ==')
for k, v in F['yoy_plate'].items():
    print(' ', k, 'cur', round(v['cur'] / 10000, 2), '万 last', round(v['last'] / 10000, 2), '万 yoy', v['yoy'], '%')
print('== 门店(万) ==')
for k, v in F['apr_store'].items():
    y = F['yoy_store'].get(k, {})
    print(' ', k, round(v['amount'] / 10000, 2), '万 毛利', round(v['profit'] / 10000, 2), '毛利率', v['margin'], '客单', v['avg_ticket'], '线上', round(v['on'] / 10000, 2), '线下', round(v['off'] / 10000, 2), '同比', y.get('yoy'))
print('== 销售员 TOP10 ==')
for k, v in list(F['salesperson'].items())[:12]:
    t = ptask.get(k, {}).get('task', 0)
    print(' ', k, v['store'], round(v['amount'] / 10000, 2), '万 任务', t, '达成', round(v['amount'] / 10000 / t * 100, 1) if t else '-', '线上', round(v['on'] / 10000, 2), '线下', round(v['off'] / 10000, 2), '主机台', v['host'], '配件', v['pp'])
print('== 平台 ==')
for k, v in F['platform'].items():
    print(' ', k, round(v['amount'] / 10000, 2), '万 毛利率', v['margin'])
print('== APR 品类 ==', {k: round(v / 10000, 1) for k, v in F['apr_struct'].items()})
print('== APR 8/20-26 日销 ==', {k: round(v / 10000, 1) for k, v in F['apr_daily'].items() if k >= '2026-08-20'})
print('== 去年 8/20-26 ==', {k: round(v / 10000, 1) for k, v in F['lastyear_trend'].items()})
print('== 京东舒尔汇总 ==', F.get('jd_shure_sum'))
print('== 天猫舒尔8月 ==', F.get('tm_shure_aug'))
print('== 库龄360+ SKU ==', severe_count, ' TOP风险', len(F['inv_risk_top']))
