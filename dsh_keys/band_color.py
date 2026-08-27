# -*- coding: utf-8 -*-
"""暗带颜色采样"""
import struct, subprocess
SRC = "/private/var/folders/jc/pnbwygz541v88t1fz1_dh0j00000gn/T/modlens-dsh-paste/p-lZX3Yd/paste.png"
subprocess.run(['sips', '-c', '60', '2052', '--cropOffset', '575', '0', '-s', 'format', 'bmp', SRC, '--out', '/tmp/band2.bmp'], capture_output=True)
with open('/tmp/band2.bmp', 'rb') as f:
    data = f.read()
off = struct.unpack('<I', data[10:14])[0]
w = struct.unpack('<i', data[18:22])[0]
h = struct.unpack('<i', data[22:26])[0]
bpp = struct.unpack('<H', data[28:30])[0]
rb = ((w * bpp + 31) // 32) * 4
def px(x, y):
    base = off + y * rb + x * (bpp // 8)
    return (data[base+2], data[base+1], data[base])  # RGB
print('y=580..635 的 (x=300, 1000, 1800) 颜色:')
for y in range(0, 60, 4):
    row = []
    for x in (300, 1000, 1800):
        r, g, b = px(x, y)
        row.append('(%3d,%3d,%3d)' % (r, g, b))
    print('  y%3d  %s' % (575+y, '  '.join(row)))
print()
print('x=1000 列 y=575..635 颜色:')
for y in range(0, 60, 3):
    r, g, b = px(1000, y)
    lum = 0.299*r+0.587*g+0.114*b
    print('  y%3d rgb(%3d,%3d,%3d) lum=%5.0f' % (575+y, r, g, b, lum))
