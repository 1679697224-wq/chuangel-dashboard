# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding="utf-8").read()

REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))

R(">演示数据<", ">8月累计<", 5, "tag全部")

R("月度目标达成 vs 时间进度（8 月）<span class=\"section-tag\">黑色刻度线 = 时间进度 64.5%</span>",
  "月度目标达成 vs 时间进度（8 月）<span class=\"section-tag\">黑色刻度线 = 时间进度 83.9%（8/1-26）</span>", 1, "goalCard时间")

R("'环比 '+c.d7+'% · 同比 +'+c.yoy+'%'", "(c.d7!=null?'环比 '+c.d7+'% · ':'')+'同比 +'+c.yoy+'%'", 2, "k1子文案")
R("'日目标 ¥780,000'", "'日目标 ¥'+Math.round(COMPANY.day.target).toLocaleString()", 1, "日目标")
R("'线下 22.4% / 线上 2.8%'", "'线下/线上转化率待接入'", 1, "转化率副标")
R("kpiCard('库存总额', '¥5,860万', null, '周转 42 天 · 超龄 12.4%', 'gold')",
  "kpiCard('库存总额', '¥'+INV_BIZ.total_amount.toFixed(0)+'万', null, '90 天以上超龄 '+INV_BIZ.risk_pct.toFixed(1)+'%', 'gold')", 2, "库存总额卡")
R("<b>¥5,860万</b>", "<b>¥'+INV_BIZ.total_amount.toFixed(0)+'万</b>", 2, "合计库存")
R("'月度目标 ¥24,600,000'", "'月度目标 '+fmtY(COMPANY.day.target*MULT.month)", 1, "月度目标")
R("'¥5,860万<br>总库存'", "'¥'+INV_BIZ.total_amount.toFixed(0)+'万<br>总库存'", 2, "库存环图中心")

R("aiTip('今日整体达成 <b>106%</b>，APR 板块贡献 50.3% 为增长主引擎；苏家屯（36.2%）与镇江（42.3%）达成率最低，是 8 月冲刺的两大攻坚点。')",
  "aiTip('8/1-26 已支付销售额 <b>¥3,189 万</b>（分摊后口径），同比 +45.8%；APR 板块贡献 63.1% 为增长主引擎，日照（147.5%）与彭城（128.3%）达成领先；Apple 电商达成 26.5% 需重点核查。')", 1, "销售指标aiTip")

# 销售指标分析（含 JS 模板字面量，用 \\` 与 \\${ 转义）
old_concl = "      concl:`${pl}销售额 <b>${fmtY(mul(COMPANY.day.sales))}</b>，目标达成 <b>${rate.toFixed(1)}%</b>，毛利率 ${pct(COMPANY.day.gpm)}。APR 板块贡献 50.3%、环比 +8.2%，为当日增长主引擎；Apple 电商受京东店 -8.7% 拖累环比 -3.4%。`,\n      anom:'苏家屯店达成率 36.2% 全系最低（转化率 2.9%）；镇江重开红利需在 8/31 前兑现；90 天以上库存占比升至 12.4%；抖音店退款率 3.4% 高于基准。',\n      act:'① 苏家屯：按 8.18 会议专项诊断方案落地（8/21-27 iPhone 转化专项）；② 镇江：开业红利期冲量，全员到岗+主推品补货；③ 京东店：核查流量下滑归因，投放 ROI 低于 2.0 红线需调整；④ 超龄库存列入周五不动销处理清单。'"
new_concl = "      concl:`8/1-26 已支付销售额 <b>${fmtY(mul(COMPANY.day.sales))}</b>（分摊后、含在途），目标达成 <b>${rate.toFixed(1)}%</b>，毛利率 ${pct(COMPANY.day.gpm)}。APR 板块贡献 63.1%、同比 +72.8%，为增长主引擎；Apple 电商在途订单占比高（567 万）。`,\n      anom:'Apple 电商达成 26.5%（目标 4,042 万/财务表，需运营确认口径）；苏家屯店达成 60.1% 全系最低；90 天以上库存占比 38.1%（706 万）；待审核订单 75 万。',\n      act:'① 与运营核对 Apple 电商目标与国补/在途口径；② 苏家屯店专项诊断（转化专项）；③ 90 天以上库存纳入处置清单；④ 明早接入电商流量/转化与线下客流接口。'"
R(old_concl, new_concl, 1, "销售指标分析")

R("aiTip('渠道结构：APR 整体贡献 50.3% 销售额、转化率 22.4% 显著高于线上；Apple 电商环比 -3.4% 受京东店拖累；Shure 电商增速 +12.6% 领跑；综合费率月度口径 8.9% 低于预算红线 9.5%。')",
  "aiTip('渠道结构：APR 整体贡献 63.1% 销售额、同比 +72.8% 显著领先；Apple 电商 +89.2%（低基数）；Shure 天猫 +15.5%。费率/转化待接入。')", 1, "渠道对比aiTip")

