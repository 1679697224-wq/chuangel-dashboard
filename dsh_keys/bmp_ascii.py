# -*- coding: utf-8 -*-
"""把 BMP 转成 ASCII 亮度图，辅助无视觉情况下观察截图"""
import sys, struct

def read_bmp(path, max_w=110):
    with open(path, 'rb') as f:
        data = f.read()
    off = struct.unpack('<I', data[10:14])[0]
    w = struct.unpack('<i', data[18:22])[0]
    h = struct.unpack('<i', data[22:26])[0]
    bpp = struct.unpack('<H', data[28:30])[0]
    comp = struct.unpack('<I', data[30:34])[0]
    h_abs = abs(h)
    row_bytes = ((w * bpp + 31) // 32) * 4
    print('BMP %dx%d bpp=%d comp=%d' % (w, h_abs, bpp, comp))
    # 取目标宽度
    step = max(1, w // max_w)
    out_w = w // step
    out_h = h_abs // step
    chars = ' .:-=+*#%@'
    rows_out = []
    for y in range(0, h_abs, step):
        row = []
        for x in range(0, w, step):
            ry = (h_abs - 1 - y) if h > 0 else y   # BMP 自下而上
            base = off + ry * row_bytes + x * (bpp // 8)
            if base + 3 > len(data):
                row.append(' '); continue
            b, g, r = data[base], data[base+1], data[base+2]
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            row.append(chars[min(int(lum * 10), 9)])
        rows_out.append(''.join(row))
    print('  ASCII %dx%d' % (out_w, out_h))
    for i, rrow in enumerate(rows_out):
        if i % 2 == 0:
            print('%03d %s' % (i * step, rrow))
    # 暗区统计：亮度<0.25 的列分布
    dark_cols = []
    for x in range(0, w, step):
        cnt = 0
        for y in range(0, h_abs, step):
            ry = (h_abs - 1 - y) if h > 0 else y
            base = off + ry * row_bytes + x * (bpp // 8)
            if base + 3 <= len(data):
                b, g, r = data[base], data[base+1], data[base+2]
                if (0.299*r + 0.587*g + 0.114*b) < 64: cnt += 1
        dark_cols.append(cnt)
    print(' 最深暗区列(前10):', sorted([(i*step, c) for i, c in enumerate(dark_cols)], key=lambda x: -x[1])[:10])

read_bmp('/tmp/shadow_small.bmp')
