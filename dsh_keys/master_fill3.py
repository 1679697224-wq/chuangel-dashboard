# -*- coding: utf-8 -*-
"""主聚合 v3：销售=分摊后金额, 按付款时间 8/1-26, 含已完成/发货在途/待发货(待审核单列)"""
import json, re
from runtime_business_data import load_runtime_business_data
from collections import defaultdict
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta

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
def xdate(v):
    try:
        return (datetime(1899, 12, 30) + timedelta(days=float(v))).strftime('%Y-%m-%d')
    except:
        return ''

# ===== 读取销售单明细账（全部行） =====
z = ZipFile(ROOT + '/销售单明细账.xlsx')
wb = ET.fromstring(z.read('xl/workbook.xml'))
rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
relmap = {rel.get('Id'): ('xl/' + rel.get('Target') if not rel.get('Target').startswith('/') else rel.get('Target')[1:]) for rel in rels}
ss = []
sst = ET.fromstring(z.read('xl/sharedStrings.xml'))
ss = [''.join(t.text or '' for t in si.findall('.//m:t', NS)) for si in sst.findall('m:si', NS)]
sheet = wb.find('m:sheets/m:sheet', NS)
rid = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
target = relmap.get(rid, '')
root = ET.fromstring(z.read(target))

raw_rows = []
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
    raw_rows.append(cells)

PAID_OK = {'已完成', '发货在途', '待发货-已递交'}
PAID_ALL = PAID_OK | {'待审核'}

lines = []
for c in raw_rows[1:]:
    d = xdate(c.get('Z', ''))
    if not ('2026-08-01' <= d <= '2026-08-26'): continue
    st = str(c.get('AB', '') or '').strip()
    if st not in PAID_ALL: continue
    sp = str(c.get('R', '')).strip()
    sp = sp.split('(')[0].strip().split('（')[0].strip()
    lines.append({
        'channel': c.get('A', ''), 'brand': c.get('B', ''), 'order': c.get('C', ''),
        'goods_no': c.get('D', ''), 'goods_name': c.get('E', ''),
        'qty': num(c.get('I', 0)), 'amount': num(c.get('J', 0)), 'cost': num(c.get('K', 0)),
        'profit': num(c.get('L', 0)), 'warehouse': c.get('M', ''),
        'pay_time': d + ' ' + (xdate(c.get('Z', '')).split(' ')[0] if False else ''),
        'goods_class': c.get('AE', ''), 'salesperson': sp, 'status': st
    })

json.dump(lines, open(ROOT + '/sales_lines_paid.json', 'w'), ensure_ascii=False)
print('行数:', len(lines))

F = {}
plate = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'orders': set(), 'audit': 0.0})
platform = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'orders': set()})
aprst = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'orders': set(), 'on': 0.0, 'off': 0.0})
daily = defaultdict(float)
apr_struct = defaultdict(float)
person = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'orders': set(), 'on': 0.0, 'off': 0.0, 'store': '', 'host': 0.0, 'pp': 0.0})
for ln in lines:
    amt, profit, qty = ln['amount'], ln['profit'], ln['qty']
    p, pf, st = classify(ln['channel'])
    plate[p]['amount'] += amt; plate[p]['profit'] += profit; plate[p]['qty'] += qty
    plate[p]['orders'].add(ln['order'])
    if ln['status'] == '待审核': plate[p]['audit'] += amt
    platform[pf]['amount'] += amt; platform[pf]['profit'] += profit
    platform[pf]['orders'].add(ln['order'])
    daily[ln['pay_time'][:10]] += amt
    gc_all = ln['goods_class']
    is_host = ('iPhone' in gc_all) or ('Mac' in gc_all) or ('iPad' in gc_all) or ('Watch' in gc_all)
    if p == 'APR':
        aprst[st]['amount'] += amt; aprst[st]['profit'] += profit; aprst[st]['qty'] += qty
        aprst[st]['orders'].add(ln['order'])
        if pf == 'APR-线上': aprst[st]['on'] += amt
        else: aprst[st]['off'] += amt
        if 'iPhone' in gc_all: apr_struct['iPhone'] += amt
        elif 'Mac' in gc_all: apr_struct['Mac'] += amt
        elif 'iPad' in gc_all: apr_struct['iPad'] += amt
        elif 'Watch' in gc_all: apr_struct['Watch'] += amt
        elif 'AirPods' in gc_all: apr_struct['AirPods'] += amt
        else: apr_struct['其他/配件'] += amt
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

