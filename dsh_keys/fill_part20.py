# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("    { k:'综合费率 vs 预算', v:fee(c.feeRate), d:isMonth()?'财务费率数据待接入':monthlyNote, cls:'' },\n", "", 1, '删错码行')
R(".detail-panel.tri{grid-template-columns:repeat(3,minmax(0,1fr))}", ".detail-panel.tri{grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}", 1, 'tri自适应')
R(".pie3d-stage{display:flex;align-items:center;justify-content:center;padding:12px 0 2px;margin:6px 0 2px}", ".pie3d-stage{display:flex;align-items:center;justify-content:center;padding:10px 0 2px;margin:4px 0 2px}", 1, 'pie3d留白')
R(".pie3d-svg{width:212px;height:200px;max-width:100%}", ".pie3d-svg{width:290px;height:274px;max-width:100%}", 1, 'pie3d放大')
R(".donut{width:150px;height:150px;border-radius:50%;position:relative;flex:0 0 auto}", ".donut{width:200px;height:200px;border-radius:50%;position:relative;flex:0 0 auto}", 1, 'donut放大')
R(".donut:after{content:attr(data-center);position:absolute;inset:30px;background:var(--card);border-radius:50%;display:grid;place-items:center;font-weight:800;color:#415771;font-size:13px;text-align:center;line-height:1.4}", ".donut:after{content:attr(data-center);position:absolute;inset:38px;background:var(--card);border-radius:50%;display:grid;place-items:center;font-weight:800;color:#415771;font-size:14px;text-align:center;line-height:1.4}", 1, 'donut中心')
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
print(); print('PART20 done, ok =', ok)