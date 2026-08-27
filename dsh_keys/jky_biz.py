# -*- coding: utf-8 -*-
import hashlib, json, time, urllib.request, urllib.parse

APPKEY = "90871460"
APPSECRET = "4e0ca84911ab48aeb2cccad89587222f"
GATEWAY = "https://open.jackyun.com/open/openapi/do"
def md5(s): return hashlib.md5(s.encode('utf-8')).hexdigest()

def call(sign, biz, ts):
    p = {'method': 'acs.bill.create', 'appkey': APPKEY, 'version': '1.0', 'contenttype': 'json', 'timestamp': ts, 'bizcontent': biz}
    p['sign'] = sign
    body = urllib.parse.urlencode(p).encode('utf-8')
    req = urllib.request.Request(GATEWAY, data=body, headers={'Content-Type': 'application/x-www-form-urlencoded;charset=UTF8'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 'EXC:' + str(e)[:120]

ts = time.strftime('%Y-%m-%d %H:%M:%S')
biz_candidates = ['{}', '[]', '', 'null']
orders = [
    ['method','appkey','version','contenttype','timestamp','bizcontent'],
    None,
]
tested = 0
for biz in biz_candidates:
    for order in orders:
        keyset = ['method','appkey','version','contenttype','timestamp','bizcontent']
        keys = order if order else sorted(keyset)
        parts = []
        for k in keys:
            if k == 'bizcontent': parts.append('bizcontent' + biz)
            elif k == 'timestamp': parts.append('timestamp' + ts)
            elif k == 'appkey': parts.append('appkey' + APPKEY)
            elif k == 'method': parts.append('methodacs.bill.create')
            elif k == 'version': parts.append('version1.0')
            elif k == 'contenttype': parts.append('contenttypejson')
        sign = md5(''.join(parts) + APPSECRET).upper()
        tested += 1
        r = call(sign, biz, ts)
        tag = 'SIGN-ERR' if '签名错误' in r else ('TS-ERR' if '时间戳' in r else '>>>HIT<<<')
        print(f'biz={biz!r:8s} order={order is None and "sorted" or "insert"} -> {tag} {r[:100]}')
        if tag == '>>>HIT<<<':
            print('WINNER:', biz, order)
            print(r[:400])
            raise SystemExit
print('NO HIT after', tested)
