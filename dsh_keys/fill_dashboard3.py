# -*- coding: utf-8 -*-
import io, json
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
F = json.load(open("/Users/lili/Desktop/deepseek harness/吉客云数据/fill_data.json"))
src = io.open(P, encoding="utf-8").read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))

# ---- INV_BIZ ----
risk_rows = []
for r in F['inv_risk_top']:
    wh = r['wh'].replace('[005]', '').replace('南京', '').strip()
    risk_rows.append('{ age:%d, amount:%.2f, brand:%s, cat:%s, name:%s, qty:%d, wh:%s }' % (r['age'], r['amount'], repr(r['brand']), repr(r['cat']), repr(r['name']), r['qty'], repr(wh)))
new_inv = '''let INV_BIZ = {
  total_amount: 2108.85,           // 库存总额（万元，总览口径含在途 · 商务表260826）
  total_skus: 6243,                // 库存明细行数
  risk_pct: 38.1,                  // 90 天以上风险占比（总览渠道库龄口径）
  severe_amount: 123.98,           // 360 天以上金额（万元）
  severe_count: 904,               // 360 天以上 SKU 数
  category: [
    { name:'苹果主机', amount:1603.38, pct:76.0, qty:2422, color:'#2f69c2' },
    { name:'原装配件', amount:139.61, pct:6.6, qty:3178, color:'#64a4da' },
    { name:'舒尔', amount:302.82, pct:14.4, qty:6065, color:'#188b70' },
    { name:'第三方配件', amount:63.05, pct:3.0, qty:12293, color:'#c79118' }
  ],
  aging: [
    { name:'0~30 天', amount:869.47, color:'#2f69c2' },
    { name:'30~60 天', amount:217.78, color:'#64a4da' },
    { name:'60~90 天', amount:57.57, color:'#42a287' },
    { name:'90~180 天', amount:351.87, color:'#c79118' },
    { name:'180~360 天', amount:230.20, color:'#e07b39' },
    { name:'360 天以上', amount:123.98, color:'#c94d5c' }
  ],
  machine: {
    'APR 门店': { normal:1136.22, demo:299.50, defect:6.86 },
    '电商-啟韬': { normal:90.96, demo:0, defect:4.26 },
    '电商-羽通': { normal:242.32, demo:0, defect:4.74 },
    '电商-舒尔': { normal:136.42, demo:0, defect:26.02 },
    '电商-其他': { normal:6.72, demo:0, defect:0.96 },
    '京东-舒尔': { normal:92.20, demo:0, defect:0 }
  },
  aging_risk: [
    ''' + ',\n    '.join(risk_rows) + '''
  ],
  coverage: [
    { status:'零库存', desc:'42mm/玫瑰金色铝金属表壳/淡桃粉色运动型表带 S/M', gap:2, mpn:'MF984CH/B' },
    { status:'零库存', desc:'Studio Display 标准玻璃面板 VESA 支架转换器', gap:1, mpn:'MFEY4CH/A' }
  ]
};'''
old_inv_start = src.index('let INV_BIZ = {')
old_inv_end = src.index('};', old_inv_start) + 2
old_inv = src[old_inv_start:old_inv_end]
R(old_inv, new_inv, 1, 'INV_BIZ')

