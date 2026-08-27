# -*- coding: utf-8 -*-
"""裁出暗带区域并高分辨率ASCII显示"""
import struct, subprocess

SRC = "/private/var/folders/jc/pnbwygz541v88t1fz1_dh0j00000gn/T/modlens-dsh-paste/p-lZX3Yd/paste.png"
subprocess.run(['sips', '-c', '260', '2052', '--cropOffset', '380', '0', '-s', 'format', 'bmp', SRC, '--out', '/tmp/band.bmp'], capture_output=True)
with open('/tmp/band.bmp', 'rb') as f:
    data = f.read()
off = struct.unpack('<I', data[10:14])[0]
w = struct.unpack('<i', data[18:22])[0]
h = struct.unpack('<i', data[22:26])[0]
bpp = struct.unpack('<H', data[28:30])[0]
h_abs = abs(h)
rb = ((w * bpp + 31) // 32) * 4
print('band %dx%d' % (w, h_abs))
chars = ' .:-=+*#%@'
step = max(1, w // 200)
for y in range(0, h_abs, step*2):
    row = []
    for x in range(0, w, step):
        base = off + y * rb + x * (bpp // 8)
        b, g, r = data[base], data[base+1], data[base+2]
        lum = (0.299*r + 0.587*g + 0.114*b) / 255.0
        row.append(chars[min(int(lum * 10), 9)])
    print('y%04d %s' % (380 + y, ''.join(row)))
