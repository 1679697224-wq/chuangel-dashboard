# -*- coding: utf-8 -*-
import hashlib, json, time, urllib.request, urllib.parse, itertools

APPKEY = "90871460"
APPSECRET = "4e0ca84911ab48aeb2cccad89587222f"
GATEWAY = "https://open.jackyun.com/open/openapi/do"
def md5(s): return hashlib.md5(s.encode('utf-8')).hexdigest()

def call(sign, biz, ts):
    p = {
        'method': 'acs.bill.create', 'appkey': APPKEY, 'version': '1.0', 'contenttype': 'json',
        'timestamp': ts, 'bizcontent': biz,
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

ts_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y%m%d%H%M%S', '%Y-%m-%dT%H:%M:%S']
bizvalues = ['{}', '[]', '', 'null']
orders = [
    ['method','appkey','version','contenttype','timestamp','bizcontent'],
    ['appkey','method','version','contenttype','timestamp','bizcontent'],
    ['bizcontent','method','appkey','version','contenttype','timestamp'],
    None,
]
tried = 0
for ts_fmt in ts_formats:
    ts = time.strftime(ts_fmt)
    for biz in bizvalues:
        for include_biz in (True, False):
            for order in orders:
                keyset = ['method','appkey','version','contenttype','timestamp'] + (['bizcontent'] if include_biz else [])
                keys = order if order else sorted(keyset)
                parts = []
                for k in keys:
                    if k == 'bizcontent':
                        parts.append('bizcontent' + biz)
                    elif k == 'timestamp':
                        parts.append('timestamp' + ts)
                    elif k == 'appkey':
                        parts.append('appkey' + APPKEY)
                    elif k == 'method':
                        parts.append('methodacs.bill.create')
                    elif k == 'version':
                        parts.append('version1.0')
                    elif k == 'contenttype':
                        parts.append('contenttypejson')
                for pos in ('append', 'prepend'):
                    s = (APPSECRET + ''.join(parts)) if pos == 'prepend' else (''.join(parts) + APPSECRET)
                    for case in ('upper', 'lower'):
                        h = md5(s)
                        sign = h.upper() if case == 'upper' else h
                        tried += 1
                        r = call(sign, biz, ts)
                        if '签名错误' not in r:
                            print('FOUND: ts_fmt=%s biz=%r include_biz=%s order=%s pos=%s case=%s' % (ts_fmt, biz, include_biz, order, pos, case))
                            print(r[:300])
                            raise SystemExit
print('NO MATCH after', tried)
