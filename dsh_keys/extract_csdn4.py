import re, html
s = open('/tmp/csdn.html', encoding='utf-8', errors='replace').read()
i = s.find('id="content_views"')
j = s.find('</article>', i)
body = s[i:j if j > 0 else len(s)]
# 找所有包含 $paramArr 的文本段
parts = re.findall(r'.{0,80}\$paramArr.{0,200}', body)
print('paramArr 片段数:', len(parts))
for p in parts[:10]:
    t = html.unescape(re.sub(r'<[^>]+>', ' ', p))
    print(re.sub(r'\s+', ' ', t).strip()[:260])
print('===== md5/strtoupper 上下文 =====')
for kw in ['strtoupper', 'md5', 'ksort', 'implode', 'http_build_query', 'curl_exec', 'do?', 'GATEWAY']:
    for m in list(re.finditer(kw, body, re.I))[:2]:
        t = html.unescape(re.sub(r'<[^>]+>', ' ', body[max(0, m.start()-200):m.end()+200]))
        print(kw, '>>', re.sub(r'\s+', ' ', t).strip()[:280])
        print('--')
