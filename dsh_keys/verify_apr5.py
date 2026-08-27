import io, re
html = io.open('/tmp/dom_apr4.html', encoding='utf-8').read()
print('渲染section数:', len(re.findall(r'<section class="section-block" id="sec-', html)))
print('区块h2:', re.findall(r'<h2>([^<]+)</h2>', html)[:12])
print('销售员排名内容(王畅):', '王畅' in html)
print('APR门店表(徐州彭城店):', '徐州彭城店' in html)
print('月度目标达成卡:', '月度目标达成' in html)
print('部门按钮3个:', len(re.findall(r'dept-code', html)) >= 3)