# -*- coding: utf-8 -*-
"""按订单状态检查各渠道销售额，验证电商是否被'已完成'过滤低估"""
import re
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta
from collections import defaultdict
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

z = ZipFile('/Users/lili/Desktop/deepseek harness/吉客云数据/销售单明细账.xlsx')
wb = ET.fromstring(z.read('xl/workbook.xml'))
rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
relmap = {rel.get('Id'): ('xl/' + rel.get('Target') if not rel.get('Target').startswith('/') else rel.get('Target')[1:]) for rel in rels}
ss = []
sst = ET.fromstring(z.read('xl/sharedStrings.xml'))
ss = [''.join(t.text or '' for t in si.findall('.//m:t', NS)) for si in sst.findall('m:si', NS)]
sheet = wb.find('m:sheets/m:sheet', NS)
rid = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
target = relmap.get(rid, '')
root = ET.fromstring(z.read(target))

def num(x):
    try: return float(x)
    except: return 0.0
def xdate(v):
    try:
        return (datetime(1899, 12, 30) + timedelta(days=float(v))).strftime('%Y-%m-%d')
    except:
        return ''

rows = []
for row in root.findall('.//m:row', NS):
    cells = {}
    for c in row.findall('m:c', NS):
        t = c.get('t'); v = c.find('m:v', NS); isel = c.find('m:is', NS)
        ref = c.get('r', '')
        col = ''.join(ch for ch in ref if ch.isalpha())
        if t == 's' and v is not None: val = ss[int(v.text)]
        elif v is not None: val = v.text
        elif isel is not None: val = ''.join(x.text or '' for x in isel.findall('.//m:t', NS))
        else: val = ''
        cells[col] = val
    rows.append(cells)

# 渠道 -> 板块 快速分类
def plate_of(ch):
    ch = str(ch)
    if 'APR' in ch or 'AAR' in ch: return 'APR'
    if '羽通' in ch or '啟韬' in ch or '响誉' in ch: return 'Apple电商'
    if '舒尔' in ch: return 'Shure电商'
    if '分销' in ch: return '分销'
    if '天羽乐购' in ch: return '天羽乐购'
    return '其他'

status_tot = defaultdict(lambda: defaultdict(float))
for c in rows[1:]:
    d = xdate(c.get('Z', ''))
    if not ('2026-08-01' <= d <= '2026-08-26'): continue
    st = str(c.get('AB', '') or '').strip() or '(空)'
    amt = num(c.get('J', 0))
    p = plate_of(c.get('A', ''))
    status_tot[p][st] += amt

print('按付款时间(8/1-26) 各板块×订单状态 金额:')
for p, sts in sorted(status_tot.items()):
    tot = sum(sts.values())
    print(' ', p, '合计', round(tot, 2))
    for st, v in sorted(sts.items(), key=lambda x: -x[1]):
        print('     %-12s %12.2f' % (st, v))

# 各状态总金额
all_st = defaultdict(float)
for p, sts in status_tot.items():
    for st, v in sts.items():
        all_st[st] += v
print()
print('全部状态合计:', round(sum(all_st.values()), 2))
for st, v in sorted(all_st.items(), key=lambda x: -x[1]):
    print('  %-12s %12.2f' % (st, v))
