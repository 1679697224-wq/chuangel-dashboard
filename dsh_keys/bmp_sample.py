# -*- coding: utf-8 -*-
"""采样 BMP 若干点 RGB，确认方向与颜色"""
import struct

def load_bmp(path):
    with open(path, 'rb') as f:
        data = f.read()
    off = struct.unpack('<I', data[10:14])[0]
    w = struct.unpack('<i', data[18:22])[0]
    h = struct.unpack('<i', data[22:26])[0]
    bpp = struct.unpack('<H', data[28:30])[0]
    h_abs = abs(h)
    rb = ((w * bpp + 31) // 32) * 4
    print('== %s: %dx%d bpp=%d h_sign=%d' % (path.split('/')[-1], w, h_abs, bpp, h))
    return data, off, w, h_abs, bpp, rb

def px(data, off, w, h, bpp, rb, x, y, bottom_up=True):
    ry = (h - 1 - y) if bottom_up else y
    base = off + ry * rb + x * (bpp // 8)
    b, g, r = data[base], data[base+1], data[base+2]
    return (r, g, b)

data, off, w, h, bpp, rb = load_bmp('/tmp/shadow_small.bmp')
print('60x33 小图采样（两种方向）:')
for y in [0, 5, 8, 15, 20, 30]:
    for x in [5, 30, 55]:
        print('  y=%d x=%d bu=%s' % (y, x, str(px(data, off, w, h, bpp, rb, x, y, True))))
    print('  ---')
# 用 sips 裁一小块原图验证
import subprocess
subprocess.run(['sips', '-c', '50', '50', '--cropOffset', '200', '200', '-s', 'format', 'bmp',
                '/private/var/folders/jc/pnbwygz541v88t1fz1_dh0j00000gn/T/modlens-dsh-paste/p-lZX3Yd/paste.png',
                '--out', '/tmp/px.bmp'], capture_output=True)
data2, off2, w2, h2, bpp2, rb2 = load_bmp('/tmp/px.bmp')
print('原图 (200,200) 附近 50x50 采样:')
for y in [0, 10, 25, 45]:
    for x in [0, 25, 49]:
        print('  y=%d x=%d rgb=%s' % (y, x, str(px(data2, off2, w2, h2, bpp2, rb2, x, y, True))))
