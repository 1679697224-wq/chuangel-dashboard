import re, html
s = open('/tmp/csdn.html', encoding='utf-8', errors='replace').read()
i = s.find('id="content_views"')
j = s.find('</article>', i)
body = s[i:j if j > 0 else len(s)]
body = re.sub(r'<script.*?</script>', '', body, flags=re.S)
# 保留代码块
codes = re.findall(r'<pre.*?</pre>', body, re.S)
print('代码块数:', len(codes))
for c in codes[:4]:
    t = re.sub(r'<[^>]+>', '', c)
    print('===== 代码块 =====')
    print(html.unescape(t)[:1800])
