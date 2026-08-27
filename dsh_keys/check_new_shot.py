# -*- coding: utf-8 -*-
"""检查新截图：OCR + 阴影带检测"""
import struct, subprocess, re

SRC = "/private/var/folders/jc/pnbwygz541v88t1fz1_dh0j00000gn/T/modlens-dsh-paste/p-u1pErK/paste.png"
# 尺寸
p = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', SRC], capture_output=True, text=True)
print(p.stdout)
# OCR
ocr = subprocess.run(['/tmp/ocr_shot', SRC], capture_output=True, text=True)
lines = [l for l in ocr.stdout.strip().split('\n') if l.strip()]
print('=== OCR（前30条）===');
for l in lines[:30]: print(' ', l[:110])
# 转 BMP 检测横向暗带
subprocess.run(['sips', '-Z', '150', '-s', 'format', 'bmp', SRC, '--out', '/tmp/newshot.bmp'], capture_output=True)
with open('/tmp/newshot.bmp', 'rb') as f: data = f.read()
off = struct.unpack('<I', data[10:14])[0]
w = struct.unpack('<i', data[18:22])[0]
h = struct.unpack('<i', data[22:26])[0]
bpp = struct.unpack('<H', data[28:30])[0]
h_abs = abs(h); rb = ((w*bpp+31)//32)*4
print()
print('=== 行亮度（找骤暗横带）===');
prev = None
for y in range(h_abs):
    s = 0
    for x in range(w):
        base = off + y*rb + x*(bpp//8)
        b = data[base]; g = data[base+1]; r = data[base+2]
        s += 0.299*r + 0.587*g + 0.114*b
    lum = s/(w*255)*100
    flag = ''
    if prev is not None and lum < prev - 6: flag = '  <<< 骤暗'
    prev = lum
    if flag or y < 8 or y > h_abs-6:
        print('y%03d %5.1f %s%s' % (y, lum, '#'*int(lum/4), flag))
