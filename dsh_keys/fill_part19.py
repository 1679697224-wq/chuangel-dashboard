# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("tableCard('门店经营对比（'+pl+'）'", "tableCard('门店经营对比（'+PERIOD_LABEL[state.period]+'）'", 1, '门店表标题修复')
R("function navMeta(c){ if(c.departments) return c.departments.length+' 个经营部门';", "function navMeta(c){ if(c.departments) return (c.departments.length-1)+' 个经营部门';", 1, 'navMeta 3部门')
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
print(); print('PART19 done, ok =', ok)