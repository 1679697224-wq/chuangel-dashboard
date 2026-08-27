import re, html
for path, tag in [('/tmp/etl.html','ETL'), ('/tmp/ql2.html','QL')]:
    s = open(path, encoding='utf-8', errors='replace').read()
    s2 = re.sub(r'<script.*?</script>', '', s, flags=re.S)
    s2 = re.sub(r'<[^>]+>', ' ', s2)
    s2 = html.unescape(re.sub(r'\s+', ' ', s2))
    print('==========', tag)
    for kw in ['签名', 'sign', 'appSecret', 'openapi', 'md5', 'MD5', '排序', '拼接', '密钥']:
        i = s2.find(kw)
        if i >= 0:
            print(f'[{kw}]', s2[max(0, i-150):i+350].strip()[:500])
            print('---')