old_cc = "      concl:`${pl}总销售额 <b>${fmtY(mul(COMPANY.day.sales))}</b>，目标达成 <b>${rate.toFixed(1)}%</b>，毛利率 ${pct(c.gpm)}。APR 整体为增长主引擎（占比 50.3%、环比 +8.2%），Shure 电商 +12.6% 领跑，Apple 电商环比 -3.4%。`,\n      anom:'Apple 电商京东店 -8.7% 拖累；APR 苏家屯达成率 36.2% 全系最低；90 天以上库存占比升至 12.4%。',\n      act:'① 苏家屯：8/21-27 iPhone 转化专项；② 京东店：流量下滑归因核查，投放 ROI 低于 2.0 红线需调整；③ 超龄库存列入周五不动销处理清单。'"
new_cc = "      concl:`${pl}总销售额 <b>${fmtY(mul(COMPANY.day.sales))}</b>，目标达成 <b>${rate.toFixed(1)}%</b>，毛利率 ${pct(c.gpm)}。APR 整体为增长主引擎（占比 63.1%、同比 +72.8%）。`,\n      anom:'Apple 电商达成 26.5% 为主要缺口；苏家屯达成 60.1% 全系最低；90 天以上库存 38.1%。',\n      act:'① Apple 电商在途发货与目标口径核查；② 苏家屯转化专项；③ 90 天以上库存处置清单。'"
R(old_cc, new_cc, 1, "渠道对比分析")

R("const segShare = SEGMENTS.map(s=>({ name:s.name, pct:s.sales/COMPANY.day.sales*100, color: s.code==='APR'?'#2f69c2':s.code==='AE'?'#c79118':'#188b70' }));",
  "const segShare = SEGMENTS.map(s=>({ name:s.name, pct:s.sales/COMPANY.day.sales*100, color: s.code==='APR'?'#2f69c2':s.code==='AE'?'#c79118':s.code==='SH'?'#188b70':'#9aa8b8' }));", 1, "segShare色")

old_vs = "  const vsItems = [\n    { k:'销售额 同比（YoY）', v:'+'+c.yoy+'%', d:'大盘同口径约 +2.8%', cls:'up' },\n    { k:'销售额 环比（WoW）', v:(c.w0>=0?'+':'')+c.w0+'%', d:'上周同期对比', cls:c.w0>=0?'up':'down' },\n    { k:'线上销售占比', v:pct(on), d:'上月 '+pct(on-0.8), cls:'up' },\n    { k:'线下销售占比', v:pct(off), d:'上月 '+pct(off+0.8), cls:'' },\n    { k:'综合费率 vs 预算', v:fee(c.feeRate), d:isMonth()?'预算红线 9.5% · 低 0.6pp':monthlyNote, cls:'up' }\n  ];"
new_vs = "  const vsItems = [\n    { k:'销售额 同比（YoY）', v:'+'+c.yoy+'%', d:'吉客云 API 实付口径（8/1-26）', cls:'up' },\n    { k:'销售额 环比（WoW）', v:c.w0!=null?(c.w0>=0?'+':'')+c.w0+'%':'待接入', d:'上周同期对比', cls:c.w0!=null?(c.w0>=0?'up':'down'):'' },\n    { k:'线上销售占比', v:pct(on), d:'线下 '+pct(off), cls:'up' },\n    { k:'线下销售占比', v:pct(off), d:'线上 '+pct(on), cls:'' },\n    { k:'综合费率 vs 预算', v:fee(c.feeRate), d:isMonth()?'财务费率数据待接入':monthlyNote, cls:'' }\n  ];"
R(old_vs, new_vs, 1, "vsItems")

old_onoff = "    <tr><td class=\"t-name\">线下（APR 整体）</td><td>${fmtY(mul(COMPANY.day.sales*off/100))}</td><td>${pct(off)}</td><td>${pct(22.4)}</td><td>客流 ${(30833/MULT[state.period]).toLocaleString()} 人次</td><td><span class=\"pos\">+8.2%</span></td></tr>\n    <tr><td class=\"t-name\">线上（Apple+舒尔）</td><td>${fmtY(mul(COMPANY.day.sales*on/100))}</td><td>${pct(on)}</td><td>${pct(2.8)}</td><td>访客 ${(51600/MULT[state.period]).toLocaleString()} 人次</td><td><span class=\"neg\">-1.2%</span></td></tr>"
new_onoff = "    <tr><td class=\"t-name\">线下（APR 整体）</td><td>${fmtY(mul(COMPANY.day.sales*off/100))}</td><td>${pct(off)}</td><td>待接入</td><td>客流 待接入（接口）</td><td>待接入</td></tr>\n    <tr><td class=\"t-name\">线上（Apple+舒尔）</td><td>${fmtY(mul(COMPANY.day.sales*on/100))}</td><td>${pct(on)}</td><td>待接入</td><td>访客 待接入（明早导出）</td><td>待接入</td></tr>"
R(old_onoff, new_onoff, 1, "线上线下行")

