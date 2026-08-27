# -*- coding: utf-8 -*-
"""基于导出表聚合：销售单明细账(分摊后金额/毛利/付款时间) + 分仓库存查询(库存金额/剔虚拟)"""
import json, re, datetime
from collections import defaultdict
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT = "/Users/lili/Desktop/deepseek harness/吉客云数据"
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
EXCEL_EPOCH = datetime.datetime(1899, 12, 30)

def parse_xlsx(path):
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
    root = ET.fromstring(z.read(relmap.get(rid, '')))
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

def num(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def excel_date(v):
    try:
        f = float(v)
        if f > 20000:
            return (EXCEL_EPOCH + datetime.timedelta(days=f)).strftime('%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        pass
    return str(v or '')

def norm_shop(s):
    return re.sub(r'^\[[0-9]{3}\]', '', str(s)).strip().rstrip('*').strip()

# ---------- 销售 ----------
rows = parse_xlsx(ROOT + '/销售单明细账.xlsx')
header = rows[0]
print('销售表列:', ' | '.join(header))
print('数据行数:', len(rows) - 1)

sales_lines = []
for r in rows[1:]:
    if len(r) < 31:
        continue
    status = str(r[27] or '').strip()
    qty = num(r[8])
    if status not in ('已完成', '') or qty == 0:
        continue
    sales_lines.append({
        'channel': str(r[0] or '').strip(),
        'brand': str(r[1] or '').strip(),
        'order': str(r[2] or '').strip(),
        'goods_no': str(r[3] or '').strip(),
        'goods_name': str(r[4] or '').strip(),
        'qty': qty,
        'amount': num(r[9]),          # 分摊后金额
        'cost': num(r[10]),
        'profit': num(r[11]),         # 毛利
        'warehouse': str(r[12] or '').strip(),
        'pay_time': excel_date(r[25]) if len(r) > 25 else '',
        'order_time': excel_date(r[24]) if len(r) > 24 else '',
        'goods_class': str(r[30] or '').strip() if len(r) > 30 else '',
    })

json.dump(sales_lines, open(ROOT + '/sales_lines_export.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('有效明细行:', len(sales_lines))

# ---------- 库存 ----------
inv = parse_xlsx(ROOT + '/分仓库存查询.xlsx')
inv_header = inv[0]
print('库存表列:', ' | '.join(inv_header))
print('库存数据行:', len(inv) - 1)
VK = ('发票', '优惠券', '虚拟', '运费', '赠品')
inv_rows = []
removed = []
for r in inv[1:]:
    if len(r) < 16:
        continue
    name = str(r[1] or '').strip()
    if any(k in name for k in VK):
        removed.append(name)
        continue
    inv_rows.append({'goods_no': str(r[0] or '').strip(), 'name': name,
                     'qty': num(r[2]), 'cost': num(r[3]), 'amount': num(r[13]),
                     'wh': str(r[16] or '').strip()})
json.dump(inv_rows, open(ROOT + '/inventory_export.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('剔除虚拟商品数:', len(removed), '样例:', removed[:8])
print('保留库存行:', len(inv_rows))
