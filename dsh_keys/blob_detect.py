# -*- coding: utf-8 -*-
"""在用户截图上检测大面积暗区（阴影特征）：亮度<110 的连通块"""
import struct, subprocess
from collections import deque

# 用 sips 转成 400px 宽 BMP（够细）
subprocess.run(['sips', '-Z', '400', '-s', 'format', 'bmp',
                '/private/var/folders/jc/pnbwygz541v88t1fz1_dh0j00000gn/T/modlens-dsh-paste/p-lZX3Yd/paste.png',
                '--out', '/tmp/shadow_400.bmp'], capture_output=True)

with open('/tmp/shadow_400.bmp', 'rb') as f:
    data = f.read()
off = struct.unpack('<I', data[10:14])[0]
w = struct.unpack('<i', data[18:22])[0]
h = struct.unpack('<i', data[22:26])[0]
bpp = struct.unpack('<H', data[28:30])[0]
h_abs = abs(h)
rb = ((w * bpp + 31) // 32) * 4
print('size %dx%d bpp=%d' % (w, h_abs, bpp))

def lum(x, y):
    base = off + y * rb + x * (bpp // 8)
    b, g, r = data[base], data[base+1], data[base+2]
    return 0.299*r + 0.587*g + 0.114*b

TH = 118   # 暗阈值
visited = [[False]*w for _ in range(h_abs)]
blobs = []
for y in range(h_abs):
    for x in range(w):
        if visited[y][x] or lum(x, y) > TH:
            continue
        # BFS
        q = deque([(x, y)]); visited[y][x] = True
        pts = [(x, y)]; minx = maxx = x; miny = maxy = y
        while q:
            cx, cy = q.popleft()
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = cx+dx, cy+dy
                if 0 <= nx < w and 0 <= ny < h_abs and not visited[ny][nx] and lum(nx, ny) <= TH:
                    visited[ny][nx] = True
                    q.append((nx, ny))
                    pts.append((nx, ny))
                    minx = min(minx, nx); maxx = max(maxx, nx)
                    miny = min(miny, ny); maxy = max(maxy, ny)
        bw, bh = maxx-minx+1, maxy-miny+1
        if bw >= 18 and bh >= 18:   # 只报告较大的暗块
            blobs.append((bw, bh, minx, miny, len(pts)))

blobs.sort(key=lambda b: -b[4])
print('大面积暗块（>18x18）共 %d 个，按像素数排序：' % len(blobs))
for bw, bh, bx, by, n in blobs[:20]:
    # 换算回原图坐标（400px 宽 -> 2052 宽，缩放 2052/400 = 5.13）
    sx = 2052/400
    print('  size %dx%d @(x=%d,y=%d) 像素%d  -> 原图约 (%d,%d) %dx%d' % (
        bw, bh, bx, by, n, int(bx*sx), int(by*sx), int(bw*sx), int(bh*sx)))
