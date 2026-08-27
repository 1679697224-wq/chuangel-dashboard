import re, io
src = io.open('/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html', encoding='utf-8').read()
print('破损(应为0):', src.count("<b>¥'+INV_BIZ"))
print('修复后(应为3):', src.count('<b>¥${INV_BIZ'))
html = io.open('/tmp/dom_ov2.html', encoding='utf-8').read() if __import__('os').path.exists('/tmp/dom_ov2.html') else ''
print('渲染中含 ¥2109万:', html.count('¥2109万') if html else '未渲染')
print('渲染中含破损文本:', html.count("¥'+INV_BIZ") if html else '-')