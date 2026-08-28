# -*- coding: utf-8 -*-
"""检查新文件结构与日期范围"""
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
                elif v is not None: val = v.text
                elif isel is not None: val = ''.join(x.text or '' for x in isel.findall('.//m:t', NS))
                else: val = ''
                cells.append(val)
            rows.append(cells)
        sheets.append({'name': name, 'rows': rows})
    return sheets

print('========== 数据预览-4.xlsx（客流） ==========')
s = load('/Users/lili/Downloads/数据预览-4.xlsx')
for sh in s:
    print('sheet:', sh['name'], '行数', len(sh['rows']))
    print('  前3行:', [str(x)[:18] for x in sh['rows'][0][:6]])
    # 日期范围
    dates = set()
    for r in sh['rows'][1:]:
        if r and str(r[0]).startswith('2026-08'):
            dates.add(str(r[0]))
    if dates:
        ds = sorted(dates)
        print('  日期范围:', ds[0], '~', ds[-1], '共', len(ds), '天')
        print('  场所数:', len(set(r[1] for r in sh['rows'][1:] if r and len(r) > 1 and str(r[0]).startswith('2026-08'))))
    break

print()
print('========== 销售单明细账828.xlsx ==========')
s = load('/Users/lili/Downloads/销售单明细账828.xlsx')
for sh in s[:1]:
    print('sheet:', sh['name'], '行数', len(sh['rows']))
    hdr = sh['rows'][0]
    print('  表头:', [str(x)[:10] for x in hdr[:31]])
    # 付款时间范围（Z列=25）
    paydates = set()
    from datetime import datetime as dt2, timedelta as td2
    for r in sh['rows'][1:]:
        if len(r) > 25 and r[25]:
            try:
                d = (EPOCH + timedelta(days=float(r[25]))).strftime('%Y-%m-%d')
                if d.startswith('2026-08'): paydates.add(d)
            except Exception: pass
    if paydates:
        pd = sorted(paydates)
        print('  付款日期:', pd[0], '~', pd[-1], '共', len(pd), '天')
    # 订单状态分布
    from collections import Counter
    st = Counter(str(r[27]) for r in sh['rows'][1:] if len(r) > 27)
    print('  状态:', dict(st.most_common(5)))

print()
print('========== 舒尔京东店铺日报-20260828 ==========')
s = load('/Users/lili/Desktop/销售/舒尔/202608/舒尔京东店铺日报-20260828.xlsx')
for sh in s[:1]:
    print('sheet:', sh['name'], '行数', len(sh['rows']))
    for r in sh['rows'][:4]:
        print('  ', [str(x)[:18] for x in r[:13]])
    for r in sh['rows']:
        hit = [i for i, x in enumerate(r) if str(x).strip() == '汇总']
        if hit:
            v = r[hit[0]+1:]
            print('  汇总:', [str(x)[:16] for x in v[:12]])
            break

print()
print('========== 天猫舒尔旗舰店日报反馈表(59) ==========')
s = load('/Users/lili/Desktop/销售/舒尔/202608/天猫舒尔旗舰店日报反馈表(59).xlsx')
for sh in s[:1]:
    print('sheet:', sh['name'], '行数', len(sh['rows']))
    days = {}
    for r in sh['rows'][2:]:
        for dc, sc in ((1, 2), (0, 1)):
            if len(r) > dc and str(r[dc]).strip():
                d = ''
                try: d = (EPOCH + timedelta(days=float(r[dc]))).strftime('%Y-%m-%d')
                except Exception: continue
                if d.startswith('2026-08') and str(r[sc]).strip() not in ('', '#DIV/0!'):
                    days[d] = (r[sc], r[4] if len(r) > 4 else '', r[11] if len(r) > 11 else '', r[10] if len(r) > 10 else '')
                    break
    if days:
        ks = sorted(days)
        print('  8月日期:', ks[0], '~', ks[-1], '共', len(ks), '天')
        print('  最后几天:', {d: days[d][0] for d in ks[-3:]})
