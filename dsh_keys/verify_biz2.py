import io, re
html = io.open('/tmp/dom_biz.html', encoding='utf-8').read()
# 部门按钮文本
print('dept-code 出现次数:', html.count('dept-code'))
for m in re.finditer(r'dept-code">([^<]+)</span><span class="dept-copy"><strong>([^<]+)</strong>', html):
    print('  按钮:', m.group(1), m.group(2))
# 剩余8月累计位置
src = io.open('/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html', encoding='utf-8').read()
for m in re.finditer('8月累计', src):
    line = src[:m.start()].count('\n') + 1
    print('源码 L%d: ...%s...' % (line, src[max(0,m.start()-30):m.start()+20].replace('\n',' ')))