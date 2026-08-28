# -*- coding: utf-8 -*-
import io
p = '/Users/lili/Desktop/deepseek harness/dsh_keys/patch_board_828.py'
src = io.open(p, encoding='utf-8').read()
old = 'gpm = round(gross / (company_sales * 10000) * 100, 2)'
new = 'gpm = round(gross / company_sales * 100, 2)'
print('命中:', src.count(old))
src = src.replace(old, new)
io.open(p, 'w', encoding='utf-8').write(src)