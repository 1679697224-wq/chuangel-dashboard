import re
for path in ['/tmp/jkmcp.html', '/tmp/jkdoc.html']:
    s = open(path, encoding='utf-8', errors='replace').read()
    print('=====', path)
    # 找 JS 里的 url/fetch/ajax 模式
    pats = set()
    for m in re.finditer(r"(?:url|fetch|action|src)\s*[:=]\s*[\"']([^\"']+)", s):
        u = m.group(1)
        if 'api' in u or '/' in u:
            pats.add(u[:120])
    for m in re.finditer(r"/developer/[a-zA-Z0-9/_.?=&-]+", s):
        pats.add(m.group(0)[:120])
    for u in sorted(pats)[:25]:
        print(' ', u)
