# -*- coding: utf-8 -*-
"""全面解析天猫日报：主块+底部块，找全部8月行"""
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
EPOCH = datetime(1899, 12, 30)
import os, glob

paths = [
  '/Users/lili/Desktop/销售/APR/202608/天猫舒尔旗舰店日报反馈表.xlsx',
]
# 也找所有可能的新版本
for p in glob.glob('/Users/lili/Desktop/**/天猫舒尔*.xlsx', recursive=True):
    if p not in paths: paths.append(p)

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

for path in paths:
    print('=====', path, os.path.getmtime(path) and '')
    import time
    print('  修改时间:', time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(path))))
    rows = load(path)
    print('  总行数:', len(rows))
    days = {}
    for i, r in enumerate(rows[2:], start=2):
        for dc, sc, oc, uc, pc in ((1, 2, 4, 11, 10), (0, 1, 3, 10, 9)):
            if len(r) > max(dc, sc, oc, uc, pc):
                d = ''
                try: d = (EPOCH + timedelta(days=float(r[dc]))).strftime('%Y-%m-%d')
                except Exception: pass
                if d.startswith('2026-08'):
                    days[d] = (float(r[sc]), float(r[oc]) if str(r[oc]).replace('.','').isdigit() else 0, float(r[uc]) if str(r[uc]).replace('.','').isdigit() else 0, r)
                    break
    print('  8月日期行数:', len(days))
    if days:
        ks = sorted(days)
        print('  范围:', ks[0], '~', ks[-1])
        missing = [d for d in ['2026-08-%02d' % x for x in range(1, 27)] if d not in days]
        print('  缺失:', missing if missing else '无（8/1-26 完整）')
        tot_s = sum(v[0] for v in days.values()); tot_u = sum(v[2] for v in days.values()); tot_o = sum(v[1] for v in days.values())
        print('  合计: 销售 %.2f 元 (%.2f万), uv %d, 单 %d, 转化 %.2f%%' % (tot_s, tot_s/10000, tot_u, tot_o, tot_o/tot_u*100 if tot_u else 0))