def fin(d):
    return {k: {'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2),
                'qty': round(v['qty'], 1), 'orders': len(v['orders']),
                'margin': round(v['profit'] / v['amount'] * 100, 2) if v['amount'] else 0,
                'avg_ticket': round(v['amount'] / len(v['orders']), 2) if v['orders'] else 0}
            for k, v in d.items()}
F['plate'] = fin(plate)
F['apr_store'] = {k: dict(fin({k: v})[k], on=round(v['on'], 2), off=round(v['off'], 2)) for k, v in aprst.items()}
F['platform'] = {k: {'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2), 'orders': len(v['orders']),
                     'margin': round(v['profit'] / v['amount'] * 100, 2) if v['amount'] else 0}
                 for k, v in sorted(platform.items(), key=lambda x: -x[1]['amount'])}
F['daily'] = {k: round(v, 2) for k, v in sorted(daily.items())}
F['apr_struct'] = {k: round(v, 2) for k, v in apr_struct.items()}
F['salesperson'] = {k: {'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2),
                        'qty': round(v['qty'], 1), 'orders': len(v['orders']),
                        'on': round(v['on'], 2), 'off': round(v['off'], 2), 'store': v['store'],
                        'host': round(v['host'], 1), 'pp': round(v['pp'], 1)}
                    for k, v in sorted(person.items(), key=lambda x: -x[1]['amount'])}
F['audit_total'] = round(sum(v['audit'] for v in plate.values()), 2)
F['total_paid'] = round(sum(v['amount'] for v in plate.values()), 2)

# 个人任务
pt = xlsx_sheets('/Users/lili/Desktop/销售/APR/202608/个人任务制定.xlsx')['Sheet1']
ptask = {}
for r in pt[1:]:
    if len(r) >= 5 and str(r[1]).strip():
        ptask[str(r[1]).strip()] = {'task': num(r[4]), 'store': str(r[0]).strip()}
F['person_task'] = ptask

# 同比(API实付 8/1-26)
def load_api(path, is2025):
    d = json.load(open(path, encoding='utf-8'))
    out = defaultdict(float)
    for o in d:
        if is2025:
            tno = str(o.get('tradeNo', ''))
            date = tno[2:10] if len(tno) >= 10 else ''
        else:
            ct = str(o.get('consignTime', '') or '')
            date = ct[:10].replace('-', '')
        if not re.match(r'^\d{8}$', date): continue
        yy, mm, dd = date[:4], date[4:6], date[6:]
        if yy != ('2025' if is2025 else '2026') or mm != '08' or int(dd) > 26: continue
        p, pf, st = classify(o.get('shopName', ''))
        out[p] += num(o.get('payment', 0))
        if p == 'APR': out['@store:' + st] += num(o.get('payment', 0))
        out['@day:' + date] += num(o.get('payment', 0))
    return out
a26 = load_api(ROOT + '/sales_raw_202608.json', False)
a25 = load_api(ROOT + '/sales_raw_202508.json', True)
def yoy(a, b): return round((a - b) / b * 100, 1) if b else None
F['yoy_plate'] = {k: {'cur': round(a26.get(k, 0), 2), 'last': round(a25.get(k, 0), 2),
                      'yoy': yoy(a26.get(k, 0), a25.get(k, 0))} for k in plate.keys()}
F['yoy_store'] = {st: {'cur': round(a26.get('@store:' + st, 0), 2), 'last': round(a25.get('@store:' + st, 0), 2),
                       'yoy': yoy(a26.get('@store:' + st, 0), a25.get('@store:' + st, 0))} for st in aprst.keys()}
tot26 = sum(a26.get(k, 0) for k in ('APR', 'Apple电商', 'Shure电商', '分销', '天羽乐购', '其他'))
tot25 = sum(a25.get(k, 0) for k in ('APR', 'Apple电商', 'Shure电商', '分销', '天羽乐购', '其他'))
F['company_yoy'] = yoy(tot26, tot25)
F['lastyear_trend'] = {dd: round(a25.get('@day:' + dd, 0), 2) for dd in
                       ['20250820', '20250821', '20250822', '20250823', '20250824', '20250825', '20250826']}