R("const INV_STRUCTURE = [\n  { name:'90 天以内（健康）', pct:74.2, color:'#2f69c2' },\n  { name:'90 天以上超龄', pct:12.4, color:'#c94d5c' },\n  { name:'周度不动销', pct:8.1, color:'#c79118' },\n  { name:'残次商品', pct:5.3, color:'#7b91ad' }\n];", "const INV_STRUCTURE = [\n  { name:'90 天以内（健康）', pct:61.9, color:'#2f69c2' },\n  { name:'90 天以上超龄', pct:38.1, color:'#c94d5c' }\n];", 1, 'INV_STRUCTURE')
R("const FEES = [ { name:'扣点租金', v:126 }, { name:'人工费用', v:98 }, { name:'推广费', v:62 }, { name:'物流费用', v:14 }, { name:'其他费用', v:17 }, { name:'资金占用+后台', v:31 }, { name:'滞销/残次计提', v:9 } ];", "const FEES = [];   // 费用数据待财务 8 月利润表接入", 1, 'FEES')
R("const ALERTS = [\n  { level:'red', title:'苏家屯店达成率 36.2% 全系最低', text:'连续 4 日未达标，客流 1575 人次为最低梯队，转化率 2.9% 远低于大盘 6.4%，需专项诊断（8 月冲刺方案已排期）。' },\n  { level:'red', title:'镇江苏宁店 8/15 重开', text:'重开前半月损失约 30 万，重开后客流环比 +12.4%，需抓住开业红利期至 8/31 冲量。' },\n  { level:'yellow', title:'90 天以上库存占比 12.4%', text:'环比 +1.8pp，主要集中在 iPad 旧款；建议纳入不动销处理清单。' },\n  { level:'yellow', title:'Apple 电商退款率 2.9%', text:'高于 2.5% 基准，抖音店 3.4% 为主要来源，核查商责归因。' },\n  { level:'green', title:'日照店达成率 90% 领先', text:'客单价 ¥3,363 全系最高（大单能力强），可提炼经验复制。' }\n];", "const ALERTS = [\n  { level:'red', title:'Apple 电商达成 26.5% 为主要缺口', text:'8/1-26 实际 1,073 万 vs 目标 4,042 万（财务表），发货在途 567 万、待审核 69 万，需与运营核对目标口径与发货时效。' },\n  { level:'red', title:'苏家屯店达成 60.1% 全系最低', text:'84.17 万/140 万，同比 -5.1% 为唯一负增长门店，需专项诊断（8 月冲刺方案已排期）。' },\n  { level:'yellow', title:'90 天以上库存占比 38.1%（706 万）', text:'集中在电商-羽通（79.3%）与舒尔（45.6%）；360 天以上 904 SKU/124 万需处置。' },\n  { level:'yellow', title:'待审核订单 75 万', text:'主要来自 Apple 电商（69 万），需关注审核时效与退款风险。' },\n  { level:'green', title:'日照店达成 147.5% 领先', text:'118.02 万/80 万，客单价 ¥4,471 全系第二，可提炼大单经验复制。' }\n];", 1, 'ALERTS')

R("  const total = FEES.reduce((a,b)=>a+b.v,0);\n  const k1 = kpiCard('费用总额（月）','¥'+total+'万',2.1,'七大费用项合计','');\n  const k2 = kpiCard('综合费率',pct(COMPANY.month.feeRate),0.2,'费率红线 9.5%',COMPANY.month.feeRate>9?'red':'');\n  const k3 = kpiCard('推广费','¥62万',6.8,'ROI 2.3（红线 2.0）','gold');\n  const k4 = kpiCard('资金占用','¥21万',-1.2,'含后台费用','');\n  const rows = FEES.map(f=>`<tr><td class=\"t-name\">${esc(f.name)}</td><td>¥${f.v}万</td><td>${pct(f.v/total*100)}</td><td>${(f.v/total>0.25?'<span class=\"neg\">占比过高</span>':'合理')}</td></tr>`).join('');\n  return `<div class=\"metric-grid\">${k1}${k2}${k3}${k4}</div>\n    <div class=\"detail-panel\">\n      ${barsChart(FEES.map(f=>f.name), FEES.map(f=>f.v), FEES.map(f=>f.v*0.92), '当期', '上期', '万元')}\n      ${tableCard('费用结构明细（月度）','金额、占比与合理性判断',['费用项','金额','占比','判断'],rows)}\n    </div>\n    ${analysisCard('费用', {\n      concl:'月度费用 ¥357 万，综合费率 8.9%，控制在 9.5% 红线内；扣点租金占 35.3% 为最大科目。',\n      anom:'推广费环比 +6.8% 但整体 ROI 2.3 尚在红线之上；京东店投放 ROI 1.6 已破线。',\n      act:'① 京东店投放预算下调 20%，迁移至抖音店（ROI 2.9）；② 租金费率门店间差异大，纳入月度复盘；③ 费用数据 9 月起对接集合云费用模块自动取数。'\n    })}`;", "  const k1 = kpiCard('费用总额（月）','待接入',null,'需财务 8 月利润表','');\n  const k2 = kpiCard('综合费率','待接入',null,'费率红线 9.5%','');\n  const k3 = kpiCard('推广费','待接入',null,'待财务数据','gold');\n  const k4 = kpiCard('资金占用','待接入',null,'待财务数据','');\n  return `<div class=\"metric-grid\">${k1}${k2}${k3}${k4}</div>\n    ${analysisCard('费用（月度）', {\n      concl:'费用与费率数据待接入：需财务提供 8 月利润表（扣点租金/人工/推广/物流/资金占用/滞销计提）。',\n      anom:'当前无真实费用数据，暂不展示占比与合理性判断（原演示数据已移除）。',\n      act:'① 与财务确认 8 月利润表提供方式；② 数据到位后自动填充费用结构、综合费率与 ROI 判断。'\n    })}`;", 1, 'secOverviewFees')

