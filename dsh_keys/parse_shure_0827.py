# -*- coding: utf-8 -*-
"""解析 8/27 早上的天猫舒尔日报 + 京东舒尔日报"""
import re
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

def num(x):
    try: return float(x)
    except: return 0.0
def xdate(v):
    try: return (EPOCH + timedelta(days=float(v))).strftime('%Y-%m-%d')
    except: return str(v)

print('========== 天猫舒尔旗舰店日报反馈表（新） ==========')
tm = load('/Users/lili/Desktop/销售/APR/202608/天猫舒尔旗舰店日报反馈表.xlsx')[0]
rows = tm['rows']
print('总行数:', len(rows))
# 找8月日期行
aug = []
for r in rows:
    if len(r) > 1 and isinstance(r[1], (int, float)):
        d = xdate(r[1])
        if d.startswith('2026-08'):
            aug.append((d, r))
print('8月日期行数:', len(aug), ' 范围:', aug[0][0] if aug else '-', '~', aug[-1][0] if aug else '-')
tot = {'sales': 0.0, 'orders': 0, 'pv': 0, 'uv': 0}
for d, r in aug:
    tot['sales'] += num(r[2]); tot['orders'] += num(r[4]); tot['pv'] += num(r[10]); tot['uv'] += num(r[11])
print('8月合计: 销售 %.2f 元 (%.2f 万), 成交 %d 单, pv %d, uv %d, 转化率 %.2f%%' % (
    tot['sales'], tot['sales']/10000, tot['orders'], tot['pv'], tot['uv'], tot['orders']/tot['uv']*100 if tot['uv'] else 0))
print('最后3天:', [(d, r[2], r[3], r[4], r[10], r[11]) for d, r in aug[-3:]])

print()
print('========== 舒尔京东店铺日报-20260827 ==========')
jd = load('/Users/lili/Desktop/销售/APR/202608/舒尔京东店铺日报-20260827.xlsx')
for sh in jd:
    print('-- sheet %s 行数 %d' % (sh['name'], len(sh['rows'])))
    for r in sh['rows'][:4]:
        print('  ', [str(x)[:20] for x in r[:14]])
    # 汇总行
    for r in sh['rows']:
        hit = [i for i, x in enumerate(r) if str(x).strip() == '汇总']
        if hit:
            v = r[hit[0]+1:]
            print('  汇总:', [str(x)[:16] for x in v[:14]])
            break
    # 最近3个日期行
    cnt = 0
    for r in sh['rows'][3:]:
        if len(r) > 1 and isinstance(r[1], (int, float)):
            d = xdate(r[1])
            if d >= '2026-08-24':
                print('  ', d, [r[i] for i in (2,3,4,5,10,11,12)])
                cnt += 1
        if cnt >= 4: break
