# -*- coding: utf-8 -*-
"""京东日报 8/24-8/27 每日行确认"""
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
EPOCH = datetime(1899, 12, 30)
z = ZipFile('/Users/lili/Desktop/销售/APR/202608/舒尔京东店铺日报-20260827.xlsx')
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
rows = []
for row in root.findall('.//m:row', NS):
    cells = []
    for c in row.findall('m:c', NS):
        t = c.get('t'); v = c.find('m:v', NS); isel = c.find('m:is', NS)
        if t == 's' and v is not None: val = ss[int(v.text)]
        elif v is not None:
            val = v.text
            try: val = float(val)
            except: pass
        elif isel is not None: val = ''.join(x.text or '' for x in isel.findall('.//m:t', NS))
        else: val = ''
        cells.append(val)
    rows.append(cells)
print('京东日报 8/24-8/27 每日(日期, 销售, 转化, 单, 客单, pv, uv):')
for r in rows[3:]:
    if len(r) > 1 and isinstance(r[1], (int, float)):
        d = (EPOCH + timedelta(days=float(r[1]))).strftime('%Y-%m-%d')
        if '2026-08-24' <= d <= '2026-08-27':
            print(' ', d, [r[i] for i in (2,3,4,5,10,11)])
