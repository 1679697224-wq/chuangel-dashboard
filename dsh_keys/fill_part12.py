# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("function applyLive(d){\n  if(!d || !d.apr) return;\n  // APR 整体\n  const a = d.apr;\n  APR_TOTAL = { sales:a.sales, task:a.task, profit:a.profit, flow:a.traffic, conv:a.conv, pm:a.pm, rate:a.rate };\n  // 10 店（保留内嵌的 inv/d7/yoy 展示字段）\n  const oldMap = {}; APR_STORES.forEach(s=>oldMap[s.name]=s);\n  APR_STORES = (a.stores||[]).map(s=>({\n    name:s.name, sales:s.sales, task:s.task, pm:s.pm, profit:s.profit, flow:s.traffic,\n    conv:s.conv, apt:s.apt, rate:s.rate,\n    inv:(oldMap[s.name]&&oldMap[s.name].inv)||0,\n    d7:(oldMap[s.name]&&oldMap[s.name].d7)||0,\n    yoy:(oldMap[s.name]&&oldMap[s.name].yoy)||0\n  }));", "function applyLive(d){\n  if(!d || !d.apr) return;\n  // APR 整体：仅覆盖有值的字段\n  const a = d.apr;\n  if(a.sales!=null) APR_TOTAL.sales = a.sales;\n  if(a.task!=null) APR_TOTAL.task = a.task;\n  if(a.profit!=null) APR_TOTAL.profit = a.profit;\n  if(a.traffic!=null) APR_TOTAL.flow = a.traffic;\n  if(a.conv!=null) APR_TOTAL.conv = a.conv;\n  if(a.pm!=null) APR_TOTAL.pm = a.pm;\n  if(a.rate!=null) APR_TOTAL.rate = a.rate;\n  // 10 店：仅合并上传字段（客流/转化等），其余保留内嵌\n  if(a.stores && a.stores.length){\n    const oldMap = {}; APR_STORES.forEach(s=>oldMap[s.name]=s);\n    APR_STORES = a.stores.map(s=>{\n      const o = oldMap[s.name] || {};\n      return {\n        name:s.name,\n        sales:s.sales!=null?s.sales:o.sales,\n        task:s.task!=null?s.task:o.task,\n        pm:s.pm!=null?s.pm:o.pm,\n        profit:s.profit!=null?s.profit:o.profit,\n        flow:s.traffic!=null?s.traffic:o.flow,\n        conv:s.conv!=null?s.conv:o.conv,\n        apt:s.apt!=null?s.apt:o.apt,\n        rate:s.rate!=null?s.rate:o.rate,\n        inv:(o&&o.inv)||0,\n        d7:(o&&o.d7)||0,\n        yoy:(o&&o.yoy)||0,\n        off:(o&&o.off)||0,\n        on:(o&&o.on)||0\n      };\n    });\n  }", 1, 'applyLive修复')
R("{code:'AE',desc:'Apple 线上业务 · 3 店'}", "{code:'AE',desc:'Apple 线上业务 · 2 店'}", 1, 'AE 2店')
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
print(); print('PART12 done, ok =', ok)