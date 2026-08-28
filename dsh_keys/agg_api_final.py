# -*- coding: utf-8 -*-
"""最终 API 聚合：销售(实付 8/1-27, payTime?:consignTime) + 同比 + 客流4 + 舒尔828"""
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

# ===== 销售：API 实付 8/1-27（日期=payTime ?: consignTime）=====
trades = json.load(open(ROOT + '/sales_raw_20260828.json', encoding='utf-8'))
plate = defaultdict(lambda: {'amount': 0.0, 'orders': 0})
platform = defaultdict(lambda: {'amount': 0.0, 'orders': 0})
aprst = defaultdict(lambda: {'amount': 0.0, 'orders': 0, 'on': 0.0, 'off': 0.0})
daily = defaultdict(float)
person = defaultdict(lambda: {'amount': 0.0, 'orders': 0, 'on': 0.0, 'off': 0.0, 'store': ''})
for o in trades:
    pt = o.get('payTime') or ''
    ct = o.get('consignTime') or ''
    d = (pt or ct)[:10]
    if not (d.startswith('2026-08') and d[8:10] <= '27'): continue
    amt = num(o.get('payment', 0))
    p, pf, st = classify(o.get('shopName', ''))
    plate[p]['amount'] += amt; plate[p]['orders'] += 1
    platform[pf]['amount'] += amt; platform[pf]['orders'] += 1
    daily[d] += amt
    if p == 'APR':
        aprst[st]['amount'] += amt; aprst[st]['orders'] += 1
        if pf == 'APR-线上': aprst[st]['on'] += amt
        else: aprst[st]['off'] += amt
    sp = re.sub(r'\\(.*\\)', '', o.get('seller', '') or '').strip()
    if sp:
        person[sp]['amount'] += amt; person[sp]['orders'] += 1
        person[sp]['store'] = st or p
        if p == 'APR':
            if pf == 'APR-线上': person[sp]['on'] += amt
            else: person[sp]['off'] += amt

F = {'sales': {'plate': dict(plate), 'platform': dict(platform), 'apr_store': dict(aprst),
               'daily': dict(sorted(daily.items())),
               'person': dict(sorted(person.items(), key=lambda x: -x[1]['amount']))}}
print('== 板块(API实付 8/1-27) ==')
for k, v in sorted(plate.items(), key=lambda x: -x[1]['amount']):
    print(' ', k, round(v['amount']/10000, 2), '万', v['orders'], '单')
print('== 门店 ==')
for k, v in sorted(aprst.items(), key=lambda x: -x[1]['amount']):
    print(' ', k, round(v['amount']/10000, 2), '万', v['orders'], '单')
print('== 平台 ==')
for k, v in sorted(platform.items(), key=lambda x: -x[1]['amount']):
    print(' ', k, round(v['amount']/10000, 2), '万')
print('== 销售员TOP8 ==')
for k, v in list(F['sales']['person'].items())[:8]:
    print(' ', k, round(v['amount']/10000, 2), '万', v['orders'], '单')
print('== 8/27 日销 ==', round(F['sales']['daily'].get('2026-08-27', 0)/10000, 2), '万')

# ===== 同比 2025（tradeNo 日期 8/1-27）=====
t25 = json.load(open(ROOT + '/sales_raw_202508.json', encoding='utf-8'))
tot25 = 0
for o in t25:
    tno = str(o.get('tradeNo', ''))
    d = tno[2:10] if len(tno) >= 10 else ''
    if re.match(r'^\d{8}$', d) and d.startswith('202508') and d[6:8] <= '27':
        tot25 += num(o.get('payment', 0))
cur_tot = sum(v['amount'] for v in plate.values())
print('== 同比 ==', '2025(8/1-27):', round(tot25/10000, 2), '万 | 2026:', round(cur_tot/10000, 2), '万 | 同比:', round((cur_tot-tot25)/tot25*100, 1) if tot25 else None, '%')
F['yoy'] = {'cur': cur_tot, 'last': tot25, 'yoy': round((cur_tot-tot25)/tot25*100, 1) if tot25 else None}

