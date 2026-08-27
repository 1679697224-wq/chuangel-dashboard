# -*- coding: utf-8 -*-
"""将真实数据填入 boss-dashboard-v6.html（仅数据与文案，不改版式）"""
import io, sys

P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding="utf-8").read()

REPS = []

def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))

# ---------- 1) 辅助函数 null 安全 ----------
R("function fmtWan(v){ return v>=10000 ? (v/10000).toFixed(v>=1000000?0:1)+'万' : Math.round(v).toLocaleString(); }",
  "function fmtWan(v){ if(v==null) return '待接入'; return v>=10000 ? (v/10000).toFixed(v>=1000000?0:1)+'万' : Math.round(v).toLocaleString(); }", 1, "fmtWan")
R("function pct(v,d=1){ return v.toFixed(d)+'%'; }",
  "function pct(v,d=1){ return v==null?'待接入':v.toFixed(d)+'%'; }", 1, "pct")
R("function fee(v, suffix){ return isMonth() ? (typeof v==='number' ? v.toFixed(1)+'%' : v) : '-' ; }",
  "function fee(v, suffix){ if(v==null) return isMonth()?'待接入':'-'; return isMonth() ? (typeof v==='number' ? v.toFixed(1)+'%' : v) : '-' ; }", 1, "fee")
R(">演示数据<", ">8月累计<", 4, "tag演示数据")

# ---------- 2) 数据对象 ----------
R("""const COMPANY = {
  day:{ sales:826500, target:780000, gross:118402, gpm:14.3, feeRate:8.7, cvr:9.6, aov:5230, d7:-6.2, w0:4.8, yoy:3.1, onlineShare:38.6, offlineShare:61.4 },
  week:{ sales:5483600, target:5460000, gross:792300, gpm:14.4, feeRate:8.8, cvr:9.4, aov:5180, d7:3.2, w0:1.1, yoy:4.2, onlineShare:39.2, offlineShare:60.8 },
  month:{ sales:23518000, target:24600000, gross:3411000, gpm:14.5, feeRate:8.9, cvr:9.5, aov:5210, d7:5.6, w0:2.3, yoy:5.1, onlineShare:40.5, offlineShare:59.5 }
};""",
"""const COMPANY = {
  day:{ sales:1092138, target:2347055, gross:47603, gpm:4.36, feeRate:null, cvr:null, aov:4395, d7:null, w0:null, yoy:45.8, onlineShare:56.3, offlineShare:43.7 },
  week:{ sales:7535752, target:16195890, gross:328461, gpm:4.36, feeRate:null, cvr:null, aov:4395, d7:null, w0:null, yoy:45.8, onlineShare:56.3, offlineShare:43.7 },
  month:{ sales:31890428, target:68534000, gross:1390009, gpm:4.36, feeRate:null, cvr:null, aov:4395, d7:null, w0:null, yoy:45.8, onlineShare:56.3, offlineShare:43.7 }
};""", 1, "COMPANY")

R("const TREND7 = { labels:['8-14','8-15','8-16','8-17','8-18','8-19','8-20'], sales:[71.2,78.6,74.3,82.1,75.9,77.8,82.7], gross:[9.8,11.4,10.6,11.9,10.8,11.2,11.8], lastYear:[68.9,75.4,71.8,79.6,73.2,75.1,80.2] };",
  "const TREND7 = { labels:['8-20','8-21','8-22','8-23','8-24','8-25','8-26'], sales:[77.8,69.2,69.4,89.5,126.6,105.9,48.7], gross:[4.76,3.71,2.73,2.4,4.15,37.54,20.69], lastYear:[47.4,35.0,46.3,62.3,55.1,71.3,56.6] };", 1, "TREND7")

