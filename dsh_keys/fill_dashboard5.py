# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding="utf-8").read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("  const vsItems = [\n    { k:'销售额 同比（YoY）', v:'+'+c.yoy+'%', d:'大盘同口径约 +2.8%', cls:'up' },\n    { k:'销售额 环比（WoW）', v:(c.w0>=0?'+':'')+c.w0+'%', d:'上周同期对比', cls:c.w0>=0?'up':'down' },\n    { k:'线上销售占比', v:pct(on), d:'上月 '+pct(on-0.8), cls:'up' },\n    { k:'线下销售占比', v:pct(off), d:'上月 '+pct(off+0.8), cls:'' },\n    { k:'APR 单店产能 vs 经销商均值', v:'+9.2%', d:'¥138,533 vs ¥126,800', cls:'up' },\n    { k:'综合费率 vs 预算', v:pct(c.feeRate), d:'预算红线 9.5% · 低于 0.8pp', cls:'up' }\n  ];", "  const vsItems = [\n    { k:'销售额 同比（YoY）', v:'+'+c.yoy+'%', d:'吉客云 API 实付口径（8/1-26）', cls:'up' },\n    { k:'销售额 环比（WoW）', v:c.w0!=null?(c.w0>=0?'+':'')+c.w0+'%':'待接入', d:'上周同期对比', cls:c.w0!=null?(c.w0>=0?'up':'down'):'' },\n    { k:'线上销售占比', v:pct(on), d:'线下 '+pct(off), cls:'up' },\n    { k:'线下销售占比', v:pct(off), d:'线上 '+pct(on), cls:'' },\n    { k:'APR 单店产能 vs 经销商均值', v:'待接入', d:'季度口径数据待更新', cls:'' },\n    { k:'综合费率 vs 预算', v:fee(c.feeRate), d:'预算红线 9.5% · 待财务数据', cls:'' }\n  ];", 1, 'vsItems2')
R("    return { name:s.name, pct:share, color: s.code==='APR'?'#2f69c2':s.code==='AE'?'#c79118':'#188b70' };", "    return { name:s.name, pct:share, color: s.code==='APR'?'#2f69c2':s.code==='AE'?'#c79118':s.code==='SH'?'#188b70':'#9aa8b8' };", 1, 'segShare2')
R("    <tr class=\"grp\"><td colspan=\"6\">线上 / 线下结构（${pl}）</td></tr>\n    <tr><td class=\"t-name\">线下（APR 门店）</td><td>${fmtY(mul(COMPANY.day.sales*off/100))}</td><td>${pct(off)}</td><td>${pct(22.4)}</td><td>客流 ${(30833/MULT[state.period]).toLocaleString()} 人次</td><td><span class=\"pos\">+8.2%</span></td></tr>\n    <tr><td class=\"t-name\">线上（Apple+舒尔）</td><td>${fmtY(mul(COMPANY.day.sales*on/100))}</td><td>${pct(on)}</td><td>${pct(2.8)}</td><td>访客 ${(51600/MULT[state.period]).toLocaleString()} 人次</td><td><span class=\"neg\">-1.2%</span></td></tr>", "    <tr class=\"grp\"><td colspan=\"6\">线上 / 线下结构（${pl}）</td></tr>\n    <tr><td class=\"t-name\">线下（APR 门店）</td><td>${fmtY(mul(COMPANY.day.sales*off/100))}</td><td>${pct(off)}</td><td>待接入</td><td>客流 待接入（接口）</td><td>待接入</td></tr>\n    <tr><td class=\"t-name\">线上（Apple+舒尔）</td><td>${fmtY(mul(COMPANY.day.sales*on/100))}</td><td>${pct(on)}</td><td>待接入</td><td>访客 待接入（明早导出）</td><td>待接入</td></tr>", 1, 'onoffRows2')
R("aiTip('业务结构健康度：APR 贡献 50.3% 销售额但转化率（22.4%）显著高于线上（2.8%）；毛利率三板块分化明显（舒尔 21.5% &gt; APR 12.8% &gt; 电商 9.6%），结构优化空间在电商 1PP 与国补承接。')", "aiTip('业务结构：APR 贡献 63.1% 销售额（线下 43.7%/线上 56.3%）；毛利率分化：Shure 30.31% &gt; Apple 电商 4.98% &gt; APR 3.10%；转化/费率待接入。')", 1, 'aiTip2')
R("      concl:`${pl}销售额同比 +${c.yoy}%、环比 +${c.w0}%；线下占 ${pct(off)}、线上占 ${pct(on)}，线上占比环比提升 0.8pp。APR 单店产能高于经销商均值 9.2%，8 项同行对比指标 6 项领先。`,", "      concl:`${pl}销售额同比 +${c.yoy}%、环比待接入；线下占 ${pct(off)}、线上占 ${pct(on)}。APR 毛利率 3.10%（线下 4.12%/线上 O2O 0.80%）。`,", 1, 'concl2')
R("      anom:'线上综合转化率 2.8% 仅为线下 1/8，京东店环比 -8.7% 拖累；线下苏家屯转化率 2.9% 与日照 9.3% 相差 3 倍以上，店间能力断层明显。',", "      anom:'线上综合转化率待接入（明早平台导出）；APR 门店转化率待接入（客流接口）；苏家屯同比 -5.1% 为唯一负增长门店。',", 1, 'anom2')
R("      act:'① 线上：京东店投放迁移抖音（ROI 2.9），详情页 A/B 提升加购转化；② 线下：苏家屯转化专项（8/21-27），日照大单经验（客单 ¥3,363）向全系复制；③ 国补承接：政策科口径五种机型分别跟踪，Mac/iPad 国补占比提升空间最大。'", "      act:'① 电商流量/转化明早接入；② 线下客流接口接入后补门店转化；③ 苏家屯负增长专项诊断。'", 1, 'act2')
R("const k4 = kpiCard('周转天数', '42 天', -2, '环比慢 2 天 · 90 天以上占 36.9%', '');", "const k4 = kpiCard('周转天数', '待接入', null, '需销售速率数据', '');", 1, '周转天数')
R("      ${pie3dCard('库龄结构（'+pl+'）', agingParts, '¥2,450万<br>总库存', '180+ 天合计 '+pct(riskPct)+' · 重点 180/360 天')}", "      ${pie3dCard('库龄结构（'+pl+'）', agingParts, '¥'+INV_BIZ.total_amount.toFixed(0)+'万<br>总库存', '90 天以上 '+pct(INV_BIZ.risk_pct)+' · 重点 90/360 天')}", 1, '库龄pie')
R("      ${tableCard('高库龄预警（180/360 天以上）','风险金额 ¥858 万 · 360 天以上 ¥120.9 万',['品类','SKU 数','金额','库龄','仓库','级别'],riskRows)}", "      ${tableCard('高库龄预警（90/360 天以上）','风险金额 ¥706 万 · 360 天以上 ¥'+INV_BIZ.severe_amount.toFixed(1)+' 万',['品类','SKU 数','金额','库龄','仓库','级别'],riskRows)}", 1, '高库龄表')
R("${tableCard('高库龄 TOP15 明细','商务库存分析表 260807 口径',['品类','数量','金额','库龄','仓库','级别'],riskRows)}", "${tableCard('高库龄 TOP15 明细','商务库存分析表 260826 口径',['品类','数量','金额','库龄','仓库','级别'],riskRows)}", 1, 'TOP15口径')
R("<div class=\"date-box\">数据日期 2026-08-20<small>更新于 12:00 · 演示数据+部分实时</small></div>", "<div class=\"date-box\">数据日期 2026-08-26<small>更新于 24:00 · 真实数据（8/1-26）· 流量/费率待接入</small></div>", 1, '日期框')
R("   V6 经营看板 · 数据层（演示数据 + 部分实时，结构对齐正式取数口径）", "   V6 经营看板 · 数据层（真实数据 8/1-26 · 吉客云 + 商务库存分析表 + 平台日报）", 1, '注释')
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
print(); print('PART5 done, ok =', ok)