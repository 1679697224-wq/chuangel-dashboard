# -*- coding: utf-8 -*-
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
root = ET.fromstring(z.read(relmap.get(rid, '')))
def f(x):
    try: return float(x)
    except Exception: return 0.0
# 子串 -> 门店
RULE = [('宿州','宿州店'),('彭城','徐州彭城店'),('无锡','无锡店'),('连云港','连云港店'),('日照','日照店'),('复兴','徐州宝龙店'),('运城','运城店'),('太原','太原店'),('苏家屯','苏家屯店'),('镇江','镇江店')]
def match(name):
    for k, v in RULE:
        if k in name: return v
    return None
flow = defaultdict(float); days = defaultdict(set); last = {}
for row in root.findall('.//m:row', NS):
    cells = []
    for c in row.findall('m:c', NS):
        t = c.get('t'); v = c.find('m:v', NS)
        if t == 's' and v is not None: val = ss[int(v.text)]
        elif v is not None: val = v.text
        else: val = ''
        cells.append(val)
    if len(cells) >= 3 and cells[0].startswith('2026-08') and cells[0] <= '2026-08-26':
        if cells[2] in ('--', ''): continue
        st = match(cells[1])
        if st:
            flow[st] += f(cells[2]); days[st].add(cells[0])
fd = json.load(open('/Users/lili/Desktop/deepseek harness/吉客云数据/fill_data.json', encoding='utf-8'))
orders = {k: v['orders'] for k, v in fd['apr_store'].items()}
print('== 8/1-26 进店客流（按门店）==')
tot = 0; tot_o = 0
for st in ['徐州彭城店','无锡店','连云港店','太原店','宿州店','镇江店','运城店','日照店','徐州宝龙店','苏家屯店']:
    v = flow.get(st, 0); o = orders.get(st, 0)
    tot += v; tot_o += o
    conv = o / v * 100 if v else 0
    print('  %s: 进店 %d 天%d | 单 %d | 转化 %.2f%%' % (st, int(v), len(days.get(st, set())), o, conv))
print('  合计进店: %d | 总单: %d | 整体转化率: %.2f%%' % (int(tot), tot_o, tot_o / tot * 100 if tot else 0))
json.dump({'flow': {k: int(v) for k, v in flow.items()}, 'total': int(tot), 'orders': orders}, open('/Users/lili/Desktop/deepseek harness/吉客云数据/apr_flow.json', 'w'), ensure_ascii=False, indent=1)
print('saved apr_flow.json')