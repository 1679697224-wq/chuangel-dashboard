# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("{ name:'徐州彭城店', sales:436.12, task:340, pm:3.46, profit:15.08, flow:null, conv:null,", "{ name:'徐州彭城店', sales:436.12, task:340, pm:3.46, profit:15.08, flow:20804, conv:4.58,", 1, 'flow:1')
R("{ name:'无锡店', sales:333.39, task:380, pm:3.03, profit:10.09, flow:null, conv:null,", "{ name:'无锡店', sales:333.39, task:380, pm:3.03, profit:10.09, flow:12303, conv:6.22,", 1, 'flow:2')
R("{ name:'连云港店', sales:310.07, task:340, pm:3.27, profit:10.14, flow:null, conv:null,", "{ name:'连云港店', sales:310.07, task:340, pm:3.27, profit:10.14, flow:8913, conv:8.12,", 1, 'flow:3')
R("{ name:'太原店', sales:174.34, task:210, pm:2.24, profit:3.90, flow:null, conv:null,", "{ name:'太原店', sales:174.34, task:210, pm:2.24, profit:3.90, flow:3584, conv:11.44,", 1, 'flow:4')
R("{ name:'宿州店', sales:175.69, task:180, pm:3.29, profit:5.78, flow:null, conv:null,", "{ name:'宿州店', sales:175.69, task:180, pm:3.29, profit:5.78, flow:6455, conv:6.60,", 1, 'flow:5')
R("{ name:'镇江店', sales:150.74, task:240, pm:4.42, profit:6.66, flow:null, conv:null,", "{ name:'镇江店', sales:150.74, task:240, pm:4.42, profit:6.66, flow:8248, conv:4.84,", 1, 'flow:6')
R("{ name:'运城店', sales:155.45, task:170, pm:3.14, profit:4.89, flow:null, conv:null,", "{ name:'运城店', sales:155.45, task:170, pm:3.14, profit:4.89, flow:6528, conv:6.10,", 1, 'flow:7')
R("{ name:'日照店', sales:118.02, task:80, pm:1.37, profit:1.62, flow:null, conv:null,", "{ name:'日照店', sales:118.02, task:80, pm:1.37, profit:1.62, flow:2545, conv:10.37,", 1, 'flow:8')
R("{ name:'徐州宝龙店', sales:73.43, task:100, pm:2.82, profit:2.07, flow:null, conv:null,", "{ name:'徐州宝龙店', sales:73.43, task:100, pm:2.82, profit:2.07, flow:2024, conv:9.68,", 1, 'flow:9')
R("{ name:'苏家屯店', sales:84.17, task:140, pm:2.49, profit:2.10, flow:null, conv:null,", "{ name:'苏家屯店', sales:84.17, task:140, pm:2.49, profit:2.10, flow:3510, conv:5.95,", 1, 'flow:10')
R("let APR_TOTAL = { sales: 2011.4, task: 2180, profit: 62.33, flow: null, conv: null, pm: 3.10, rate: 92.3, forecast_rate: null };", "let APR_TOTAL = { sales: 2011.4, task: 2180, profit: 62.33, flow: 74914, conv: 6.33, pm: 3.10, rate: 92.3, forecast_rate: null };", 1, 'APR_TOTAL客流')
R("线下（APR 整体）</td><td>${fmtY(mul(COMPANY.day.sales*off/100))}</td><td>${pct(off)}</td><td>待接入</td><td>客流 待接入（接口）</td><td>待接入</td></tr>", "线下（APR 整体）</td><td>${fmtY(mul(COMPANY.day.sales*off/100))}</td><td>${pct(off)}</td><td>${pct(APR_TOTAL.conv)}</td><td>客流 ${APR_TOTAL.flow.toLocaleString()} 人次</td><td>待接入</td></tr>", 1, '线上线下行线下')
R("线下（APR 门店）</td><td>${fmtY(mul(COMPANY.day.sales*off/100))}</td><td>${pct(off)}</td><td>待接入</td><td>客流 待接入（接口）</td><td>待接入</td></tr>", "线下（APR 门店）</td><td>${fmtY(mul(COMPANY.day.sales*off/100))}</td><td>${pct(off)}</td><td>${pct(APR_TOTAL.conv)}</td><td>客流 ${APR_TOTAL.flow.toLocaleString()} 人次</td><td>待接入</td></tr>", 1, '线上线下行线下2')
R("      anom:'线上综合转化率待接入（明早平台导出）；APR 门店转化率待接入（客流接口）；苏家屯同比 -5.1% 为唯一负增长门店。',", "      anom:'线上综合转化率待接入（明早平台导出）；APR 进店客流 74,914 人次/转化 6.33%（镇江仅15天重开）；苏家屯同比 -5.1% 为唯一负增长门店。',", 2, '占比anom')
R("aiTip('10 店分化明显：日照达成 147.5%、彭城 128.3% 领先；苏家屯 60.1% 垫底且同比 -5.1%。店间达成差异大，产能标准化是 APR 最大的增长杠杆（客流/转化待接入）。')", "aiTip('10 店分化明显：日照达成 147.5%、彭城 128.3% 领先；苏家屯 60.1% 垫底且同比 -5.1%。进店客流合计 74,914 人次/转化 6.33%，太原 11.4% 最高、彭城 4.6% 偏低，转化提升空间大。')", 1, 'APR aiTip')
R("      concl:'APR 板块 8/1-26 累计销售 ¥'+totalSales.toFixed(1)+' 万、目标达成 '+pct(APR_TOTAL.rate)+'；日照（147.5%）与彭城（128.3%）领跑；平均客单价 ¥4,240，彭城最高 ¥4,576。',", "      concl:'APR 板块 8/1-26 累计销售 ¥'+totalSales.toFixed(1)+' 万、目标达成 '+pct(APR_TOTAL.rate)+'；进店客流 74,914 人次、转化率 '+pct(APR_TOTAL.conv)+'；日照（147.5%）与彭城（128.3%）达成领先。',", 1, 'APR concl')
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
print(); print('PART16 done, ok =', ok)