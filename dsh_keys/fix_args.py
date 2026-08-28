# -*- coding: utf-8 -*-
import io
p = '/Users/lili/Desktop/deepseek harness/dsh_keys/patch_board_828.py'
src = io.open(p, encoding='utf-8').read()
old = 'month_sales, gross_y, gpm, aov, on, off)' + chr(10) + 'R(old_c, new_c, 1'
new = 'month_sales, gross_y, gpm, aov, on, off, on, off)' + chr(10) + 'R(old_c, new_c, 1'
if old in src:
    src = src.replace(old, new)
    print('args fixed')
else:
    i = src.find('new_c =')
    print('NOT FOUND; ctx:', src[i:i+300])
io.open(p, 'w', encoding='utf-8').write(src)