R("kpiCard('营业利润（月）','¥186万',4.2,'利润率 7.9%','green')", "kpiCard('营业利润（月）','待接入',null,'需财务 8 月利润表','')", 1, 'profit1')
R("kpiCard('店铺利润合计','¥158万',3.8,'三大板块合计','')", "kpiCard('店铺利润合计','待接入',null,'待财务数据','')", 1, 'profit2')
R("kpiCard('净利率','3.4%（APR口径）',0.2,'高于经销商平均 3.1%','')", "kpiCard('净利率','待接入',null,'待财务数据','')", 1, 'profit3')
R("kpiCard('滞销/残次计提','¥9万',0.4,'资产减值损失','')", "kpiCard('滞销/残次计提','待接入',null,'待财务数据','')", 1, 'profit4')
R("concl:'月度营业利润 ¥186 万、利润率 7.9%，环比 +4.2%；毛利额 341 万覆盖费用 357 万后由其他收益补足。'", "concl:'利润数据待接入：需财务提供 8 月利润表（含营业利润/净利率/费用结构）。'", 1, 'profit5')
R("anom:'Apple 电商毛利率 9.6% 为三板块最低，主要受平台扣点与补贴影响。'", "anom:'当前毛利为直接毛利（分摊后金额-货品成本），未扣除费用；综合利润需财务利润表。'", 1, 'profit6')
R("act:'① Apple 电商以 1PP 结构优化与国补承接提升有效毛利率；② 舒尔板块毛利率 21.5% 保持内容投放加码；③ 月度利润表 9 月起由财务报表直接推送。'", "act:'① 与财务确认 8 月利润表提供方式；② 到数后自动填充利润板块。'", 1, 'profit7')

