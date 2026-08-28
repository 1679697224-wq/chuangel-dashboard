# -*- coding: utf-8 -*-
import io
p = '/Users/lili/Desktop/deepseek harness/dsh_keys/patch_board_828.py'
src = io.open(p, encoding='utf-8').read()
old = 'int(dg * 6.9), gpm, aov, month_sales'
new = 'int(dg * 6.9), gpm, aov, on, off, month_sales'
n = src.count(old)
print('命中:', n)
src = src.replace(old, new)
io.open(p, 'w', encoding='utf-8').write(src)