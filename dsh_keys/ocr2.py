# -*- coding: utf-8 -*-
import subprocess, sys
for path in sys.argv[1:]:
    print('=====', path)
    p = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', path], capture_output=True, text=True)
    print(p.stdout.strip())
    ocr = subprocess.run(['/tmp/ocr_shot', path], capture_output=True, text=True)
    for l in [x for x in ocr.stdout.strip().split('\n') if x.strip()][:40]:
        print(' ', l[:120])
