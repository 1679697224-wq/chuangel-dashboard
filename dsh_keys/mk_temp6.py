import io
src = io.open('/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html', encoding='utf-8').read()
io.open('/tmp/dash_overview2.html','w',encoding='utf-8').write(src)
print('temp2 written')