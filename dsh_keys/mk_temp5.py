import io
src = io.open('/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html', encoding='utf-8').read()
old = "const state = { cat:0, dept:0, sec:0, period:'day' };"
new = "const state = { cat:0, dept:0, sec:0, period:'day' };"
assert old in src
io.open('/tmp/dash_overview.html','w',encoding='utf-8').write(src)
print('ok')