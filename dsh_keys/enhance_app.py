# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/登录权限系统/app.py"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("    if '天猫' in filename or '反馈表' in filename:\n        s = summarize_daily(rows, 1, 2, 11, 4)\n        set_upload('shure', {'stores': {'天猫旗舰店': {'uv': s['uv'], 'sales': round(s['sales'], 2), 'orders': s['orders']}}, 'last_upload': datetime.now().isoformat(timespec='seconds')})\n        return '天猫舒尔：8月销售 %.2f 万 / uv %d / 单 %d' % (s['sales']/10000, s['uv'], s['orders'])", "    if '天猫' in filename or '反馈表' in filename:\n        aug = {'sales': 0.0, 'uv': 0, 'orders': 0}\n        for r in rows[2:]:\n            for dc, sc, oc, uc in ((1, 2, 4, 11), (0, 1, 3, 10)):\n                if len(r) <= max(dc, sc, oc, uc):\n                    continue\n                d = excel_serial(r[dc])\n                if not d.startswith('2026-08'):\n                    continue\n                def f(i):\n                    try: return float(r[i])\n                    except Exception: return 0.0\n                aug['sales'] += f(sc); aug['orders'] += f(oc); aug['uv'] += int(f(uc))\n                break\n        set_upload('shure', {'stores': {'天猫旗舰店': {'uv': aug['uv'], 'sales': round(aug['sales'], 2), 'orders': aug['orders']}}, 'last_upload': datetime.now().isoformat(timespec='seconds')})\n        return '天猫舒尔：8月销售 %.2f 万 / uv %d / 单 %d' % (aug['sales']/10000, aug['uv'], aug['orders'])", 1, '天猫解析增强')
ok = True
for old, new, expect, name in REPS:
    n = src.count(old)
    if n != expect:
        print("MISS/COUNT[%s]: expected %d, got %d" % (name, expect, n))
        ok = False
    else:
        src = src.replace(old, new)
        print("ok  [%s]" % name)
io.open(P, 'w', encoding='utf-8').write(src)
print(); print('app.py 增强 done, ok =', ok)