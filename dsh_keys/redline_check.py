# -*- coding: utf-8 -*-
"""检查红色横线范围"""
import struct, subprocess
SRC = "/private/var/folders/jc/pnbwygz541v88t1fz1_dh0j00000gn/T/modlens-dsh-paste/p-lZX3Yd/paste.png"
subprocess.run(['sips', '-c', '40', '2052', '--cropOffset', '580', '0', '-s', 'format', 'bmp', SRC, '--out', '/tmp/red.bmp'], capture_output=True)
with open('/tmp/red.bmp', 'rb') as f:
    data = f.read()
off = struct.unpack('<I', data[10:14])[0]
w = struct.unpack('<i', data[18:22])[0]
h = struct.unpack('<i', data[22:26])[0]
bpp = struct.unpack('<H', data[28:30])[0]
rb = ((w * bpp + 31) // 32) * 4
def px(x, y):
    base = off + y * rb + x * (bpp // 8)
    return (data[base+2], data[base+1], data[base])
# 每 50px 取 x，检查 y=580..620 是否红
print('x 每隔100px，红色行范围:')
for x in range(0, w, 100):
    red_rows = [y for y in range(0, 40) if px(x, y)[0] > 200 and px(x, y)[1] < 100]
    if red_rows:
        print('  x=%4d: y=%d..%d (相对580)' % (x, red_rows[0]+580, red_rows[-1]+580))
    else:
        print('  x=%4d: 无红色' % x)
# 看看红色行是否连续（x=1500 相邻像素）
print()
print('y=597 水平红色连续性（x=0..2052, 每10px 是否红）:')
run_start = None
segments = []
for x in range(0, w, 5):
    r, g, b = px(x, 17)  # 597-580=17
    is_red = r > 200 and g < 100
    if is_red and run_start is None: run_start = x
    if not is_red and run_start is not None:
        segments.append((run_start, x-5)); run_start = None
if run_start is not None: segments.append((run_start, w-1))
print('  红色段:', segments)
