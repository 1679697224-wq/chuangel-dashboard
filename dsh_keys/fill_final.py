# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("${esc(tag||'演示数据')}", "${esc(tag||'8月累计')}", 1, 'tableCard默认标签')
R("暂不展示占比与合理性判断（原演示数据已移除）", "暂不展示占比与合理性判断（原示例数据已移除）", 1, '费用分析文案')
R("演示数据 · 待接入自动取数", "未接入 · 待自动取数", 5, '训练卡未接入')
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
print('演示数据残留:', src.count('演示数据'))
print(); print('FINAL done, ok =', ok)