import re, html
s = open('/tmp/csdn.html', encoding='utf-8', errors='replace').read()
i = s.find('id="content_views"')
j = s.find('</article>', i)
body = s[i:j if j > 0 else len(s)]
codes = re.findall(r'<pre.*?</pre>', body, re.S)
t = html.unescape(re.sub(r'<[^>]+>', '', codes[0]))
print(t)
