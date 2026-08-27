# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("    } else {\n    const seg = SEGMENTS[state.dept-1] || SEGMENTS[0];\n    hs.innerHTML = `<div class=\"hero-stat\"><span>${PERIOD_LABEL[state.period]}销售额</span><strong>${fmtY(mul(seg.sales))}</strong><small class=\"${seg.d7>=0?'':'down'}\">${seg.d7>=0?'▲':'▼'} 环比 ${Math.abs(seg.d7)}%</small><span class=\"hs-sub\">同比 +${seg.yoy}% · ${esc(seg.note)}</span></div>\n      <div class=\"hero-stat\"><span>${PERIOD_LABEL[state.period]}毛利率</span><strong>${pct(seg.gpm)}</strong><small>毛利额 ${fmtWan(mul(seg.gross))}</small><span class=\"hs-sub\">费率 ${fee(seg.feeRate)}</span></div>\n      <div class=\"hero-stat\"><span>转化率</span><strong>${pct(seg.cvr)}</strong><small>${seg.cvr>=5?'✓ 达标线以上':'需关注'}</small><span class=\"hs-sub\">${esc(seg.note)}</span></div>`;\n    }", "    } else {\n    const seg = SEGMENTS[state.dept-1] || SEGMENTS[0];\n    // Shure：hero 总销售 = 天猫 + 京东 两店合计（京东为平台日报口径）\n    const isSH = seg && seg.code==='SH';\n    const heroSales = isSH ? SH_STORES.reduce((a,b)=>a+b.sales,0) : seg.sales;\n    const heroNote = isSH ? '天猫72.15(吉客云)+京东74.73(日报) · 两店合计' : esc(seg.note);\n    const heroConv = isSH ? 1.37 : seg.cvr;\n    const heroConvSub = isSH ? '京东3.12% / 天猫0.88%（平台日报）' : esc(seg.note);\n    hs.innerHTML = `<div class=\"hero-stat\"><span>${PERIOD_LABEL[state.period]}销售额</span><strong>${fmtY(mul(heroSales))}</strong><small class=\"${seg.d7>=0?'':'down'}\">${seg.d7>=0?'▲':'▼'} 环比 ${Math.abs(seg.d7||0)}%</small><span class=\"hs-sub\">同比 +${seg.yoy}% · ${heroNote}</span></div>\n      <div class=\"hero-stat\"><span>${PERIOD_LABEL[state.period]}毛利率</span><strong>${pct(seg.gpm)}</strong><small>毛利额 ${fmtWan(mul(seg.gross))}</small><span class=\"hs-sub\">费率 ${fee(seg.feeRate)}</span></div>\n      <div class=\"hero-stat\"><span>转化率</span><strong>${pct(heroConv)}</strong><small>${(heroConv||0)>=5?'✓ 达标线以上':'需关注'}</small><span class=\"hs-sub\">${heroConvSub}</span></div>`;\n    }", 1, 'Shure hero两店合计')
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
print(); print('PART15 done, ok =', ok)