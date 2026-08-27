# -*- coding: utf-8 -*-
"""主聚合：为确认版看板生成全部真实数据(fill_data.json)"""
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

def norm_shop(s): return re.sub(r'^[[0-9]{3}]', '', str(s)).strip().rstrip('*').strip()
def norm_wh(s): return re.sub(r'^[[0-9]{3}]', '', str(s)).strip()

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

# ============ 1) 销售：导出表(分摊后金额/按付款时间) ============
lines = json.load(open(ROOT + '/sales_lines_export.json', encoding='utf-8'))
plate = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'orders': set()})
aprst = defaultdict(lambda: {'amount': 0.0, 'profit': 0.0, 'qty': 0.0, 'orders': set()})
aprdaily = defaultdict(float)
apr_struct = defaultdict(float)   # APR 主机品类
for ln in lines:
    amt, profit, qty = num(ln['amount']), num(ln['profit']), num(ln['qty'])
    p, pf, st = classify(ln['channel'])
    plate[p]['amount'] += amt; plate[p]['profit'] += profit; plate[p]['qty'] += qty
    plate[p]['orders'].add(ln['order'])
    if p == 'APR':
        aprst[st]['amount'] += amt; aprst[st]['profit'] += profit; aprst[st]['qty'] += qty
        aprst[st]['orders'].add(ln['order'])
        d = str(ln['pay_time'])[:10]
        aprdaily[d] += amt
        gc = str(ln.get('goods_class', ''))
        if 'iPhone' in gc: apr_struct['iPhone'] += amt
        elif 'Mac' in gc: apr_struct['Mac'] += amt
        elif 'iPad' in gc: apr_struct['iPad'] += amt
        elif 'Watch' in gc: apr_struct['Watch'] += amt
        elif 'AirPods' in gc: apr_struct['AirPods'] += amt
        else: apr_struct['其他/配件'] += amt

F['plate'] = {k: {'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2),
                  'qty': v['qty'], 'orders': len(v['orders']),
                  'margin': round(v['profit'] / v['amount'] * 100, 2) if v['amount'] else 0,
                  'avg_ticket': round(v['amount'] / len(v['orders']), 2) if v['orders'] else 0}
              for k, v in plate.items()}
F['apr_store'] = {k: {'amount': round(v['amount'], 2), 'profit': round(v['profit'], 2),
                      'qty': v['qty'], 'orders': len(v['orders']),
                      'margin': round(v['profit'] / v['amount'] * 100, 2) if v['amount'] else 0,
                      'avg_ticket': round(v['amount'] / len(v['orders']), 2) if v['orders'] else 0}
                  for k, v in aprst.items()}
F['apr_daily'] = {k: round(v, 2) for k, v in sorted(aprdaily.items())}
F['apr_struct'] = {k: round(v, 2) for k, v in apr_struct.items()}

# ============ 2) 同比：API 实付口径（2026-08 vs 2025-08） ============
def load_api(path, is2025):
    d = json.load(open(path, encoding='utf-8'))
    out = defaultdict(lambda: {'amount': 0.0, 'orders': 0, 'days': defaultdict(float)})
    for o in d:
        shop = o.get('shopName', '')
        if is2025:
            date = o.get('tradeNo', '')[:8]
        else:
            ct = o.get('consignTime', '') or ''
            date = ct[:10].replace('-', '')
        if not re.match(r'^d{8}$', date): continue
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

F['yoy_plate'] = {k: {'cur': round(a26[k]['amount'], 2), 'last': round(a25[k]['amount'], 2),
                      'yoy': yoy(a26[k]['amount'], a25[k]['amount'])} for k in plate.keys() if k in a26 and k in a25}
F['yoy_store'] = {}
for st in aprst.keys():
    k = '@store:' + st
    if k in a26 and k in a25:
        F['yoy_store'][st] = {'cur': round(a26[k]['amount'], 2), 'last': round(a25[k]['amount'], 2),
                              'yoy': yoy(a26[k]['amount'], a25[k]['amount'])}
F['company_yoy'] = yoy(a26['APR']['amount'] + a26['Apple电商']['amount'] + a26['Shure电商']['amount'] + a26.get('分销', {}).get('amount', 0) + a26.get('天羽乐购', {}).get('amount', 0) + a26.get('其他', {}).get('amount', 0),
                        a25['APR']['amount'] + a25['Apple电商']['amount'] + a25['Shure电商']['amount'] + a25.get('分销', {}).get('amount', 0) + a25.get('天羽乐购', {}).get('amount', 0) + a25.get('其他', {}).get('amount', 0))

