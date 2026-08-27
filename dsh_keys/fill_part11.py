# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("    return tableCard('业务板块对比（'+pl+'）', feeHead, ['业务板块','销售额','毛利额','毛利率','转化率', ...(isMonth()?['费率']:[]), '库存','占比','环比','同比'], SEGMENTS.map(s=>cells(s)+segSubRows(s)).join('')+tRow);", "    return tableCard('业务板块对比（'+pl+'）', feeHead, ['业务板块','销售额','毛利额','毛利率','转化率', ...(isMonth()?['费率']:[]), '库存','占比','环比','同比'], SEGMENTS.map(cells).join('')+tRow);", 1, '简报去分店行')
R("    return mainRow + segSubRows(s);", "    return mainRow;", 1, '渠道对比去分店行')
R("const SH_STORES = [\n  { name:'天猫旗舰店', sales:24709, gpm:30.31, gross:7489, uv:null, cvr:null, refund:null, d7:null, yoy:15.5, task:220, rate:32.8, src:'吉客云自动' },\n  { name:'京东旗舰店', sales:24726, gpm:null, gross:0, uv:24172, cvr:3.15, refund:null, d7:null, yoy:null, task:210, rate:34.4, src:'平台日报·手工' }\n];", "const SH_STORES = [\n  { name:'天猫旗舰店', sales:24709, gpm:30.31, gross:7489, uv:65082, cvr:0.72, refund:null, d7:null, yoy:15.5, task:220, rate:32.8, src:'吉客云自动' },\n  { name:'京东旗舰店', sales:25592, gpm:null, gross:0, uv:25117, cvr:3.12, refund:null, d7:null, yoy:null, task:210, rate:35.6, orders:783, aov:954, src:'平台日报·手工' }\n];", 1, 'SH_STORES更新')
R("  const k1 = kpiCard('销售总额',fmtY(mul(total)),null,'天猫(吉客云自动)+京东(日报手工)','green');", "  const k1 = kpiCard('销售总额',fmtY(mul(total)),null,'天猫72.15万(吉客云)+京东74.73万(日报)','green');", 1, 'SH k1')
R("  const k3 = kpiCard('访客数','待接入',null,'京东 24,172（8/1-25）· 天猫待导出','gold');", "  const k3 = kpiCard('访客数','25,117（京东）',null,'天猫 65,082（日报8/1-16，17-26待补）','gold');", 1, 'SH k3')
R("  const k4 = kpiCard('转化率','待接入',null,'京东 3.15% · 天猫待导出','');", "  const k4 = kpiCard('转化率','3.12%（京东）',null,'天猫 0.72%（日报8/1-16）','');", 1, 'SH k4')
R("  const k5 = kpiCard('客单价','¥949',null,'京东 8/1-25 · 天猫 ¥756','');", "  const k5 = kpiCard('客单价','¥954',null,'京东 8/1-26 · 天猫 ¥756','');", 1, 'SH k5')
R("      ${tableCard('店铺经营对比（天猫 / 京东）','目标为财务 8 月表 · 京东为平台日报手工口径',['店铺','销售额','目标','达成率','毛利率','访客数','转化率'],rows)}", "      ${tableCard('店铺经营对比（天猫 / 京东）','目标为财务 8 月表 · 京东为平台日报口径(8/1-26) · 天猫流量为日报8/1-16',['店铺','销售额','目标','达成率','毛利率','访客数','转化率'],rows)}", 1, 'SH表头')
R("      concl:'Shure 电商：天猫 72.15 万/达成 32.8%（目标 220 万）·吉客云自动；京东 72.2 万/达成 34.4%（目标 210 万）·日报手工（8/1-25）。',\n      anom:'天猫流量待明早导出（模板到 8/16，转化 0.72%）；京东 8/26 待补；京东毛利率无数据（未计入合计）。',\n      act:'① 明早接天猫完整流量/转化；② 京东按日报手工更新；③ 两店转化对标优化（天猫 0.72% vs 京东 3.15%）。'", "      concl:'Shure 电商：天猫 72.15 万/达成 32.8%（目标 220 万）·吉客云；京东 74.73 万/达成 35.6%（目标 210 万）·日报 8/1-26。',\n      anom:'天猫流量日报仅至 8/16（uv 65,082/转化 0.72%），17-26 待运营补全；京东毛利率无数据（未计入公司合计）；京东舒尔若含入，公司销售约 3,264 万。',\n      act:'① 向运营补要天猫 8/17-26 流量；② 京东按日报持续手工更新；③ 两店转化对标优化（天猫 0.72% vs 京东 3.12%）。'", 1, 'SH分析')
R("aiTip('8/1-26 已支付销售额 <b>¥3,189 万</b>（分摊后口径），同比 +45.8%；APR 板块贡献 63.1% 为增长主引擎；Apple 电商分店：啟韬 71.6% / 羽通 13.5%，羽通目标口径需核查；Shure 天猫(自动)+京东(日报手工) 已分店展示。')", "aiTip('8/1-26 已支付销售额 <b>¥3,189 万</b>（分摊后口径），同比 +45.8%；APR 板块贡献 63.1% 为增长主引擎；Apple 电商分店：啟韬 71.6% / 羽通 13.5%，目标口径需运营确认；京东舒尔 74.73 万（平台日报）另计，含入后公司约 3,264 万。')", 1, '简报aiTip')
R("  { name:'Shure 电商', code:'SH', sales:24708, gross:7489, gpm:30.31, cvr:null, feeRate:null, inv:229.5, d7:null, yoy:15.5, onlineShare:100, offlineShare:0, note:'天猫(吉客云自动)+京东(日报手工另计)',", "  { name:'Shure 电商', code:'SH', sales:24708, gross:7489, gpm:30.31, cvr:null, feeRate:null, inv:229.5, d7:null, yoy:15.5, onlineShare:100, offlineShare:0, note:'天猫72.15(吉客云)+京东74.73(日报)另计',", 1, 'SH segment note')
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
print(); print('PART11 done, ok =', ok)