R("""const SEGMENTS = [
  { name:'APR（整体）', code:'APR', sales:415600, gross:53197, gpm:12.8, cvr:22.4, feeRate:6.2, inv:2460, d7:8.2, yoy:4.6, onlineShare:6.8, offlineShare:93.2, note:'10 家门店 · 含线上线下整体' },
  { name:'Apple 电商', code:'AE', sales:298200, gross:28627, gpm:9.6, cvr:2.8, feeRate:11.8, inv:1580, d7:-3.4, yoy:2.1, onlineShare:100, offlineShare:0, note:'3 家店铺' },
  { name:'Shure 电商', code:'SH', sales:112700, gross:24231, gpm:21.5, cvr:1.9, feeRate:13.5, inv:320, d7:12.6, yoy:8.9, onlineShare:100, offlineShare:0, note:'2 家店铺' }
];""",
"""const SEGMENTS = [
  { name:'APR（整体）', code:'APR', sales:688842, gross:21345, gpm:3.10, cvr:null, feeRate:null, inv:1442.6, d7:null, yoy:72.8, onlineShare:30.7, offlineShare:69.3, note:'10 家门店 · 含线上线下整体' },
  { name:'Apple 电商', code:'AE', sales:367479, gross:18294, gpm:4.98, cvr:null, feeRate:null, inv:367.5, d7:null, yoy:89.2, onlineShare:100, offlineShare:0, note:'京东羽通/苏宁啟韬/响誉' },
  { name:'Shure 电商', code:'SH', sales:24708, gross:7489, gpm:30.31, cvr:null, feeRate:null, inv:229.5, d7:null, yoy:15.5, onlineShare:100, offlineShare:0, note:'天猫（吉客云口径）' },
  { name:'分销/其他', code:'OTH', sales:11108, gross:475, gpm:4.27, cvr:null, feeRate:null, inv:0, d7:null, yoy:-88.9, onlineShare:0, offlineShare:100, note:'分销 + 天羽乐购' }
];""", 1, "SEGMENTS")

R("""const GOALS = [
  { name:'公司整体', target:24600000, done:14306000, time:64.5 },
  { name:'APR 门店', target:12600000, done:7620000, time:64.5 },
  { name:'Apple 电商', target:8600000, done:4790000, time:64.5 },
  { name:'Shure电商', target:3400000, done:1896000, time:64.5 }
];""",
"""const GOALS = [
  { name:'公司整体', target:68534000, done:31890428, time:83.9 },
  { name:'APR 门店', target:21800000, done:20114197, time:83.9 },
  { name:'Apple 电商', target:40416000, done:10730377, time:83.9 },
  { name:'Shure电商', target:4300000, done:721479, time:83.9 }
];""", 1, "GOALS")

