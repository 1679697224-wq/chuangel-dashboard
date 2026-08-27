# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("const state = { cat:0, dept:0, sec:0, period:'day' };", "const state = { cat:0, dept:0, sec:0, period:'month' };", 1, '默认月度')
R("nav.querySelectorAll('button').forEach(b=>b.onclick=()=>{ state.cat=+b.dataset.i; state.sec=0; render(); window.scrollTo({top:0,behavior:'smooth'}); });", "nav.querySelectorAll('button').forEach(b=>b.onclick=()=>{ state.cat=+b.dataset.i; state.dept=0; state.sec=0; render(); window.scrollTo({top:0,behavior:'smooth'}); });", 1, '导航重置dept')
R("<button class=\"active\" data-p=\"day\">日</button><button data-p=\"week\">周</button><button data-p=\"month\">月</button>", "<button data-p=\"day\">日</button><button data-p=\"week\">周</button><button class=\"active\" data-p=\"month\">月</button>", 1, '周期默认月')
R("function renderDepartments(c){\n  if(!c.departments){ deptSwitch.innerHTML=''; return; }\n  const deptMeta = [\n    {code:'ALL',desc:'四大渠道整体对比'},\n    {code:'APR',desc:'线下零售门店 · 10 店'},\n    {code:'AE',desc:'Apple 线上业务 · 2 店'},\n    {code:'SH',desc:'舒尔线上业务 · 2 店'}\n  ];\n  deptSwitch.innerHTML = `<div class=\"dept-heading\"><span>BUSINESS UNIT</span><strong>选择经营部门</strong></div>${c.departments.map((d,i)=>`<button class=\"${i===state.dept?'active':''}\" data-i=\"${i}\"><span class=\"dept-code\">${deptMeta[i].code}</span><span class=\"dept-copy\"><strong>${esc(d.name)}</strong><small>${deptMeta[i].desc}</small></span><span class=\"dept-arrow\">›</span></button>`).join('')}`;\n  deptSwitch.querySelectorAll('button').forEach(b=>b.onclick=()=>{ state.dept=+b.dataset.i; state.sec=0; render(); window.scrollTo({top:0,behavior:'smooth'}); });\n}", "function renderDepartments(c){\n  if(!c.departments){ deptSwitch.innerHTML=''; return; }\n  const deptMeta = [\n    {code:'APR',desc:'线下零售门店 · 10 店'},\n    {code:'AE',desc:'Apple 线上业务 · 2 店'},\n    {code:'SH',desc:'舒尔线上业务 · 2 店'}\n  ];\n  const btns = c.departments.slice(1).map((d,i)=>{\n    const real = i + 1;\n    return `<button class=\"${real===state.dept?'active':''}\" data-i=\"${real}\"><span class=\"dept-code\">${deptMeta[i].code}</span><span class=\"dept-copy\"><strong>${esc(d.name)}</strong><small>${deptMeta[i].desc}</small></span><span class=\"dept-arrow\">›</span></button>`;\n  }).join('');\n  deptSwitch.innerHTML = `<div class=\"dept-heading\"><span>BUSINESS UNIT</span><strong>选择经营部门</strong></div>${btns}`;\n  deptSwitch.querySelectorAll('button').forEach(b=>b.onclick=()=>{ state.dept=+b.dataset.i; state.sec=0; render(); window.scrollTo({top:0,behavior:'smooth'}); });\n}", 1, '3部门按钮')
R("{ name:'APR（整体）', code:'APR', sales:688842, gross:21345, gpm:3.10, cvr:null, feeRate:null, inv:1442.6, d7:null, yoy:72.8, onlineShare:30.7, offlineShare:69.3, note:'10 家门店 · 含线上线下整体' },", "{ name:'APR（整体）', code:'APR', sales:688842, gross:21345, gpm:3.10, cvr:6.33, feeRate:null, inv:1442.6, d7:null, yoy:72.8, onlineShare:30.7, offlineShare:69.3, note:'10 家门店 · 含线上线下整体' },", 1, 'SEGMENTS APR转化')
R("{ name:'APR（整体）', code:'APR', sales:688842, gross:21345, gpm:3.10, cvr:null, feeRate:null, inv:1442.6, d7:null, yoy:72.8, note:'10 家门店 · 含线上线下' },", "{ name:'APR（整体）', code:'APR', sales:688842, gross:21345, gpm:3.10, cvr:6.33, feeRate:null, inv:1442.6, d7:null, yoy:72.8, note:'10 家门店 · 含线上线下' },", 1, 'BUSINESS_ROWS APR转化')
R("<span class=\"section-tag\">8月累计</span>", "<span class=\"section-tag\">${PERIOD_LABEL[state.period]}</span>", 4, '卡片标签动态')
R("${esc(tag||'8月累计')}", "${esc(tag||PERIOD_LABEL[state.period])}", 1, 'tableCard默认动态')
R("tableCard('门店经营对比（8月累计）'", "tableCard('门店经营对比（'+pl+'）'", 1, '门店表标题动态')
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
print(); print('PART17 done, ok =', ok)