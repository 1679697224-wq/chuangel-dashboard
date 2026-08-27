# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding="utf-8").read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("const AE_FUNNEL = [\n  { name:'访客数', v:42600, w:100, r:'42,600' },\n  { name:'详情页浏览', v:31200, w:73, r:'73.2%' },\n  { name:'加购', v:8540, w:36, r:'20.0%' },\n  { name:'支付订单', v:1192, w:14, r:'支付转化 2.8%' }\n];", "const AE_FUNNEL = [\n  { name:'访客数', v:0, w:100, r:'待接入' },\n  { name:'详情页浏览', v:0, w:70, r:'待接入' },\n  { name:'加购', v:0, w:35, r:'待接入' },\n  { name:'支付订单', v:0, w:15, r:'支付转化 待接入' }\n];", 1, 'AE_FUNNEL')
R("${f.w===100?'42,600':f.r}", "${f.w===100?'待接入':f.r}", 1, '漏斗硬编码')
R("${kpiCard('支付转化率',pct(2.8),-0.1,'成交 1,192 ÷ 访客 42,600 = 2.8%','')}", "${kpiCard('支付转化率','待接入',null,'明早平台导出后接入','')}", 1, 'AE转化率卡')
R("${kpiCard('退款金额（日）',fmtY(mul(8648)),3.2,'退款率 2.9%','red')}", "${kpiCard('退款金额（月）','待接入',null,'平台数据待接入','red')}", 1, 'AE退款卡')
R("${kpiCard('平台用户画像','新客 62%','—','25-34 岁占 48%，待接入完整画像','gold')}", "${kpiCard('平台用户画像','待接入',null,'明早平台导出后接入','gold')}", 1, 'AE画像卡')
R("${kpiCard('用户习惯分析','晚 20-22 点峰值','—','下单高峰占 31%，待接入明细','gold')}", "${kpiCard('用户习惯分析','待接入',null,'明早平台导出后接入','gold')}", 1, 'AE习惯卡')
R("    concl:'漏斗整体健康（加购→支付 14.0%）；规模指数 86 位居竞店第 2，定价低于 TOP 竞店 1.8% 具备价格竞争力；补贴/分期力度（24期免息）优于多数竞店。',\n    anom:'详情页→加购转化 27.4% 低于上期 29.1%（主图与详情待优化）；退款集中在抖音店（3.4%）；竞店 A 百亿补贴活动期间访客高 10%，需监控价格挤压。',\n    act:'① 详情页 A/B 测试本周上线（加购转化目标 30%）；② 抖音店核查物流商责赔付；③ 竞店数据每日自动抓取（平台 API），补贴/定价变化自动预警。'", "    concl:'Apple 电商流量/转化数据待接入（明早平台导出）；当前仅有销售/毛利真实数据。',\n    anom:'在途 567 万/待审核 69 万为最大运营风险；京东羽通毛利率 9.92% 为正、苏宁啟韬 2.48% 偏低。',\n    act:'① 明早接入天猫/京东流量、转化、退款与用户画像；② 核查在途发货时效；③ 与运营确认 8 月目标口径。'", 1, 'AE分析文本')
R("/* ---------- 商务库存分析表（真实口径，来源：库存分析表_260807.xlsx） ---------- */", "/* ---------- 商务库存分析表（真实口径，来源：库存分析表_260826.xlsx） ---------- */", 1, '库存来源注释')
ok = True
for old, new, expect, name in REPS:
    n = src.count(old)
    if n != expect:
        print("MISS/COUNT[%s]: expected %d, got %d" % (name, expect, n))
        ok = False
    else:
        src = src.replace(old, new)
        print("ok  [%s]" % name)
io.open(P, "w", encoding="utf-8").write(src)
print(); print('PART6 done, ok =', ok)