R("const k1 = kpiCard('月累计销售额', '¥'+totalSales.toFixed(0)+'万', 8.2, '10 店合计 · 目标 ¥2,180 万','green');", "const k1 = kpiCard('月累计销售额', '¥'+totalSales.toFixed(1)+'万', null, '10 店合计 · 目标 ¥2,180 万','green');", 1, 'aprk1')
R("const k2 = kpiCard('目标达成率', pct(APR_TOTAL.rate), null, '预测月末 '+APR_TOTAL.forecast_rate+'%','');", "const k2 = kpiCard('目标达成率', pct(APR_TOTAL.rate), null, APR_TOTAL.forecast_rate!=null?'预测月末 '+APR_TOTAL.forecast_rate+'%':'月度目标 ¥2,180 万','');", 1, 'aprk2')
R("const k4 = kpiCard('总转化率', pct(APR_TOTAL.conv), 0.8, '客流 '+APR_TOTAL.flow.toLocaleString()+' 人次','');", "const k4 = kpiCard('总转化率', pct(APR_TOTAL.conv), null, '客流 '+(APR_TOTAL.flow!=null?APR_TOTAL.flow.toLocaleString():'待接入')+' 人次','');", 1, 'aprk4')
R("const k5 = kpiCard('平均客单价', '¥2,430', 1.4, '日照最高 ¥3,363','gold');", "const k5 = kpiCard('平均客单价', '¥4,240', null, '彭城最高 ¥4,576','gold');", 1, 'aprk5')
R("const k6 = isMonth() ? kpiCard('人工费率', fee(5.8), -0.1, '低于经销商平均 6.3%','') : '';", "const k6 = isMonth() ? kpiCard('人工费率', fee(null), null, '财务费率数据待接入','') : '';", 1, 'aprk6')
R("${s.flow.toLocaleString()}", "${s.flow!=null?s.flow.toLocaleString():'待接入'}", 1, 'aprflow')
R("barsChart(['8-14','8-15','8-16','8-17','8-18','8-19','8-20'], [36.2,40.1,38.4,43.6,39.8,41.2,41.6], [4.5,5.1,4.9,5.6,5.0,5.2,5.3], '销售额', '毛利额', '万元')", "barsChart(['8-20','8-21','8-22','8-23','8-24','8-25','8-26'], [63.9,53.8,58.1,60.6,85.1,69.3,29.6], [2.57,1.43,1.97,1.2,2.15,2.19,1.46], '销售额', '毛利额', '万元')", 1, 'aprchart')
R("aiTip('10 店分化明显：日照达成 90%、徐州彭城 90.2% 领先；苏家屯 36.2% 垫底且同比 -12.4%。店间转化率相差 3 倍，能力标准化是 APR 最大的增长杠杆。')", "aiTip('10 店分化明显：日照达成 147.5%、彭城 128.3% 领先；苏家屯 60.1% 垫底且同比 -5.1%。店间达成差异大，产能标准化是 APR 最大的增长杠杆（客流/转化待接入）。')", 1, 'apraikit')
R("concl:'APR 板块 8 月累计销售 ¥'+totalSales.toFixed(0)+' 万、目标达成 '+pct(APR_TOTAL.rate)+'，日照（90%）与彭城（90.2%）领跑；全系转化率 6.4%，单店产能口径 ¥138,533 高于经销商平均 9.2%。'", "concl:'APR 板块 8/1-26 累计销售 ¥'+totalSales.toFixed(1)+' 万、目标达成 '+pct(APR_TOTAL.rate)+'；日照（147.5%）与彭城（128.3%）领跑；平均客单价 ¥4,240，彭城最高 ¥4,576。'", 1, 'aprconcl')
R("anom:'苏家屯达成 36.2% 且同比 -12.4%（客流与转化双低）；镇江苏宁重开后半程需冲刺；无锡店目标 ¥380 万为全系最高但达成仅 60.9%，需重点盯。'", "anom:'苏家屯达成 60.1% 且同比 -5.1% 为唯一负增长；镇江 62.8%、宝龙 73.4% 偏低；无锡店目标 ¥380 万为全系最高，达成 87.7%。'", 1, 'apranom')
R("act:'① 苏家屯：专项诊断落地（8/18 会议方案），iPhone 转化专项 8/21-27；② 镇江：开业红利期冲量，全员到岗+主推品补货；③ 无锡：旗舰店产能提升，连带话术+高毛利推荐复盘；④ 日照大单经验（客单 ¥3,363）提炼为话术包全系推广。'", "act:'① 苏家屯专项诊断（8/18 会议方案落地）；② 镇江开业红利期冲量至 8/31；③ 无锡旗舰店产能提升复盘；④ 日照大单经验（客单 ¥4,471）向全系复制。'", 1, 'apract')

R("APR_STORES.slice(0,6).map(s=>`<tr><td class=\"t-name\">${esc(s.name)}</td><td>¥${(s.sales*0.55).toFixed(1)}万</td><td>¥${(s.sales*0.45).toFixed(1)}万</td><td>55%</td></tr>`).join(''))}", "APR_STORES.slice(0,6).map(s=>`<tr><td class=\"t-name\">${esc(s.name)}</td><td>¥${s.off.toFixed(1)}万</td><td>¥${s.on.toFixed(1)}万</td><td>${(s.off/(s.off+s.on)*100).toFixed(1)}%</td></tr>`).join(''))}", 1, 'onofftable')

