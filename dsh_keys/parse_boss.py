# -*- coding: utf-8 -*-
import re, json
s = open('/tmp/boss_dash.html', encoding='utf-8').read()

# CSS 设计变量
m = re.search(r':root\s*\{([^}]*)\}', s)
print('== CSS 变量 ==')
if m:
    for line in m.group(1).split(';'):
        line = line.strip()
        if line and ':' in line:
            print(' ', line.split(':')[0].strip(), '=', line.split(':', 1)[1].strip())

# 提取 script
scripts = re.findall(r'<script[^>]*>(.*?)</script>', s, re.S)
open('/tmp/boss_script.js', 'w', encoding='utf-8').write(scripts[0] if scripts else '')
print('== script 长度 ==', len(scripts[0]) if scripts else 0)

# 找 config 结构：打印含 sections: 的片段
print('== sections 上下文 ==')
for m2 in list(re.finditer(r'sections:', scripts[0] if scripts else ''))[:8]:
    print(scripts[0][max(0, m2.start()-600):m2.start()+900].replace('\n', ' ')[:1500])
    print('-----')
