# -*- coding: utf-8 -*-
"""天猫日报：看底部汇总行 + 与旧版 diff"""
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
EPOCH = datetime(1899, 12, 30)

def load(path):
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
    return rows

new_rows = load('/Users/lili/Desktop/销售/APR/202608/天猫舒尔旗舰店日报反馈表.xlsx')
old_rows = load('/Users/lili/Downloads/天猫舒尔旗舰店日报反馈表(57).xlsx')
print('新行数:', len(new_rows), ' 旧行数:', len(old_rows))
# 逐行 diff（前14列）
diffs = []
for i in range(max(len(new_rows), len(old_rows))):
    nr = new_rows[i] if i < len(new_rows) else []
    or_ = old_rows[i] if i < len(old_rows) else []
    if nr[:14] != or_[:14]:
        diffs.append(i)
print('发生变化的行号:', diffs[:20])
for i in diffs[:12]:
    print('row%d 新:' % i, [str(x)[:14] for x in new_rows[i][:14]] if i < len(new_rows) else 'NEW?')
    print('     旧:' , [str(x)[:14] for x in old_rows[i][:14]] if i < len(old_rows) else 'OLD?')
