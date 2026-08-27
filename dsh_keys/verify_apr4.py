import io, re
html = io.open('/tmp/dom_apr2.html', encoding='utf-8').read()
print('渲染section元素:', len(re.findall(r'<section class="section-block"', html)))
print('id=sec-N:', re.findall(r'id="sec-\d+"', html))
print('section-head h2:', re.findall(r'section-head"><div><h2>([^<]+)</h2>', html))
# 确认渲染的销售员排名内容（表格行）
print('王畅表格行:', re.findall(r'王畅.*?</tr>', html)[:1])
print('渲染的销售指标k1:', '月累计销售额' in html)
# 页面是否渲染了整体（shell 内容区）
i = html.find('class="content"')
print('content区有内容:', i >= 0 and len(html[i:i+3000]) > 500)