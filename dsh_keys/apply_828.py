# -*- coding: utf-8 -*-
import json, io, re
ROOT = "/Users/lili/Desktop/deepseek harness/吉客云数据"
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
F = json.load(open(ROOT + '/api_fill_828.json', encoding='utf-8'))
S = F['sales']
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, name=''):
    REPS.append((old, new, name))

# 1) SEGMENTS
R("""const SEGMENTS = [
  { name:'APR（整体）', code:'APR', sales:688842, gross:21345, gpm:3.10, cvr:6.33, feeRate:null, inv:1442.6, d7:null, yoy:72.8, onlineShare:30.7, offlineShare:69.3, note:'10 家门店 · 含线上线下整体' },
  { name:'Apple 电商', code:'AE', sales:367479, gross:18294, gpm:4.98, cvr:null, feeRate:null, inv:367.5, d7:null, yoy:89.2, onlineShare:100, offlineShare:0, note:'啟韬(苏宁)+羽通(京东)·其余 3.7 万未细分',
    stores:[
      { name:'苏宁旗舰店（啟韬）', sales:220880, gross:5478, gpm:2.48, cvr:null, feeRate:null, inv:103.5, d7:null, yoy:null, src:'吉客云自动' },
      { name:'京东旗舰店（羽通）', sales:145332, gross:14418, gpm:9.92, cvr:null, feeRate:null, inv:264.0, d7:null, yoy:null, src:'吉客云自动' }
    ] },
  { name:'Shure 电商', code:'SH', sales:24708, gross:7489, gpm:30.31, cvr:null, feeRate:null, inv:229.5, d7:null, yoy:15.5, onlineShare:100, offlineShare:0, note:'天猫72.15(吉客云)+京东74.73(日报)另计',
    stores:[
      { name:'天猫旗舰店', sales:24709, gross:7489, gpm:30.31, cvr:null, feeRate:null, inv:137.3, d7:null, yoy:15.5, src:'吉客云自动' },
      { name:'京东旗舰店（另计）', sales:24726, gross:0, gpm:null, cvr:3.15, feeRate:null, inv:92.2, d7:null, yoy:null, src:'平台日报·手工' }
    ] },
  { name:'分销/其他', code:'OTH', sales:11108, gross:475, gpm:4.27, cvr:null, feeRate:null, inv:0, d7:null, yoy:-88.9, onlineShare:0, offlineShare:100, note:'分销 + 天羽乐购' }
];""",
"""const SEGMENTS = [
  { name:'APR（整体）', code:'APR', sales:635037, gross:49271, gpm:3.57, cvr:5.70, feeRate:null, inv:987, d7:null, yoy:120.2, onlineShare:27.2, offlineShare:72.8, note:'10 家门店 · 含线上线下整体' },
  { name:'Apple 电商', code:'AE', sales:360810, gross:0, gpm:5.07, cvr:null, feeRate:null, inv:318, d7:null, yoy:89.2, onlineShare:100, offlineShare:0, note:'啟韬(苏宁)+羽通(京东) 实付口径' },
  { name:'Shure 电商', code:'SH', sales:20754, gross:0, gpm:30.31, cvr:null, feeRate:null, inv:135, d7:null, yoy:15.5, onlineShare:100, offlineShare:0, note:'天猫(API实付)+京东(日报)另计' },
  { name:'分销/其他', code:'OTH', sales:15401, gross:0, gpm:0, cvr:null, feeRate:null, inv:0, d7:null, yoy:null, onlineShare:0, offlineShare:100, note:'分销+天羽乐购+3PP' }
];""", 'SEGMENTS')

# 2) GOALS
R("""const GOALS = [
  { name:'公司整体', target:68534000, done:31890428, time:83.9 },
  { name:'APR 门店', target:21800000, done:20114197, time:83.9 },
  { name:'Apple 电商', target:40416000, done:10730377, time:83.9 },
  { name:'Shure电商', target:4300000, done:721479, time:83.9 }
];""",
"""const GOALS = [
  { name:'公司整体', target:68534000, done:30134400, time:87.1 },
  { name:'APR 门店', target:21800000, done:18543100, time:87.1 },
  { name:'Apple 电商', target:40416000, done:10535600, time:87.1 },
  { name:'Shure电商', target:4300000, done:1377388, time:87.1 }
];""", 'GOALS')

# 3) APR_TOTAL
R("let APR_TOTAL = { sales: 2011.4, task: 2180, profit: 62.33, flow: 74914, conv: 6.33, pm: 3.10, rate: 92.3, forecast_rate: null };",
  "let APR_TOTAL = { sales: 1854.31, task: 2180, profit: 66.21, flow: 77364, conv: 5.70, pm: 3.57, rate: 85.1, forecast_rate: null };", 'APR_TOTAL')

