import sys, json
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
    sheets = []
    for sheet in wb.findall('m:sheets/m:sheet', NS):
        name = sheet.get('name')
        rid = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        target = relmap.get(rid, '')
        rows = []
        try:
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
        except Exception as e:
            print('ERR sheet %s: %s' % (name, e), file=sys.stderr)
        sheets.append({'name': name, 'rows': rows})
    return sheets

def xl_date(v):
    if isinstance(v, (int, float)):
        return (EPOCH + timedelta(days=float(v))).strftime('%Y-%m-%d')
    return str(v)

print('== 天猫舒尔日报: 全部含日期行(序列, 日期, 销售金额, 转化率, 成交数, pv, uv, 跳失率) ==')
tm = load('/Users/lili/Downloads/天猫舒尔旗舰店日报反馈表(57).xlsx')[0]
for r in tm['rows']:
    if len(r) > 1 and isinstance(r[1], (int, float)):
        d = xl_date(r[1])
        if d >= '2026-07-20':
            print(' ', d, r[1], [r[i] for i in (2,3,4,10,11,12)])
print()
print('== 京东舒尔日报: 店铺销售 sheet 全部含日期行 ==')
jd = load('/Users/lili/Downloads/舒尔京东店铺日报-20260826.xlsx')
for sh in jd:
    if sh['name'] != '店铺销售':
        continue
    for r in sh['rows'][3:]:
        if len(r) > 1 and isinstance(r[1], (int, float)):
            d = xl_date(r[1])
            print(' ', d, r[1], [r[i] for i in (2,3,4,5,10,11,12,13)])
        elif len(r) > 2 and str(r[2]) == '汇总':
            print('  汇总:', [r[i] for i in range(21)])
print()
print('== 经营目标 电商 sheet 全部行 ==')
tgt = load('/Users/lili/Desktop/2026年销售预算指标-王新梦跟进.xlsx')
for sh in tgt:
    if sh['name'] != '电商':
        continue
    for i, r in enumerate(sh['rows']):
        if any(str(v).strip() for v in r):
            print(' row%d:' % i, [str(v)[:22] for v in r])
print()
print('== 经营目标 APR sheet 全部行 ==')
for sh in tgt:
    if sh['name'] != 'APR':
        continue
    for i, r in enumerate(sh['rows']):
        if any(str(v).strip() for v in r):
            print(' row%d:' % i, [str(v)[:20] for v in r])
