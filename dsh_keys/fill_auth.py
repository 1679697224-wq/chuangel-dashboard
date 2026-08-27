# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding="utf-8").read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("const res = await fetch('http://localhost:8003/api/data', {mode:'cors'});", "const urls = ['/api/data', 'http://47.96.42.110:8003/api/data', 'http://localhost:8003/api/data'];\n    let res = null;\n    for (const u of urls) { try { const r = await fetch(u, {mode:'cors'}); if (r.ok) { res = r; break; } } catch(e){} }\n    if(!res) throw new Error('no live source');", 1, 'loadLiveData URL')
R("  // 商务库存\n  if(d.inventory_biz){", "  // 电商分店流量/转化（负责人上传）\n  if(d.ecom){\n    const mergeStore = (arr, map, extra) => {\n      (map||{}).forEach && Object.keys(map).forEach(name=>{\n        const s = arr.find(x=>x.name.indexOf(name)>=0 || name.indexOf(x.name)>=0);\n        if(!s) return;\n        const v = map[name] || {};\n        if(v.uv!=null) s.uv = v.uv;\n        if(v.cvr!=null) s.cvr = v.cvr;\n        if(v.refund!=null) s.refund = v.refund;\n        if(v.sales!=null) s.sales = v.sales/ (extra&&extra.div||1);\n        if(v.aov!=null) s.aov = v.aov;\n      });\n    };\n    if(d.ecom.ae) mergeStore(AE_STORES, d.ecom.ae);\n    if(d.ecom.sh) mergeStore(SH_STORES, d.ecom.sh, {div:29.2});\n  }\n  // 商务库存\n  if(d.inventory_biz){", 1, 'applyLive 电商合并')
R("(async function init(){\n  await loadLiveData();\n  render();\n})();", "function filterByRole(role){\n  if(!role || role === 'boss') return;\n  const allow = {apr:['APR'], apple:['Apple'], shure:['Shure'], finance:['整体','APR','Apple','Shure','3PP'], hr:[]}[role] || [];\n  document.querySelectorAll('.department-switch button').forEach(function(b){\n    const ok = allow.some(function(d){ return b.textContent.indexOf(d) >= 0; });\n    if(!ok) b.style.display = 'none';\n  });\n}\n(async function init(){\n  await loadLiveData();\n  render();\n  if(window.__ROLE__) filterByRole(window.__ROLE__);\n})();", 1, 'filterByRole')
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
print(); print('PART8 done, ok =', ok)