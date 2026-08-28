import io
P = '/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html'
src = io.open(P, encoding='utf-8').read()
old = "    { k:'综合费率 vs 预算', v:fee(c.feeRate), d:isMonth()?'财务费率数据待接入':monthlyNote, cls:'' }\n"
n = src.count(old)
print('错码行:', n)
src = src.replace(old, '')
io.open(P, 'w', encoding='utf-8').write(src)
print('已删除，剩余 monthlyNote 引用:', src.count('monthlyNote'))