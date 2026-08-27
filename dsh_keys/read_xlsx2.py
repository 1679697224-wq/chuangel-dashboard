import zipfile, re, sys
from xml.etree import ElementTree as ET

def read_xlsx(path, max_rows=200):
    z = zipfile.ZipFile(path)
    NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    nsr = {'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
    relmap = {rel.get('Id'): ('xl/' + rel.get('Target') if not rel.get('Target').startswith('/') else rel.get('Target')[1:]) for rel in rels}
    ss = []
    try:
        sst = ET.fromstring(z.read('xl/sharedStrings.xml'))
        ss = [''.join(t.text or '' for t in si.findall('.//m:t', NS)) for si in sst.findall('m:si', NS)]
    except KeyError:
        pass
    for sheet in wb.findall('m:sheets/m:sheet', NS):
        name = sheet.get('name')
        rid = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        target = relmap.get(rid, '')
        print('===== SHEET:', name)
        if target not in z.namelist():
            print('  (missing)'); continue
        root = ET.fromstring(z.read(target))
        for row in root.findall('.//m:row', NS)[:max_rows]:
            cells = []
            for c in row.findall('m:c', NS):
                t = c.get('t')
                v = c.find('m:v', NS)
                isel = c.find('m:is', NS)
                if t == 's' and v is not None:
                    val = ss[int(v.text)]
                elif v is not None:
                    val = v.text
                elif isel is not None:
                    val = ''.join(x.text or '' for x in isel.findall('.//m:t', NS))
                else:
                    val = ''
                cells.append(str(val).strip())
            if any(cells):
                print(' | '.join(cells))

for p in sys.argv[1:]:
    print('##########', p)
    read_xlsx(p)
