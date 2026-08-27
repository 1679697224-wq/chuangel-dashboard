# -*- coding: utf-8 -*-
import subprocess
SRC = "/private/var/folders/jc/pnbwygz541v88t1fz1_dh0j00000gn/T/modlens-dsh-paste/p-yPflop/paste.png"
p = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', SRC], capture_output=True, text=True)
print(p.stdout)
ocr = subprocess.run(['/tmp/ocr_shot', SRC], capture_output=True, text=True)
lines = [l for l in ocr.stdout.strip().split('\n') if l.strip()]
print('=== OCR ===')
for l in lines[:60]: print(' ', l[:120])
