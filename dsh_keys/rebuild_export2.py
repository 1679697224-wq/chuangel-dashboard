# -*- coding: utf-8 -*-
import json
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

z = ZipFile('/Users/lili/Desktop/deepseek harness/吉客云数据/销售单明细账.xlsx')
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

def num(x):
    try: return float(x)
    except: return 0.0
def xdate(v):
    try:
        return (datetime(1899, 12, 30) + timedelta(days=float(v))).strftime('%Y-%m-%d')
    except:
        return ''

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

for name, cond in [
    ('已完成+8月付款', lambda c: c.get('AB','')=='已完成' and '2026-08-01' <= xdate(c.get('Z','')) <= '2026-08-26'),
    ('已完成+8月付款+金额!=0', lambda c: c.get('AB','')=='已完成' and '2026-08-01' <= xdate(c.get('Z','')) <= '2026-08-26' and num(c.get('J','')) != 0),
]:
    tot = 0.0; lines = 0; orders = set()
    for c in rows[1:]:
        if cond(c):
            tot += num(c.get('J', 0)); lines += 1; orders.add(c.get('C', ''))
    print('%s: 行 %d, 单 %d, 总额 %.2f' % (name, lines, len(orders), tot))
