# -*- coding: utf-8 -*-
"""裁剪 BMP 指定带并输出高分辨率 ASCII（两种方向都打印，人工判读）"""
import struct, subprocess, os

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

SRC = "/private/var/folders/jc/pnbwygz541v88t1fz1_dh0j00000gn/T/modlens-dsh-paste/p-lZX3Yd/paste.png"
W, H = 2052, 1128
# 中间带（y 450-750）与底部带（y 800-1128）
for name, y0, y1 in [('mid', 420, 760), ('bottom', 780, 1128)]:
    out_path = '/tmp/crop_%s.bmp' % name
    subprocess.run(['sips', '-c', str(y1-y0), str(W), '--cropOffset', str(y0), '0', '-s', 'format', 'bmp', SRC, '--out', out_path],
                   capture_output=True)
    data, off, w, h, bpp, rb = load_bmp(out_path)
    print('==== %s band %dx%d ====' % (name, w, h))
    chars = ' .:-=+*#%@'
    step = max(1, w // 150)
    for y in range(0, h, step*2):
        row = []
        for x in range(0, w, step):
            ry = h - 1 - y
            base = off + ry * rb + x * (bpp // 8)
            if base + 3 > len(data):
                row.append(' '); continue
            b, g, r = data[base], data[base+1], data[base+2]
            lum = (0.299*r + 0.587*g + 0.114*b) / 255.0
            row.append(chars[min(int(lum * 10), 9)])
        print('y%04d %s' % (y0 + y, ''.join(row)))