# 去年趋势（8/20-8/26）
F['lastyear_trend'] = {}
for dd in ['20250820', '20250821', '20250822', '20250823', '20250824', '20250825', '20250826']:
    k = '@day:' + dd
    F['lastyear_trend'][dd] = round(a25[k]['amount'], 2)

# ============ 3) 库存：商务库存分析表_260826 ============
inv = xlsx_sheets(ROOT + '/库存分析表_260826.xlsx')
# 总览：分类 + 仓位 + 渠道库龄
z = inv['总览']
F['inv_category'] = [
    {'name': '苹果主机', 'amount': 1603.3783376326, 'qty': 2422},
    {'name': '原装配件', 'amount': 139.6055536141, 'qty': 3178},
    {'name': '舒尔', 'amount': 302.8152990727, 'qty': 6065},
    {'name': '第三方配件', 'amount': 63.0520116143, 'qty': 12293},
]
F['inv_machine'] = {
    'APR 门店': {'normal': 1136.2241968626, 'demo': 299.498783999499, 'defect': 6.858652},
    '电商-羽通': {'normal': 242.3158729986, 'demo': 0.0, 'defect': 4.7413699999},
    '电商-啟韬': {'normal': 90.9637199998, 'demo': 0.0, 'defect': 4.259351},
    '电商-舒尔': {'normal': 136.4208829682, 'demo': 0.0, 'defect': 26.0231896109},
    '电商-其他': {'normal': 6.7176799995, 'demo': 0.0, 'defect': 0.95711},
    '京东-舒尔': {'normal': 92.2035994945, 'demo': 0.0, 'defect': 0.0},
}
# 渠道库龄（总览 rows34-49 合计行34）
F['inv_aging'] = {
    '0~30 天': 869.466139999999, '30~60 天': 217.776742, '60~90 天': 57.56853,
    '90~180 天': 351.86624, '180~360 天': 230.19718, '360 天以上': 123.977267,
}
# 库龄 sheet：SKU 计数 + TOP 风险
kl = inv['库龄'][1:]  # 跳过重复表头
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

# ============ 4) 电商日报（京东舒尔汇总 + 天猫舒尔 8月） ============
jd = xlsx_sheets('/Users/lili/Downloads/舒尔京东店铺日报-20260826.xlsx')
for r in jd['店铺销售']:
    if len(r) > 3 and str(r[2]) == '汇总':
        F['jd_shure_sum'] = {'sales': num(r[3]), 'conv': num(r[4]) if len(r) > 4 else 0,
                             'orders': num(r[5]) if len(r) > 5 else 0, 'aov': num(r[6]) if len(r) > 6 else 0,
                             'pv': num(r[11]) if len(r) > 11 else 0, 'uv': num(r[12]) if len(r) > 12 else 0}
        break
tm = xlsx_sheets('/Users/lili/Downloads/天猫舒尔旗舰店日报反馈表(57).xlsx')
tm_rows = tm['日报表']
tm_aug = {'sales': 0.0, 'pv': 0, 'uv': 0, 'orders': 0}
for r in tm_rows:
    if len(r) > 2 and isinstance(r[1], str) and r[1].strip().isdigit() or (len(r) > 2 and re.match(r'^d+.0$', str(r[1]))):
        pass
F['tm_shure'] = {'note': '模板含8/1-8/16每日数据，8/17后待明早导出'}

json.dump(F, open(ROOT + '/fill_data.json', 'w'), ensure_ascii=False, indent=1)
print('saved fill_data.json')
print()
print('== 板块(分摊后) ==')
for k, v in F['plate'].items():
    print(' ', k, v['amount'], '万 毛利', v['profit'], '毛利率', v['margin'], '% 客单', v['avg_ticket'])
print('== 公司同比(API实付) ==', F['company_yoy'], '%')
print('== 板块同比 ==')
for k, v in F['yoy_plate'].items():
    print(' ', k, 'cur', v['cur'], 'last', v['last'], 'yoy', v['yoy'])
print('== 门店(分摊后) ==')
for k, v in F['apr_store'].items():
    print(' ', k, v['amount'], '万 毛利率', v['margin'], '% 客单', v['avg_ticket'], '同比', F['yoy_store'].get(k, {}).get('yoy'))
print('== APR 品类结构 ==', F['apr_struct'])
print('== APR 8/20-26 日销 ==', {k: v for k, v in F['apr_daily'].items() if k >= '2026-08-20'})
print('== 去年 8/20-26 ==', F['lastyear_trend'])
print('== 京东舒尔汇总 ==', F.get('jd_shure_sum'))
print('== 库龄360+ SKU ==', severe_count, ' TOP风险数', len(F['inv_risk_top']))
