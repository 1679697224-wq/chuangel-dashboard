# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("  { name:'天猫旗舰店', sales:24709, gpm:30.31, gross:7489, uv:70155, cvr:0.82, refund:null, d7:null, yoy:15.5, task:220, rate:32.8, src:'吉客云自动' },", "  { name:'天猫旗舰店', sales:24709, gpm:30.31, gross:7489, uv:90841, cvr:0.88, refund:null, d7:null, yoy:15.5, task:220, rate:32.8, src:'吉客云自动' },", 1, 'SH天猫uv完整')
R("  const k3 = kpiCard('访客数','25,117（京东）',null,'天猫 70,155（日报8/1-16+24-26，17-23待补）','gold');", "  const k3 = kpiCard('访客数','25,117（京东）',null,'天猫 90,841（日报8/1-26）','gold');", 1, 'SH k3完整')
R("  const k4 = kpiCard('转化率','3.12%（京东）',null,'天猫 0.82%（日报19天）','');", "  const k4 = kpiCard('转化率','3.12%（京东）',null,'天猫 0.88%（日报8/1-26）','');", 1, 'SH k4完整')
R("      ${tableCard('店铺经营对比（天猫 / 京东）','目标为财务 8 月表 · 京东为平台日报口径(8/1-26) · 天猫流量为日报8/1-16+8/24-26',['店铺','销售额','目标','达成率','毛利率','访客数','转化率'],rows)}", "      ${tableCard('店铺经营对比（天猫 / 京东）','目标为财务 8 月表 · 天猫销售以吉客云为准(日报111.74万) · 流量为平台日报8/1-26',['店铺','销售额','目标','达成率','毛利率','访客数','转化率'],rows)}", 1, 'SH表头完整')
R("      anom:'天猫流量日报含 8/1-16 与 8/24-26（uv 70,155/转化 0.82%），8/17-23 待运营补全；京东毛利率无数据（未计入公司合计）；京东舒尔若含入，公司销售约 3,264 万。',", "      anom:'天猫日报 8/1-26 完整（uv 90,841/转化 0.88%，销售 111.74 万为平台口径，与吉客云 72.15 万差 39.6 万，以吉客云为准）；京东毛利率无数据（未计入公司合计）；京东舒尔若含入，公司销售约 3,264 万。',", 1, 'SH anom完整')
ok = True
for old, new, expect, name in REPS:
    n = src.count(old)
    if n != expect:
        print("MISS/COUNT[%s]: expected %d, got %d" % (name, expect, n))
        ok = False
    else:
        src = src.replace(old, new)
        print("ok  [%s]" % name)
io.open(P, 'w', encoding='utf-8').write(src)
print(); print('PART14 done, ok =', ok)