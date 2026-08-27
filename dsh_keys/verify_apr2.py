import io, re
html = io.open('/tmp/dom_apr2.html', encoding='utf-8').read()
print('区块 h2:', re.findall(r'<h2>([^<]+)</h2>', html)[:12])
print('王畅:', '王畅' in html)
print('部门按钮:', re.findall(r'dept-code">(?:<|)([A-Z]{1,3})', html))
print('区块id:', re.findall(r'id="sec-\d+"', html)[:12])
print('销售员排名区块:', '销售员月度排名' in html)
print('APR门店表:', '徐州彭城店' in html)