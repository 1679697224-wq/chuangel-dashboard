import io, re
html = io.open('/tmp/dom_biz.html', encoding='utf-8').read()
btns = re.findall(r'选择经营部门.*?</div>', html, re.S)
if btns:
    t = btns[0]
    for code in ['ALL', 'APR', 'AE', 'SH']:
        print(code, '按钮:', ('dept-code">' + code) in t)
else:
    print('未找到部门按钮')
print('APR转化率6.33%:', '6.3%' in html)
print('月度标签:', '>月度<' in html, '| 日度标签:', '>日度<' in html)
print('8月累计标签残留:', html.count('8月累计'))
m = re.search(r'渠道对比.*?</table>', html, re.S)
print('渠道对比表存在:', bool(m))