R("""let APR_STORES = [
  { name:'徐州彭城店', sales:306.8, task:340, pm:8.59, profit:11.72, flow:10356, conv:5.0, apt:2981.7, inv:920, d7:8.2, yoy:6.1, rate:90.2 },
  { name:'无锡店', sales:231.6, task:380, pm:8.83, profit:7.18, flow:4157, conv:8.6, apt:2580.5, inv:810, d7:-3.1, yoy:2.3, rate:60.9 },
  { name:'连云港店', sales:222.4, task:340, pm:9.44, profit:5.81, flow:3922, conv:7.0, apt:2521.9, inv:730, d7:4.6, yoy:7.4, rate:65.4 },
  { name:'太原店', sales:126.9, task:210, pm:9.65, profit:2.0, flow:1650, conv:8.5, apt:1677.5, inv:560, d7:-1.2, yoy:-2.8, rate:60.4 },
  { name:'宿州店', sales:121.0, task:180, pm:7.05, profit:3.62, flow:3187, conv:8.2, apt:2226.0, inv:480, d7:5.8, yoy:9.2, rate:67.2 },
  { name:'镇江店', sales:101.6, task:240, pm:9.9, profit:3.12, flow:1409, conv:9.2, apt:2744.5, inv:390, d7:12.4, yoy:15.6, rate:42.3 },
  { name:'运城店', sales:99.2, task:170, pm:7.37, profit:1.99, flow:2946, conv:4.7, apt:2208.3, inv:350, d7:3.3, yoy:4.9, rate:58.4 },
  { name:'日照店', sales:72.0, task:80, pm:10.15, profit:1.72, flow:613, conv:9.3, apt:3363.3, inv:190, d7:-4.5, yoy:-1.8, rate:90.0 },
  { name:'徐州宝龙店', sales:56.9, task:100, pm:8.08, profit:1.14, flow:1018, conv:5.2, apt:2993.7, inv:150, d7:2.1, yoy:-6.3, rate:56.9 },
  { name:'苏家屯店', sales:50.6, task:140, pm:8.9, profit:0.69, flow:1575, conv:2.9, apt:1916.0, inv:120, d7:-8.9, yoy:-12.4, rate:36.2 }
];""",
"""let APR_STORES = [
  { name:'徐州彭城店', sales:436.12, task:340, pm:3.46, profit:15.08, flow:null, conv:null, apt:4576, inv:140.6, d7:null, yoy:112.7, rate:128.3, off:315.58, on:120.54 },
  { name:'无锡店', sales:333.39, task:380, pm:3.03, profit:10.09, flow:null, conv:null, apt:4358, inv:121.8, d7:null, yoy:67.8, rate:87.7, off:234.83, on:98.56 },
  { name:'连云港店', sales:310.07, task:340, pm:3.27, profit:10.14, flow:null, conv:null, apt:4283, inv:155.3, d7:null, yoy:113.7, rate:91.2, off:203.89, on:106.18 },
  { name:'太原店', sales:174.34, task:210, pm:2.24, profit:3.90, flow:null, conv:null, apt:4252, inv:83.5, d7:null, yoy:79.1, rate:83.0, off:96.14, on:78.21 },
  { name:'宿州店', sales:175.69, task:180, pm:3.29, profit:5.78, flow:null, conv:null, apt:4124, inv:97.3, d7:null, yoy:32.1, rate:97.6, off:130.17, on:45.52 },
  { name:'镇江店', sales:150.74, task:240, pm:4.42, profit:6.66, flow:null, conv:null, apt:3778, inv:78.7, d7:null, yoy:23.6, rate:62.8, off:109.37, on:41.37 },
  { name:'运城店', sales:155.45, task:170, pm:3.14, profit:4.89, flow:null, conv:null, apt:3906, inv:95.9, d7:null, yoy:157.9, rate:91.4, off:108.30, on:47.16 },
  { name:'日照店', sales:118.02, task:80, pm:1.37, profit:1.62, flow:null, conv:null, apt:4471, inv:79.1, d7:null, yoy:86.2, rate:147.5, off:84.67, on:33.35 },
  { name:'徐州宝龙店', sales:73.43, task:100, pm:2.82, profit:2.07, flow:null, conv:null, apt:3746, inv:77.2, d7:null, yoy:17.4, rate:73.4, off:48.37, on:25.06 },
  { name:'苏家屯店', sales:84.17, task:140, pm:2.49, profit:2.10, flow:null, conv:null, apt:4027, inv:92.7, d7:null, yoy:-5.1, rate:60.1, off:62.16, on:22.00 }
];""", 1, "APR_STORES")

R("let APR_TOTAL = { sales: 1388.9, task: 2180, profit: 38.99, flow: 30833, conv: 6.4, pm: 7.99, rate: 63.9 };",
  "let APR_TOTAL = { sales: 2011.4, task: 2180, profit: 62.33, flow: null, conv: null, pm: 3.10, rate: 92.3, forecast_rate: null };", 1, "APR_TOTAL")