R("aiTip('业务结构健康度：APR 贡献 50.3% 销售额但转化率 22.4% 显著高于线上 2.8%；毛利率三板块分化明显（舒尔 21.5% &gt; APR 12.8% &gt; 电商 9.6%）；线上占比环比提升 0.8pp。')",
  "aiTip('业务结构：APR 贡献 63.1% 销售额（线下 43.7%/线上 56.3%）；毛利率分化：Shure 30.31% &gt; Apple 电商 4.98% &gt; APR 3.10%；转化/费率待接入。')", 1, "占比aiTip")

old_cs = "      concl:`${pl}销售额同比 +${c.yoy}%、环比 +${c.w0}%；线下占 ${pct(off)}、线上占 ${pct(on)}，线上占比环比提升 0.8pp。`,\n      anom:'线上综合转化率 2.8% 仅为线下 1/8；京东店环比 -8.7% 拖累；线下苏家屯转化率 2.9% 与日照 9.3% 相差 3 倍以上。',\n      act:'① 线上：京东店投放迁移抖音（ROI 2.9），详情页 A/B 提升加购转化；② 线下：苏家屯转化专项（8/21-27），日照大单经验（客单 ¥3,363）向全系复制。'"
new_cs = "      concl:`${pl}销售额同比 +${c.yoy}%、环比待接入；线下占 ${pct(off)}、线上占 ${pct(on)}。`,\n      anom:'线上综合转化率待接入（明早平台导出）；APR 门店转化率待接入（客流接口）；苏家屯同比 -5.1% 为唯一负增长门店。',\n      act:'① 电商流量/转化明早接入；② 线下客流接口接入后补门店转化；③ 苏家屯负增长专项诊断。'"
R(old_cs, new_cs, 1, "占比分析")

R("const k2 = kpiCard('高库龄风险占比', pct(INV_BIZ.risk_pct), 0, '180 天以上口径 · 风险金额 ¥858 万', 'red');",
  "const k2 = kpiCard('90 天以上风险占比', pct(INV_BIZ.risk_pct), null, '90 天以上口径 · 风险金额 ¥706 万', 'red');", 1, "库存k2")
R("'主机 79%'", "'主机 76%'", 1, "主机占比")
R("aiTip('库存健康度：总库存 ¥2,450 万、180 天以上风险占比 <b>37.0%</b>（¥858 万），其中 360 天以上 ¥120.9 万（1,325 SKU）必须处置。高库龄集中在 iPhone 17 Pro Max 星宇色（¥162 万/169 台/153 天）与 iPhone 17 黑色（¥48 万），两个型号合计占高库龄 24.5%。')",
  "aiTip('库存健康度：总库存 <b>¥2,109 万</b>（商务表 260826、含在途）、90 天以上风险占比 <b>38.1%</b>（¥706 万），其中 360 天以上 ¥124 万（904 SKU）需处置。最大单点风险为 iPhone 17 Pro Max 星宇橙 137 台（¥131 万/162 天，南京羽通仓）。')", 1, "库存aiTip")

old_inv = "      concl:'商务库存表（260807）口径：库存总额 ¥2,450 万、SKU 2.02 万；苹果主机占 79% 为库存主体；90 天以上库龄合计 ¥858 万（37%），周转压力集中在主机类。',\n      anom:'iPhone 17 Pro Max 星宇色 169 台（¥162 万）库龄 153 天为最大单点风险；360 天以上 1,325 SKU 需处置；舒尔仓库（欧瑞特南京云）耳机类 87 条库龄 272 天；零库存 Watch 表带与 Studio Display 支架需补货。',\n      act:'① 高库龄 iPhone 优先走员工内购+总代退换+以旧换新通道；② 360 天以上 SKU 本周出处置清单（目标 30%）；③ 零库存 2 项 3 天内补货；④ 每周五商务表同步后更新看板。'"
new_inv = "      concl:'商务库存分析表（260826）口径：库存总额 ¥2,109 万、SKU 6,243；苹果主机占 76% 为库存主体；90 天以上库龄合计 ¥706 万（38.1%），周转压力集中在电商-羽通（79.3%）与舒尔（45.6%）。',\n      anom:'iPhone 17 Pro Max 星宇橙 137 台（¥131 万）库龄 162 天为最大单点风险；360 天以上 904 SKU 需处置；APR 门店 90 天以上 404 万（30.4%）样机占比较高；京东舒尔库存 92.2 万需关注动销。',\n      act:'① 高库龄 iPhone 优先走员工内购/总代退换/以旧换新通道；② 360 天以上 SKU 本周出处置清单（目标 30%）；③ 每周五商务表更新后刷新看板。'"
R(old_inv, new_inv, 1, "库存分析")

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
print()
print("PART2 done, ok =", ok)