# 库存(商务表)
inv = xlsx_sheets(ROOT + '/库存分析表_260826.xlsx')
runtime_business = load_runtime_business_data()
F['inv_category'] = runtime_business['inv_category']
F['inv_machine'] = runtime_business['inv_machine']
F['inv_aging'] = {
    '0~30 天': 869.466139999999, '30~60 天': 217.776742, '60~90 天': 57.56853,
    '90~180 天': 351.86624, '180~360 天': 230.19718, '360 天以上': 123.977267,
}
kl = inv['库龄'][1:]
severe_count = 0; risk = []
for r in kl:
    if len(r) < 25: continue
    if num(r[24]) > 0: severe_count += 1
    age = num(r[10]); amt = num(r[12])
    if age >= 90 and amt > 0:
        risk.append({'age': int(age), 'amount': round(amt, 2), 'brand': r[6] if len(r) > 6 else '',
                     'cat': r[7] if len(r) > 7 else '', 'name': r[2] if len(r) > 2 else '',
                     'qty': int(num(r[11])), 'wh': r[0] if len(r) > 0 else ''})
risk.sort(key=lambda x: -x['amount'])
F['inv_severe_count'] = severe_count
F['inv_risk_top'] = risk[:15]

# 电商日报
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
                             'uv': int(num(vals[9])) if len(vals) > 9 else 0}
        break
tm = xlsx_sheets('/Users/lili/Downloads/天猫舒尔旗舰店日报反馈表(57).xlsx')
tm_aug = {'sales': 0.0, 'orders': 0, 'pv': 0, 'uv': 0, 'days': 0}
for r in tm['日报表']:
    if len(r) > 1 and isinstance(r[1], str) and re.match(r'^\d+(\.0+)?$', r[1].strip()):
        try:
            dt = (datetime(1899, 12, 30) + timedelta(days=float(r[1]))).strftime('%Y-%m-%d')
        except Exception:
            continue
        if '2026-08-01' <= dt <= '2026-08-26':
            tm_aug['sales'] += num(r[2]); tm_aug['orders'] += num(r[4])
            tm_aug['pv'] += num(r[10]); tm_aug['uv'] += num(r[11]); tm_aug['days'] += 1
F['tm_shure_aug'] = {k: round(v, 2) for k, v in tm_aug.items()}

json.dump(F, open(ROOT + '/fill_data.json', 'w'), ensure_ascii=False, indent=1)
print('saved fill_data.json')
print()
print('== 板块(分摊后·含在途, 待审核单列) ==')
for k, v in F['plate'].items():
    print(' ', k, round(v['amount'] / 10000, 2), '万 毛利', round(v['profit'] / 10000, 2), '万 毛利率', v['margin'], '客单', v['avg_ticket'], '单', v['orders'], '待审核', round(plate[k]['audit'] / 10000, 2))
print('== 公司已支付合计 ==', round(F['total_paid'] / 10000, 2), '万, 其中待审核', round(F['audit_total'] / 10000, 2), '万')
print('== 公司同比 ==', F['company_yoy'], '%')
for k, v in F['yoy_plate'].items():
    print('  ', k, 'cur', round(v['cur'] / 10000, 2), 'last', round(v['last'] / 10000, 2), 'yoy', v['yoy'])
print('== 门店(万) ==')
for k, v in F['apr_store'].items():
    y = F['yoy_store'].get(k, {})
    print(' ', k, round(v['amount'] / 10000, 2), '毛利率', v['margin'], '客单', v['avg_ticket'], '线上', round(v['on'] / 10000, 2), '线下', round(v['off'] / 10000, 2), '同比', y.get('yoy'))
print('== 销售员 TOP12 ==')
for k, v in list(F['salesperson'].items())[:12]:
    t = ptask.get(k, {}).get('task', 0)
    print(' ', k, v['store'], round(v['amount'] / 10000, 2), '任务', t, '达成', round(v['amount'] / 10000 / t * 100, 1) if t else '-', '线上', round(v['on'] / 10000, 2), '线下', round(v['off'] / 10000, 2), '主机', v['host'], '配件', v['pp'])
print('== 平台 ==')
for k, v in F['platform'].items():
    print(' ', k, round(v['amount'] / 10000, 2), '万 毛利率', v['margin'])
print('== APR 品类 ==', {k: round(v / 10000, 1) for k, v in F['apr_struct'].items()})
print('== 8/20-26 日销 ==', {k: round(v / 10000, 1) for k, v in F['daily'].items() if k >= '2026-08-20'})
print('== 去年 8/20-26 ==', {k: round(v / 10000, 1) for k, v in F['lastyear_trend'].items()})
print('== 京东舒尔 ==', F.get('jd_shure_sum'), ' 天猫舒尔8/1-16 ==', F.get('tm_shure_aug'))
