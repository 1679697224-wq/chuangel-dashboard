# -*- coding: utf-8 -*-
"""修正方向后全图 ASCII + 行亮度（找阴影）"""
import struct, subprocess

def load_bmp(path):
    with open(path, 'rb') as f:
        data = f.read()
    off = struct.unpack('<I', data[10:14])[0]
    w = struct.unpack('<i', data[18:22])[0]
    h = struct.unpack('<i', data[22:26])[0]
    bpp = struct.unpack('<H', data[28:30])[0]
    h_abs = abs(h)
    rb = ((w * bpp + 31) // 32) * 4
    return data, off, w, h_abs, bpp, rb

# 用原图做更细的 ASCII（sips -Z 150）
subprocess.run(['sips', '-Z', '150', '-s', 'format', 'bmp',
                '/private/var/folders/jc/pnbwygz541v88t1fz1_dh0j00000gn/T/modlens-dsh-paste/p-lZX3Yd/paste.png',
                '--out', '/tmp/shadow_150.bmp'], capture_output=True)
data, off, w, h, bpp, rb = load_bmp('/tmp/shadow_150.bmp')
print('150px 图: %dx%d bpp=%d' % (w, h, bpp))
chars = ' .:-=+*#%@'
print('=== 全图 ASCII（top-down）===')
for y in range(0, h, 2):
    row = []
    for x in range(0, w, 2):
        base = off + y * rb + x * (bpp // 8)
        b, g, r = data[base], data[base+1], data[base+2]
        lum = (0.299*r + 0.587*g + 0.114*b) / 255.0
        row.append(chars[min(int(lum * 10), 9)])
    print('%03d %s' % (y, ''.join(row)))
print()
print('=== 行平均亮度（找暗带）===')
prev = None
for y in range(h):
    s = 0
    for x in range(w):
        base = off + y * rb + x * (bpp // 8)
        b, g, r = data[base], data[base+1], data[base+2]
        s += 0.299*r + 0.587*g + 0.114*b
    lum = s / (w*255) * 100
    flag = ''
    if prev is not None and lum < prev - 6:
        flag = '   <<< 骤暗'
    prev = lum
    print('y%03d %5.1f %s%s' % (y, lum, '#'*int(lum/4), flag))