R("""let SALESPERSONS = [
  {rank:1,name:'王畅',store:'徐州店',pos:'店员',sales:50.8,task:90,rate:56.5,offline:31.5,online:19.3,pm:6.9,host:41,pp:43,acs:45.8,profit:2.2,profit_rank:1,pp_rate:54.2,pp_sales:1.7,offline_profit_rate:53.0,high_sell:1.9},
  {rank:2,name:'鲁健',store:'连云港店',pos:'店员',sales:36.1,task:150,rate:24.0,offline:13.2,online:22.9,pm:8.6,host:16,pp:19,acs:30.0,profit:1.1,profit_rank:2,pp_rate:9.1,pp_sales:0.4,offline_profit_rate:19.0,high_sell:0.0},
  {rank:3,name:'袁兆行',store:'无锡店',pos:'店员',sales:30.5,task:95,rate:32.1,offline:10.0,online:20.5,pm:7.6,host:13,pp:17,acs:37.5,profit:0.8,profit_rank:5,pp_rate:8.5,pp_sales:0.3,offline_profit_rate:18.8,high_sell:0.0},
  {rank:4,name:'田国伟',store:'太原店',pos:'店员',sales:28.6,task:105,rate:27.3,offline:5.0,online:23.6,pm:9.1,host:8,pp:14,acs:50.0,profit:0.5,profit_rank:10,pp_rate:6.9,pp_sales:0.1,offline_profit_rate:17.5,high_sell:0.0},
  {rank:5,name:'蒋玉玄',store:'运城店',pos:'店员',sales:26.5,task:90,rate:29.4,offline:6.4,online:20.1,pm:6.8,host:10,pp:13,acs:25.0,profit:0.4,profit_rank:12,pp_rate:8.5,pp_sales:0.2,offline_profit_rate:16.8,high_sell:0.0},
  {rank:6,name:'查越',store:'太原店',pos:'店员',sales:25.4,task:105,rate:24.2,offline:5.7,online:19.7,pm:7.9,host:9,pp:20,acs:75.0,profit:0.5,profit_rank:11,pp_rate:10.8,pp_sales:0.2,offline_profit_rate:17.4,high_sell:0.0},
  {rank:7,name:'徐婷婷',store:'连云港店',pos:'店员',sales:24.4,task:150,rate:16.2,offline:5.6,online:18.8,pm:7.3,host:8,pp:12,acs:0.0,profit:0.4,profit_rank:14,pp_rate:7.0,pp_sales:0.3,offline_profit_rate:6.8,high_sell:0.0},
  {rank:8,name:'秦子杰',store:'徐州店',pos:'店员',sales:23.5,task:75,rate:31.4,offline:7.5,online:16.0,pm:7.0,host:10,pp:7,acs:28.6,profit:0.5,profit_rank:8,pp_rate:8.1,pp_sales:0.2,offline_profit_rate:15.5,high_sell:1.8},
  {rank:9,name:'潘思源',store:'无锡店',pos:'店员',sales:21.4,task:95,rate:22.5,offline:5.1,online:16.3,pm:7.9,host:7,pp:12,acs:75.0,profit:0.4,profit_rank:15,pp_rate:6.2,pp_sales:0.2,offline_profit_rate:9.7,high_sell:0.0},
  {rank:10,name:'李珍',store:'日照店',pos:'店员',sales:21.3,task:40,rate:53.3,offline:1.4,online:19.9,pm:3.5,host:4,pp:0,acs:0.0,profit:0.1,profit_rank:25,pp_rate:0.0,pp_sales:0.0,offline_profit_rate:4.3,high_sell:0.0}
];""",
"""let SALESPERSONS = [
  {rank:1,name:'王畅',store:'徐州彭城店',pos:'店员',sales:161.98,task:90,rate:180.0,offline:118.46,online:43.52,pm:3.91,host:280,pp:210,acs:null,profit:6.33,profit_rank:1,pp_rate:null,pp_sales:null,offline_profit_rate:null,high_sell:null,pp_amount_pct:null},
  {rank:2,name:'朱正波',store:'徐州宝龙店',pos:'店员',sales:80.66,task:75,rate:107.6,offline:62.88,online:17.79,pm:5.16,host:144,pp:107,acs:null,profit:4.16,profit_rank:2,pp_rate:null,pp_sales:null,offline_profit_rate:null,high_sell:null,pp_amount_pct:null},
  {rank:3,name:'鲁健',store:'连云港店',pos:'店员',sales:131.78,task:150,rate:87.9,offline:90.05,online:41.73,pm:3.09,host:222,pp:180,acs:null,profit:4.07,profit_rank:3,pp_rate:null,pp_sales:null,offline_profit_rate:null,high_sell:null,pp_amount_pct:null},
  {rank:4,name:'徐婷婷',store:'连云港店',pos:'店员',sales:122.57,task:150,rate:81.7,offline:74.79,online:47.77,pm:3.21,host:202,pp:147,acs:null,profit:3.93,profit_rank:4,pp_rate:null,pp_sales:null,offline_profit_rate:null,high_sell:null,pp_amount_pct:null},
  {rank:5,name:'袁兆行',store:'无锡店',pos:'店员',sales:109.51,task:95,rate:115.3,offline:79.73,online:29.78,pm:2.90,host:175,pp:118,acs:null,profit:3.17,profit_rank:5,pp_rate:null,pp_sales:null,offline_profit_rate:null,high_sell:null,pp_amount_pct:null},
  {rank:6,name:'蒋玉玄',store:'运城店',pos:'店员',sales:83.55,task:90,rate:92.8,offline:57.36,online:26.20,pm:3.42,host:148,pp:91,acs:null,profit:2.86,profit_rank:6,pp_rate:null,pp_sales:null,offline_profit_rate:null,high_sell:null,pp_amount_pct:null},
  {rank:7,name:'白国良',store:'无锡店',pos:'店员',sales:81.60,task:95,rate:85.9,offline:52.78,online:28.82,pm:3.49,host:144,pp:113,acs:null,profit:2.85,profit_rank:7,pp_rate:null,pp_sales:null,offline_profit_rate:null,high_sell:null,pp_amount_pct:null},
  {rank:8,name:'杨明',store:'无锡店',pos:'店员',sales:86.84,task:95,rate:91.4,offline:64.91,online:21.93,pm:2.87,host:156,pp:109,acs:null,profit:2.49,profit_rank:8,pp_rate:null,pp_sales:null,offline_profit_rate:null,high_sell:null,pp_amount_pct:null},
  {rank:9,name:'田国伟',store:'太原店',pos:'店员',sales:84.44,task:105,rate:80.4,offline:43.76,online:40.68,pm:2.45,host:134,pp:92,acs:null,profit:2.07,profit_rank:9,pp_rate:null,pp_sales:null,offline_profit_rate:null,high_sell:null,pp_amount_pct:null},
  {rank:10,name:'查越',store:'太原店',pos:'店员',sales:89.90,task:105,rate:85.6,offline:52.37,online:37.53,pm:2.05,host:144,pp:100,acs:null,profit:1.84,profit_rank:10,pp_rate:null,pp_sales:null,offline_profit_rate:null,high_sell:null,pp_amount_pct:null}
];""", 1, "SALESPERSONS")

