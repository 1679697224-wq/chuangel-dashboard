# -*- coding: utf-8 -*-
"""解析 库存分析表_260826：总览(库龄分段) + 库龄明细 + 舒尔京东"""
import json, re
from collections import defaultdict
from zipfile import ZipFile
from xml.etree import ElementTree as ET

P = '/Users/lili/Desktop/deepseek harness/吉客云数据/库存分析表_260826.xlsx'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def load_sheets():
    z = ZipFile(P)
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

S = load_sheets()
print('sheets:', list(S.keys()))

# 1) 总览：找 库龄分段 行（分类=合计/苹果主机/原装配件...）
print('===== 总览 前 22 行 =====')
for r in S['总览'][:22]:
    print(' | '.join(x[:14] for x in r)[:260])

# 2) 库龄 sheet 表头 + 抽样 + 90天以上聚合
rows = S['库龄']
print()
print('===== 库龄 sheet 表头 =====')
print(rows[0])
print('表头长度:', len(rows[0]), '| 数据行:', len(rows)-1)
print('样例:', ' | '.join(rows[1])[:260])