# ===== 客流4（8/1-27 进店客流）=====
z = ZipFile('/Users/lili/Downloads/数据预览-4.xlsx')
wb = ET.fromstring(z.read('xl/workbook.xml'))
rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
relmap = {rel.get('Id'): ('xl/' + rel.get('Target') if not rel.get('Target').startswith('/') else rel.get('Target')[1:]) for rel in rels}
ss = []
sst = ET.fromstring(z.read('xl/sharedStrings.xml'))
ss = [''.join(t.text or '' for t in si.findall('.//m:t', NS)) for si in sst.findall('m:si', NS)]
sheet = wb.find('m:sheets/m:sheet', NS)
rid = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
root = ET.fromstring(z.read(relmap.get(rid, '')))
RULE = [('宿州', '宿州店'), ('彭城', '徐州彭城店'), ('无锡', '无锡店'), ('连云港', '连云港店'), ('日照', '日照店'),
        ('复兴', '徐州宝龙店'), ('运城', '运城店'), ('太原', '太原店'), ('苏家屯', '苏家屯店'), ('镇江', '镇江店')]
def match(name):
    for k, v in RULE:
        if k in name: return v
    return None
flow = defaultdict(float)
for row in root.findall('.//m:row', NS):
    cells = []
    for c in row.findall('m:c', NS):
        t = c.get('t'); v = c.find('m:v', NS)
        if t == 's' and v is not None: val = ss[int(v.text)]
        elif v is not None: val = v.text
        else: val = ''
        cells.append(val)
    if len(cells) >= 3 and cells[0].startswith('2026-08') and cells[0] <= '2026-08-27':
        if cells[2] in ('--', ''): continue
        st = match(cells[1])
        if st: flow[st] += num(cells[2])
F['flow'] = {k: int(v) for k, v in flow.items()}
print('== 客流(8/1-27 进店) ==', dict(F['flow']), '合计', sum(F['flow'].values()))

# ===== 舒尔：京东日报828 + 天猫日报59 =====
jd = xlsx_sheets('/Users/lili/Desktop/销售/舒尔/202608/舒尔京东店铺日报-20260828.xlsx')
for r in jd['店铺销售']:
    hit = [i for i, x in enumerate(r) if str(x).strip() == '汇总']
    if hit:
        v = r[hit[0]+1:]
        if len(v) > 9:
            F['jd_shure'] = {'sales': round(num(v[0]), 2), 'conv': round(num(v[1])*100, 2), 'orders': int(num(v[2])),
                             'aov': round(num(v[3]), 2), 'pv': int(num(v[8])), 'uv': int(num(v[9]))}
        break
tm = xlsx_sheets('/Users/lili/Desktop/销售/舒尔/202608/天猫舒尔旗舰店日报反馈表(59).xlsx')
tm_days = {}
for r in tm['日报表'][2:]:
    for dc, sc, oc, uc in ((1, 2, 4, 11), (0, 1, 3, 10)):
        if len(r) <= max(dc, sc, oc, uc): continue
        dd = ''
        try: dd = (EPOCH + timedelta(days=float(r[dc]))).strftime('%Y-%m-%d')
        except Exception: continue
        if dd.startswith('2026-08') and dd <= '2026-08-27' and str(r[sc]).strip() not in ('', '#DIV/0!'):
            tm_days[dd] = (num(r[sc]), num(r[oc]), num(r[uc]))
            break
tm_tot = {'sales': sum(v[0] for v in tm_days.values()), 'orders': sum(v[1] for v in tm_days.values()), 'uv': sum(v[2] for v in tm_days.values())}
F['tm_shure'] = {k: round(v, 2) for k, v in tm_tot.items()}
print('== 京东舒尔 ==', F.get('jd_shure'))
print('== 天猫日报(8/1-27) ==', F['tm_shure'], '转化', round(tm_tot['orders']/tm_tot['uv']*100, 2) if tm_tot['uv'] else 0)

json.dump(F, open(ROOT + '/api_fill_828.json', 'w'), ensure_ascii=False, indent=1)
print('saved api_fill_828.json')
