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
    sheets = {}
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
                elif v is not None:
                    val = v.text
                    try: val = float(val)
                    except: pass
                elif isel is not None: val = ''.join(x.text or '' for x in isel.findall('.//m:t', NS))
                else: val = ''
                cells.append(val)
            rows.append(cells)
        sheets[name] = rows
    return sheets

s = load('/Users/lili/Desktop/deepseek harness/吉客云数据/库存分析表_260826.xlsx')

print('===== 总览 全部行 =====')
for i, r in enumerate(s['总览']):
    if any(str(v).strip() for v in r):
        vals = [str(v)[:20] for v in r]
        print('row%d:' % i, vals)

print()
print('===== 库龄 前6行 =====')
for i, r in enumerate(s['库龄'][:6]):
    print('row%d:' % i, [str(v)[:24] for v in r])
