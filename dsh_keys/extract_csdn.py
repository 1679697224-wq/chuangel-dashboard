import re, html
s = open('/tmp/csdn.html', encoding='utf-8', errors='replace').read()
# 找正文里的关键段落
for kw in ['sign', 'appSecret', 'appKey', 'MD5', 'md5', 'access_token', 'timestamp', 'sign_method']:
    for m in list(re.finditer(kw, s, re.I))[:3]:
        ctx = re.sub(r'<[^>]+>', ' ', s[max(0, m.start()-150):m.end()+250])
        ctx = html.unescape(re.sub(r'\s+', ' ', ctx)).strip()
        print(kw, '>>', ctx[:300])
        print('---')
