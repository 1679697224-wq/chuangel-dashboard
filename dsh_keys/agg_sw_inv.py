# -*- coding: utf-8 -*-
"""聚合商务库存分析表：库龄90天+ 按渠道/品类；舒尔京东表"""
import json
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
def num(v):
    try: return float(str(v).replace(',', ''))
    except (TypeError, ValueError): return 0.0

# 库龄 sheet 列: 0仓库 25渠道分类 26产品分类 27仓位分类 ... 11库存数量 12库存金额 19 90~180金额 22 180~360金额 25? 360天以上金额
# 表头: ['仓库','货品编号','货品名称','规格','单位','条码','品牌','分类','固定成本价','成本价','库龄(天)','库存数量','库存金额','0~30数量','0~30金额','30~60数量','30~60金额','60~90数量','60~90金额','90~180数量','90~180金额','180~360数量','180~360金额','360以上数量','360以上金额','渠道分类','产品分类','仓位分类',...]
rows = S['库龄'][1:]
agg = defaultdict(lambda: {'amount': 0.0, 'qty': 0.0, 'over90_amount': 0.0, 'over90_qty': 0.0})
for r in rows:
    if len(r) < 27:
        continue
    ch = r[25] or '未分类'
    prod = r[26] or ''
    amt = num(r[12]); qty = num(r[11])
    o90a = num(r[20]) + num(r[22]) + num(r[24])
    o90q = num(r[19]) + num(r[21]) + num(r[23])
    agg[ch]['amount'] += amt; agg[ch]['qty'] += qty
    agg[ch]['over90_amount'] += o90a; agg[ch]['over90_qty'] += o90q

print('===== 库龄按渠道分类（金额万）=====')
for k, v in sorted(agg.items(), key=lambda x: -x[1]['amount']):
    print(f"  {k:<14} 库存 {round(v['amount'],2):>10} | 90天以上 {round(v['over90_amount'],2):>10} ({round(v['over90_amount']/v['amount']*100,1) if v['amount'] else 0}%)")

total = sum(v['amount'] for v in agg.values())
o90 = sum(v['over90_amount'] for v in agg.values())
print(f"合计: 库存 {round(total,2)} | 90天以上 {round(o90,2)} ({round(o90/total*100,1)}%)")

# 舒尔京东 sheet
sj = S.get('舒尔京东', [])
print()
print('===== 舒尔京东 sheet 行数:', len(sj), '=====')
if sj:
    print('表头:', ' | '.join(sj[0])[:300])
    print('样例:', ' | '.join(sj[1])[:300])

# 总览：分类库龄（合计行）
print()
print('===== 总览·分类库龄分段（从第5行起）=====')
for r in S['总览'][4:10]:
    print(' | '.join(x[:16] for x in r)[:300])
