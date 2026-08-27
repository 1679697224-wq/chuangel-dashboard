import re
s = open('/tmp/jkmcp.html', encoding='utf-8', errors='replace').read()
for m in list(re.finditer(r'toolList', s))[:6]:
    print(re.sub(r'<[^>]+>', ' ', s[max(0, m.start()-300):m.end()+300])[:500])
    print('-----')
