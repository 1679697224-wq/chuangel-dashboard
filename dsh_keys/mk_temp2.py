import io
src = io.open('/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html', encoding='utf-8').read()
old = "const state = { cat:0, dept:0, sec:0, period:'day' };"
new = "const state = { cat:1, dept:1, sec:2, period:'day' };"
assert old in src
src = src.replace(old, new)
io.open('/tmp/dash_sp_day.html','w',encoding='utf-8').write(src)
print('temp day written')