import io, re
html = io.open('/tmp/dom_ov2.html', encoding='utf-8').read()
idxs = [m.start() for m in re.finditer(re.escape("¥'+INV_BIZ"), html)]
print('共', len(idxs), '处')
for i in idxs[:14]:
    ctx = html[max(0,i-70):i+70].replace('\n',' ')
    print('...', ctx, '...')
    print('---')