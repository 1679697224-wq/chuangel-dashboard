# -*- coding: utf-8 -*-
import os, hashlib, json, time, urllib.request, urllib.parse

APPKEY = os.environ.get("JKY_APP_KEY", "")
APPSECRET = os.environ.get("JKY_APP_SECRET", "")
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

def base():
    return {
        'method': 'acs.bill.create', 'appkey': APPKEY, 'version': '1.0', 'contenttype': 'json',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'bizcontent': json.dumps({}, ensure_ascii=False),
    }

orders = [
    ['method','appkey','version','contenttype','timestamp','bizcontent'],
    ['appkey','method','version','contenttype','timestamp','bizcontent'],
    ['bizcontent','method','appkey','version','contenttype','timestamp'],
    None,
]
tried = 0
for order in orders:
    p = base()
    keys = order if order else sorted(p)
    q = urllib.parse.urlencode({k: p[k] for k in keys})
    variants = []
    variants.append(('qs+secret', md5(q + APPSECRET).upper()))
    variants.append(('qs+secret_low', md5(q + APPSECRET)))
    variants.append(('secret+qs', md5(APPSECRET + q).upper()))
    variants.append(('qs', md5(q).upper()))
    # 不编码括号
    q2 = '&'.join(k + '=' + str(p[k]) for k in keys)
    variants.append(('rawqs+secret', md5(q2 + APPSECRET).upper()))
    for name, sign in variants:
        tried += 1
        r = call(sign)
        if '签名错误' not in r:
            print('FOUND:', order, name)
            print(r[:300])
            raise SystemExit
print('NO MATCH after', tried)
