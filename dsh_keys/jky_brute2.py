# -*- coding: utf-8 -*-
import hashlib, json, time, urllib.request, urllib.parse

APPKEY = "90871460"
APPSECRET = "4e0ca84911ab48aeb2cccad89587222f"
GATEWAY = "https://open.jackyun.com/open/openapi/do"
def md5(s): return hashlib.md5(s.encode('utf-8')).hexdigest()

def call(sign):
    p = {
        'method': 'acs.bill.create', 'appkey': APPKEY, 'version': '1.0', 'contenttype': 'json',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'bizcontent': json.dumps({}, ensure_ascii=False),
    }
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

def qs(keys, sep='&', kv='='):
    p = {
        'method': 'acs.bill.create', 'appkey': APPKEY, 'version': '1.0', 'contenttype': 'json',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'bizcontent': json.dumps({}, ensure_ascii=False),
    }
    if keys is None:
        keys = sorted(p)
    return sep.join(k + kv + str(p[k]) for k in keys)

import itertools
orders = [
    ['method','appkey','version','contenttype','timestamp','bizcontent'],
    ['appkey','method','version','contenttype','timestamp','bizcontent'],
    ['bizcontent','method','appkey','version','contenttype','timestamp'],
    None,
]
tried = 0
for order in orders:
    for use_secret in (True, False):
        for pos in ('append', 'prepend'):
            for case in ('upper', 'lower'):
                for sep, kv in (('&','='), ('', '')):
                    q = qs(order, sep, kv)
                    s = (APPSECRET + q) if (use_secret and pos == 'prepend') else q
                    if use_secret and pos == 'append':
                        s = q + APPSECRET
                    h = md5(s)
                    sign = h.upper() if case == 'upper' else h
                    tried += 1
                    r = call(sign)
                    if '签名错误' not in r:
                        print('FOUND:', order, use_secret, pos, case, repr(sep), repr(kv))
                        print(r[:300])
                        raise SystemExit
print('NO MATCH after', tried)
