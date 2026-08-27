# -*- coding: utf-8 -*-
import hashlib, json, time, urllib.request, urllib.parse
APPKEY = "90871460"
APPSECRET = "4e0ca84911ab48aeb2cccad89587222f"
GATEWAY = "https://open.jackyun.com/open/openapi/do"

def md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def call(method, bizcontent, signer):
    params = {
        'method': method, 'appkey': APPKEY, 'version': '1.0', 'contenttype': 'json',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'bizcontent': json.dumps(bizcontent, ensure_ascii=False),
    }
    params['sign'] = signer(params, APPSECRET)
    body = urllib.parse.urlencode(params).encode('utf-8')
    req = urllib.request.Request(GATEWAY, data=body, headers={'Content-Type': 'application/x-www-form-urlencoded;charset=UTF8'})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read().decode('utf-8', 'replace')[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:400]
    except Exception as e:
        return -1, str(e)[:200]

def s1(params, secret):
    return md5(''.join(k + str(params[k]) for k in sorted(params)) + secret).upper()

def s3(params, secret):
    order = ['method', 'appkey', 'version', 'contenttype', 'timestamp', 'bizcontent']
    return md5(''.join(k + str(params[k]) for k in order if k in params) + secret).upper()

for name, fn in [('V1排序大写', s1), ('V3固定序大写', s3)]:
    code, body = call('acs.bill.create', {}, fn)
    print(f'--- {name}: HTTP {code}')
    print(body)
