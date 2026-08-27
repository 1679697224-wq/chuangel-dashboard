import sys
from zipfile import ZipFile
from xml.etree import ElementTree as ET
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def inspect(path, maxrows=8):
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
    print('== sheets ==')
    for sheet in wb.findall('m:sheets/m:sheet', NS):
        name = sheet.get('name')
        rid = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        target = relmap.get(rid, '')
        try:
            root = ET.fromstring(z.read(target))
            rows = root.findall('.//m:row', NS)
            print(f'  [{name}] 行数(含表头): {len(rows)}')
        except Exception as e:
            print(f'  [{name}] ERR {e}')
    # 打印第一个 sheet 前几行
    sheet0 = wb.find('m:sheets/m:sheet', NS)
    rid0 = sheet0.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
    target0 = relmap.get(rid0, '')
    root0 = ET.fromstring(z.read(target0))
    print('== 第一个 sheet 前', maxrows, '行 ==')
    for row in root0.findall('.//m:row', NS)[:maxrows]:
        cells = []
        for c in row.findall('m:c', NS):
            t = c.get('t'); v = c.find('m:v', NS); isel = c.find('m:is', NS)
            if t == 's' and v is not None: val = ss[int(v.text)]
            elif v is not None: val = v.text
            elif isel is not None: val = ''.join(x.text or '' for x in isel.findall('.//m:t', NS))
            else: val = ''
            cells.append(str(val).strip())
        if any(cells):
            print(' | '.join(cells)[:400])
for p in sys.argv[1:]:
    print('##########', p)
    inspect(p)
