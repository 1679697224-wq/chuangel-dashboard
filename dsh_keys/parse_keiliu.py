# -*- coding: utf-8 -*-
"""解析数据预览-3.xlsx（APR 客流数据）"""
from zipfile import ZipFile
from xml.etree import ElementTree as ET
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

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
    sheets = []
    for sheet in wb.findall('m:sheets/m:sheet', NS):
        name = sheet.get('name')
        rid = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        target = relmap.get(rid, '')
        rows = []
        root = ET.fromstring(z.read(target))
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
        sheets.append({'name': name, 'rows': rows})
    return sheets

for path in ['/Users/lili/Downloads/数据预览-3.xlsx', '/Users/lili/Downloads/数据预览-2.xlsx']:
    print('==========', path)
    try:
        for sh in load(path):
            print('-- sheet:', sh['name'], '行数', len(sh['rows']))
            for i, r in enumerate(sh['rows'][:25]):
                vals = [str(x)[:22] for x in r[:12]]
                if any(v.strip() for v in vals):
                    print('  row%d:' % i, vals)
    except Exception as e:
        print('ERR', e)
