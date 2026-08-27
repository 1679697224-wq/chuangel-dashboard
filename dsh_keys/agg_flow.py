# -*- coding: utf-8 -*-
"""聚合 APR 客流：进店客流按店汇总(8/1-26)，转化率=单数/进店客流"""
import json
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from collections import defaultdict
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

z = ZipFile('/Users/lili/Downloads/数据预览-3.xlsx')
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

def f(x):
    try: return float(x)
    except Exception: return 0.0

flow = defaultdict(lambda: {'in': 0.0, 'days': set(), 'last': ''})
for row in root.findall('.//m:row', NS):
    cells = []
    for c in row.findall('m:c', NS):
        t = c.get('t'); v = c.find('m:v', NS); isel = c.find('m:is', NS)
        if t == 's' and v is not None: val = ss[int(v.text)]
        elif v is not None: val = v.text
        elif isel is not None: val = ''.join(x.text or '' for x in isel.findall('.//m:t', NS))
        else: val = ''
        cells.append(val)
    if len(cells) >= 3 and cells[0].startswith('2026-08'):
        d = cells[0]
        place = cells[1]
        vin = cells[2]
        if vin == '--' or vin == '': continue
        flow[place]['in'] += f(vin)
        flow[place]['days'].add(d)
        if d > flow[place]['last']: flow[place]['last'] = d

# 8/1-26 口径
flow26 = defaultdict(float)
for row in root.findall('.//m:row', NS):
    cells = []
    for c in row.findall('m:c', NS):
        t = c.get('t'); v = c.find('m:v', NS)
        if t == 's' and v is not None: val = ss[int(v.text)]
        elif v is not None: val = v.text
        else: val = ''
        cells.append(val)
    if len(cells) >= 3 and cells[0].startswith('2026-08') and cells[0] <= '2026-08-26':
        if cells[2] not in ('--', ''):
            flow26[cells[1]] += f(cells[2])

# 场所 -> 看板门店名
STORE_MAP = {
    '安徽宿州苏宁广场店': '宿州店',
    '江苏镇江Chuangel镇江': '镇江店',
    '江苏镇江Chuangel镇江店': '镇江店',
    '江苏徐州彭城苏宁广场店': '徐州彭城店',
    '江苏无锡Chuangel无锡苏宁广场店': '无锡店',
    '江苏连云港苏宁广场店': '连云港店',
    '山东日照苏宁广场店': '日照店',
    '江苏徐州复兴苏宁广场店': '徐州宝龙店',
    '山西运城苏宁广场店': '运城店',
    '山西太原富力广场店': '太原店',
    '辽宁沈阳苏家屯苏宁广场店': '苏家屯店',
}

# 订单数（fill_data.json 的 apr_store）
fd = json.load(open('/Users/lili/Desktop/deepseek harness/吉客云数据/fill_data.json', encoding='utf-8'))
orders = {k: v['orders'] for k, v in fd['apr_store'].items()}

print('== 场所名称（原始）==')
for k in flow.keys(): print(' ', repr(k), '| 天数', len(flow[k]['days']), '| 最后', flow[k]['last'], '| 全月进店', int(flow[k]['in']))

print()
print('== 按门店（8/1-26 进店客流）==')
total26 = 0
for raw, store in STORE_MAP.items():
    if raw in flow26:
        v = flow26[raw]
        total26 += v
        print('  %s: 进店客流 %d 人次 | 全月(至8/27) %d | 单数 %d | 转化率(单/进店) %.2f%%' % (
            store, int(v), int(flow.get(raw, {}).get('in', 0)), orders.get(store, 0),
            orders.get(store, 0) / v * 100 if v else 0))
print('  10店合计(8/1-26):', int(total26))
print('  APR_TOTAL 转化率(全单/总客流): %.2f%%' % (sum(orders.get(store, 0) for store in STORE_MAP.values()) / total26 * 100 if total26 else 0))
print('  全月(至8/27) 合计:', int(sum(v['in'] for v in flow.values())))
