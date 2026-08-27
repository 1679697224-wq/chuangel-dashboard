# -*- coding: utf-8 -*-
"""深挖天猫舒尔日报：找8/17以后的数据"""
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
EPOCH = datetime(1899, 12, 30)

z = ZipFile('/Users/lili/Desktop/销售/APR/202608/天猫舒尔旗舰店日报反馈表.xlsx')
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
rows = []
for row in root.findall('.//m:row', NS):
    cells = []
    for c in row.findall('m:c', NS):
        t = c.get('t'); v = c.find('m:v', NS); isel = c.find('m:is', NS)
        if t == 's' and v is not None: val = ss[int(v.text)]
        elif v is not None: val = v.text
        elif isel is not None: val = ''.join(x.text or '' for x in isel.findall('.//m:t', NS))
        else: val = ''
        cells.append(val)
    rows.append(cells)
print('总行数:', len(rows))
# 打印 row 10-30（8/16 附近）
for i, r in enumerate(rows[10:30], start=10):
    vals = [str(x)[:14] for x in r[:14]]
    print('row%d:' % i, vals)
print()
# 找所有可能是8/17+的行：B列序列>=46251(8/17) 或 字符串含2026-08-1[7-9]
found = 0
for i, r in enumerate(rows[3:], start=3):
    b = str(r[1]) if len(r) > 1 else ''
    d = ''
    if b:
        try:
            d = (EPOCH + timedelta(days=float(b))).strftime('%Y-%m-%d')
        except Exception:
            d = b
    if d >= '2026-08-17' and d <= '2026-08-27':
        print('AUG17+ row%d: %s | %s' % (i, d, [str(x)[:12] for x in r[:12]]))
        found += 1
print('8/17+ 行数:', found)