R("concl:'iPhone 占主机销售 71.7%（¥207万）为绝对主力；1PP 占比 68.2%（高于平均 2.8pp）；转化科四大机型 18.2% 全面优于经销商平均。'", "concl:'iPhone 占 APR 主机销售 77.7%（¥1,562.8 万）为绝对主力；主机合计 95.6%（iPhone+Mac+iPad+Watch）；APR 整体毛利率 3.10%（分摊后-成本直接毛利）。'", 1, 'saconcl')
R("anom:'同城激活率 98.1% 贴近 98% 红线（黄色关注，防串货）；ACS 连带率 28.6% 低于 30% 目标；3PP 规模小（¥10.2万）但手机配件占比 52.8% 结构健康。'", "anom:'APR 毛利率 3.10% 处于低位：线下 4.12% / 线上 O2O 仅 0.80%；3PP/配件结构数据待补全。'", 1, 'saanom')
R("act:'① 同城激活率每周核查一次异常订单归因；② ACS 连带话术纳入本周培训（目标 30%）；③ 五科数据 9 月起对接 Apple API 自动取数；④ 3PP 渠道按授权进度推进（当前暂未开展）。'", "act:'① 优化线上 O2O 毛利率（扣点与补贴结构）；② 3PP 配件销售按授权进度推进；③ 品类结构每日随明细账自动更新。'", 1, 'saact')

R("aiTip('TOP 销售员共性：线上销售占比高（王畅/鲁健线上均超 40%）、ACS 开口率高（查越/潘思源 75%）。日照李珍达成 53.3% 但线上占比 93%——线上渠道是个人产能放大器，建议全员复制线上打法。')", "aiTip('TOP 销售员：王畅 ¥162 万/达成 180% 居首；鲁健 ¥132 万、徐婷婷 ¥123 万紧随；高达成者多为线上占比高+主机台数多。')", 1, 'spai')
R("concl:'王畅以 ¥50.8万 居首（达成 56.5%），TOP5 中 3 人来自徐州/连云港；高达成者线上销售占比普遍较高。'", "concl:'王畅以 ¥162 万居首（达成 180%）；朱正波 ¥80.7 万/达成 107.6%；TOP5 中连云港/无锡各占 2 席。'", 1, 'spconcl')
R("anom:'连云港鲁健任务 ¥150万 为全员最高但达成仅 24%；日照李珍达成 53.3% 但毛利率 3.5% 偏低（配件率 0%）。'", "anom:'查越达成 85.6% 但毛利率 2.05% 偏低；田国伟达成 80.4% 低于 90 万+ 任务；ACS/配件金额等个人维度待接入。'", 1, 'spanom')
R("act:'① 线上打法（直播/企微/私域）标准化并全员培训；② 高任务低达成人员（鲁健等）一对一辅导；③ ACS 开口率低于 30% 人员纳入晨会话术演练重点。'", "act:'① 线上打法（企微/私域）标准化全员培训；② 高任务低达成人员（田国伟等）一对一辅导；③ 明早补个人客流/转化维度。'", 1, 'spact')

R("<div class=\"p-k\"><span>ACS 开口率</span><b>${p.acs}%</b></div>", "<div class=\"p-k\"><span>ACS 开口率</span><b>${p.acs!=null?p.acs+'%':'待接入'}</b></div>", 1, 'acsguard')
R("      ${p.acs<30?'ACS 开口率低于 30%，纳入晨会话术演练重点；':''}", "      ${(p.acs!=null&&p.acs<30)?'ACS 开口率低于 30%，纳入晨会话术演练重点；':''}", 1, 'acsguard2')
R("      ${p.pp===0||p.pp_amount_pct<3?'配件率偏低，加强连带推荐（目标 1PP ≥40%）；':''}", "      ${(p.pp===0||(p.pp_amount_pct!=null&&p.pp_amount_pct<3))?'配件率偏低，加强连带推荐（目标 1PP ≥40%）；':''}", 1, 'acsguard3')

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
print(); print('PART3 done, ok =', ok)