R("""let APR_STRUCTURE = [
  { name:'iPhone', pct:71.7, amount:206.95, color:'#2f69c2' },
  { name:'Mac', pct:12.2, amount:35.25, color:'#64a4da' },
  { name:'Watch', pct:8.4, amount:24.15, color:'#c79118' },
  { name:'iPad', pct:7.7, amount:22.33, color:'#7b91ad' }
];""",
"""let APR_STRUCTURE = [
  { name:'iPhone', pct:77.7, amount:1562.8, color:'#2f69c2' },
  { name:'Mac', pct:5.8, amount:117.1, color:'#64a4da' },
  { name:'iPad', pct:5.2, amount:104.3, color:'#7b91ad' },
  { name:'Watch', pct:6.9, amount:139.3, color:'#c79118' },
  { name:'AirPods+其他', pct:4.4, amount:88.0, color:'#42a287' }
];""", 1, "APR_STRUCTURE")

R("""const AE_STORES = [
  { name:'天猫旗舰店', sales:148600, gpm:9.2, gross:13671, uv:22100, cvr:2.6, refund:2.9, d7:5.4, yoy:3.8 },
  { name:'京东旗舰店', sales:109800, gpm:10.1, gross:11090, uv:13400, cvr:3.1, refund:2.4, d7:-8.7, yoy:-2.1 },
  { name:'抖音专卖店', sales:39800, gpm:9.8, gross:3900, uv:7100, cvr:2.1, refund:3.4, d7:18.2, yoy:9.6 }
];""",
"""const AE_STORES = [
  { name:'京东旗舰店（羽通）', sales:145332, gpm:9.92, gross:14417, uv:null, cvr:null, refund:null, d7:null, yoy:null },
  { name:'苏宁旗舰店（啟韬）', sales:220880, gpm:2.48, gross:5478, uv:null, cvr:null, refund:null, d7:null, yoy:null },
  { name:'天猫旗舰店（响誉）', sales:58, gpm:null, gross:58, uv:null, cvr:null, refund:null, d7:null, yoy:null }
];""", 1, "AE_STORES")

R("""const SH_STORES = [
  { name:'京东旗舰店', sales:72400, gpm:22.1, gross:16002, uv:5900, cvr:2.1, refund:1.8, d7:9.8, yoy:7.2 },
  { name:'天猫旗舰店', sales:40300, gpm:20.7, gross:8342, uv:3900, cvr:1.6, refund:2.2, d7:16.4, yoy:11.8 }
];""",
"""const SH_STORES = [
  { name:'京东旗舰店', sales:24726, gpm:null, gross:0, uv:24172, cvr:3.15, refund:null, d7:null, yoy:null },
  { name:'天猫旗舰店', sales:24709, gpm:30.31, gross:7489, uv:null, cvr:null, refund:null, d7:null, yoy:null }
];""", 1, "SH_STORES")

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
print("PART1 done, ok =", ok)
