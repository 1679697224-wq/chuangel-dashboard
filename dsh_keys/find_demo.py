import io
src = io.open('/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html', encoding='utf-8').read()
import re
for kw in ['演示数据', '第三方配件', '3PP']:
    idxs = [m.start() for m in re.finditer(kw, src)]
    print(kw, ':', len(idxs))
    for i in idxs[:8]:
        line = src[:i].count('\n') + 1
        ctx = src[max(0,i-40):i+40].replace('\n', ' ')
        print('  L%d: ...%s...' % (line, ctx))