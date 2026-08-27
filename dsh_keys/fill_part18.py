# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("  const deptMeta = [\n    {code:'ALL',desc:'四大渠道整体对比'},\n    {code:'APR',desc:'线下零售门店 · 10 店'},\n    {code:'AE',desc:'Apple 线上业务 · 2 店'},\n    {code:'SH',desc:'舒尔线上业务 · 2 店'},\n\n  ];", "  const deptMeta = [\n    {code:'APR',desc:'线下零售门店 · 10 店'},\n    {code:'AE',desc:'Apple 线上业务 · 2 店'},\n    {code:'SH',desc:'舒尔线上业务 · 2 店'}\n  ];", 1, 'deptMeta3')
R("deptSwitch.innerHTML = `<div class=\"dept-heading\"><span>BUSINESS UNIT</span><strong>选择经营部门</strong></div>${c.departments.map((d,i)=>`<button class=\"${i===state.dept?'active':''}\" data-i=\"${i}\"><span class=\"dept-code\">${deptMeta[i].code}</span><span class=\"dept-copy\"><strong>${esc(d.name)}</strong><small>${deptMeta[i].desc}</small></span><span class=\"dept-arrow\">›</span></button>`).join('')}`;", "deptSwitch.innerHTML = `<div class=\"dept-heading\"><span>BUSINESS UNIT</span><strong>选择经营部门</strong></div>${c.departments.slice(1).map((d,i)=>`<button class=\"${(i+1)===state.dept?'active':''}\" data-i=\"${i+1}\"><span class=\"dept-code\">${deptMeta[i].code}</span><span class=\"dept-copy\"><strong>${esc(d.name)}</strong><small>${deptMeta[i].desc}</small></span><span class=\"dept-arrow\">›</span></button>`).join('')}`;", 1, '部门按钮slice')
R("<span class=\"section-tag\">8月累计</span>", "<span class=\"section-tag\">${PERIOD_LABEL[state.period]}</span>", 5, '卡片标签动态5')
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
print(); print('PART18 done, ok =', ok)