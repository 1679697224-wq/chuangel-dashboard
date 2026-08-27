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

print('========== 天猫舒尔旗舰店日报反馈表(57) ==========')
tianmao = load('/Users/lili/Downloads/天猫舒尔旗舰店日报反馈表(57).xlsx')[0]
rows = tianmao['rows']
print('总行数:', len(rows))
for i, r in enumerate(rows[:3]):
    print('--- row%d ---' % i)
    for ci, v in enumerate(r):
        if str(v).strip():
            print('  col%d: %s' % (ci, v))
aug = []
for r in rows:
    if len(r) > 1 and isinstance(r[1], (int, float)):
        d = xl_date(r[1])
        if d.startswith('2026-08'):
            aug.append((d, r))
print('8月日期行数:', len(aug))
if aug:
    print('8月首行样例(列索引: 值):')
    for ci, v in enumerate(aug[0][1]):
        if str(v).strip():
            print('  col%d: %s' % (ci, v))
def num(v):
    try: return float(v)
    except: return 0.0
tot = {}
for d, r in aug:
    for ci in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
        tot[ci] = tot.get(ci, 0.0) + num(r[ci])
print('8月关键列合计:', {k: round(v, 2) for k, v in tot.items()})
print('8月每日明细(日期, 销售金额, 转化率, 成交数, 客单价, 加购, 退款, 实际成交, 关注, pv, uv, 跳失率):')
for d, r in aug[-5:]:
    print(' ', d, [r[ci] for ci in (1,2,3,4,5,6,7,8,9,10,11,12)])

print()
print('========== 舒尔京东店铺日报-20260826 ==========')
jd = load('/Users/lili/Downloads/舒尔京东店铺日报-20260826.xlsx')
for sh in jd:
    print('-- sheet %s 行数 %d' % (sh['name'], len(sh['rows'])))
    for label, rr in (('row0', sh['rows'][0]), ('row1', sh['rows'][1] if len(sh['rows']) > 1 else []), ('row2', sh['rows'][2] if len(sh['rows']) > 2 else [])):
        print(label)
        for ci, v in enumerate(rr):
            if str(v).strip():
                print('  col%d: %s' % (ci, v))
    if sh['name'] == '店铺销售':
        for r in sh['rows']:
            if len(r) > 2 and str(r[2]) == '汇总':
                print('汇总行:', [str(v)[:22] for v in r[:22]])
                break

print()
print('========== 2026年销售预算指标-王新梦跟进 ==========')
tgt = load('/Users/lili/Desktop/2026年销售预算指标-王新梦跟进.xlsx')
for sh in tgt:
    print('-- sheet %s 行数 %d' % (sh['name'], len(sh['rows'])))
    for i, r in enumerate(sh['rows'][:4]):
        print('  row%d: %s' % (i, [str(v)[:26] for v in r]))