# 4) TREND7
R("const TREND7 = { labels:['8-20','8-21','8-22','8-23','8-24','8-25','8-26'], sales:[77.8,69.2,69.4,89.5,126.6,105.9,48.7], gross:[4.76,3.71,2.73,2.4,4.15,37.54,20.69], lastYear:[47.4,35.0,46.3,62.3,55.1,71.3,56.6] };",
  "const TREND7 = { labels:['8-21','8-22','8-23','8-24','8-25','8-26','8-27'], sales:[14.33,68.37,86.26,131.6,74.29,69.92,90.95], gross:[0.68,3.24,4.09,6.24,3.52,3.31,4.31], lastYear:[34.98,46.34,62.29,55.12,71.34,56.59,0.0] };", 'TREND7')

# 5) AE
R("""const AE_STORES = [
  { name:'苏宁旗舰店（啟韬）', sales:220880, gpm:2.48, gross:5478, uv:null, cvr:null, refund:null, d7:null, yoy:null, task:901.47, rate:71.6, src:'吉客云自动' },
  { name:'京东旗舰店（羽通）', sales:145332, gpm:9.92, gross:14418, uv:null, cvr:null, refund:null, d7:null, yoy:null, task:3140.13, rate:13.5, src:'吉客云自动' }
];""",
"""const AE_STORES = [
  { name:'苏宁旗舰店（啟韬）', sales:22039, gpm:2.48, gross:0, uv:null, cvr:null, refund:null, d7:null, yoy:null, task:901.47, rate:71.4, src:'吉客云 API' },
  { name:'京东旗舰店（羽通）', sales:12541, gpm:9.92, gross:0, uv:null, cvr:null, refund:null, d7:null, yoy:null, task:3140.13, rate:11.7, src:'吉客云 API' }
];""", 'AE')

# 6) SH
R("""const SH_STORES = [
  { name:'天猫旗舰店', sales:24709, gpm:30.31, gross:7489, uv:90841, cvr:0.88, refund:null, d7:null, yoy:15.5, task:220, rate:32.8, src:'吉客云自动' },
  { name:'京东旗舰店', sales:25592, gpm:null, gross:0, uv:25117, cvr:3.12, refund:null, d7:null, yoy:null, task:210, rate:35.6, orders:783, aov:954, src:'平台日报·手工' }
];""",
"""const SH_STORES = [
  { name:'天猫旗舰店', sales:20754, gpm:30.31, gross:0, uv:92331, cvr:0.90, refund:null, d7:null, yoy:15.5, task:220, rate:27.5, src:'吉客云 API' },
  { name:'京东旗舰店', sales:26417, gpm:null, gross:0, uv:26074, cvr:3.11, refund:null, d7:null, yoy:null, task:210, rate:36.7, orders:812, aov:950, src:'平台日报·手工' }
];""", 'SH')

# 7) INV 顶部
R("let INV_BIZ = {\n  total_amount: 2108.85,           // 库存总额（万元，总览口径含在途 · 商务表260826）\n  total_skus: 6243,                // 库存明细行数",
  "let INV_BIZ = {\n  total_amount: 1925.77,           // 库存总额（万元，吉客云 API 现存量 8/28）\n  total_skus: 74286,               // 现存量 SKU 行数", 'INV')

# 8) 日期 + aiTip
R("数据日期 2026-08-26<small>更新于 24:00 · 真实数据（8/1-26）· 流量/费率待接入</small>",
  "数据日期 2026-08-27<small>更新于 24:00 · 吉客云 API 口径（8/1-27）</small>", '日期')
R("aiTip('8/1-26 已支付销售额 <b>¥3,189 万</b>（分摊后口径），同比 +45.8%；APR 板块贡献 63.1% 为增长主引擎；Apple 电商分店：啟韬 71.6% / 羽通 13.5%，目标口径需运营确认；京东舒尔 74.73 万（平台日报）另计，含入后公司约 3,264 万。')",
  "aiTip('8/1-27 销售额 <b>¥3,013 万</b>（吉客云 API 实付口径），同比 +47.6%；APR 贡献 61.5%；京东舒尔 77.14 万（日报）另计。')", 'aiTip')

ok = True
for old, new, name in REPS:
    n = src.count(old)
    if n != 1:
        print('MISS[%s]: %d' % (name, n))
        ok = False
    else:
        src = src.replace(old, new)
        print('ok[%s]' % name)
io.open(P, 'w', encoding='utf-8').write(src)
print('DONE ok =', ok)
