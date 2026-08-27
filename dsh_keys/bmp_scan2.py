# -*- coding: utf-8 -*-
"""细扫内容区 + 行平均亮度找横向暗带（投影特征）"""
import struct

def load_bmp(path):
    with open(path, 'rb') as f:
        data = f.read()
    off = struct.unpack('<I', data[10:14])[0]
    w = struct.unpack('<i', data[18:22])[0]
    h = struct.unpack('<i', data[22:26])[0]
    bpp = struct.unpack('<H', data[28:30])[0]
    h_abs = abs(h)
    row_bytes = ((w * bpp + 31) // 32) * 4
    return data, off, w, h_abs, bpp, row_bytes

data, off, w, h, bpp, rb = load_bmp('/tmp/shadow_small.bmp')
# 行平均亮度（60px 宽的小图）
print('=== 行平均亮度（0=黑 100=白）===')
prev = None
for y in range(h):
    ry = h - 1 - y
    base = off + ry * rb
    s = 0
    for x in range(w):
        b = data[base + x*3]; g = data[base + x*3 + 1]; r = data[base + x*3 + 2]
        s += 0.299*r + 0.587*g + 0.114*b
    lum = s / (w*255) * 100
    bar = '#' * int(lum/5)
    flag = ''
    if prev is not None and lum < prev - 8 and y > 2:
        flag = '  <<< 变暗(可能有投影)'
    prev = lum
    print('y%02d lum%5.1f %s%s' % (y, lum, bar, flag))
