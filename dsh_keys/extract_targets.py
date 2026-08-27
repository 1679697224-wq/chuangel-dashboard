import json
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
                elif v is not None:
                    val = v.text
                    try: val = float(val)
                    except: pass
                elif isel is not None: val = ''.join(x.text or '' for x in isel.findall('.//m:t', NS))
                else: val = ''
                cells.append(val)
            rows.append(cells)
        sheets.append({'name': name, 'rows': rows})
    return sheets

tgt = load('/Users/lili/Desktop/2026年销售预算指标-王新梦跟进.xlsx')
out = {}

# ---- 电商 sheet: 月份 x 店铺, 销售额含税(万) ----
ec = [sh for sh in tgt if sh['name'] == '电商'][0]
stores = {}
for r in ec['rows']:
    if len(r) >= 2 and str(r[0]).strip() and str(r[1]).strip():
        month = str(r[0]).strip()
        store = str(r[1]).strip()
        if store == '合计':
            continue
        stores.setdefault(store, {})
        def f(v):
            try: return round(float(v), 2)
            except: return None
        stores[store][month] = {'sales_tax_wan': f(r[2]), 'revenue_wan': f(r[3]), 'cost_wan': f(r[4]), 'gross_wan': f(r[5]), 'gross_rate': f(r[6])}
out['ecom'] = stores
print('电商 sheet 店铺数:', len(stores))
print('店铺列表:', list(stores.keys()))
print()
print('各店 8月目标(万):')
for s, m in stores.items():
    if '8月' in m:
        print('  %s: 销售含税 %s 万, 毛利率 %s' % (s, m['8月']['sales_tax_wan'], m['8月']['gross_rate']))

# ---- APR sheet ----
ap = [sh for sh in tgt if sh['name'] == 'APR'][0]
apr_rows = []
for i, r in enumerate(ap['rows']):
    if i < 3:
        continue
    if any(str(v).strip() for v in r[:14]):
        apr_rows.append([str(v)[:24] for v in r[:14]])
out['apr_raw'] = apr_rows
print()
print('APR sheet 数据行数:', len(apr_rows))
for r in apr_rows:
    print(' ', r)
json.dump(out, open('/Users/lili/Desktop/deepseek harness/吉客云数据/targets_2026.json', 'w'), ensure_ascii=False, indent=1)
print()
print('saved 吉客云数据/targets_2026.json')
