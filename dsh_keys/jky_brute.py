# -*- coding: utf-8 -*-
import hashlib, json, time, urllib.request, urllib.parse, itertools

APPKEY = "90871460"
APPSECRET = "4e0ca84911ab48aeb2cccad89587222f"
GATEWAY = "https://open.jackyun.com/open/openapi/do"

def md5(s): return hashlib.md5(s.encode('utf-8')).hexdigest()

def base_params():
    return {
        'method': 'acs.bill.create',
        'appkey': APPKEY,
        'version': '1.0',
        'contenttype': 'json',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'bizcontent': json.dumps({}, ensure_ascii=False),
    }

def call(params):
    body = urllib.parse.urlencode(params).encode('utf-8')
    req = urllib.request.Request(GATEWAY, data=body, headers={'Content-Type': 'application/x-www-form-urlencoded;charset=UTF8'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 'EXC:' + str(e)[:120]

# 变体生成器
def variants():
    orders = [
        ['method','appkey','version','contenttype','timestamp','bizcontent'],
        ['appkey','method','version','contenttype','timestamp','bizcontent'],
        None,  # sorted
    ]
    joins = [
        ('kv', lambda parts: ''.join(parts)),
        ('kv_eq', lambda parts: ''.join(parts)),
    ]
    # 每种：是否含 bizcontent、key=value 拼接方式、分隔符、secret 位置、大小写
    for include_biz in (True, False):
        keyset = ['method','appkey','version','contenttype','timestamp'] + (['bizcontent'] if include_biz else [])
        for order in orders:
            for sep in ('', '&'):
                for kv_sep in ('', '='):
                    for secret_pos in ('append', 'prepend'):
                        for case in ('upper', 'lower'):
                            yield (include_biz, order, sep, kv_sep, secret_pos, case, keyset)

count = 0
for (include_biz, order, sep, kv_sep, secret_pos, case, keyset) in variants():
    p = base_params()
    if not include_biz:
        p.pop('bizcontent', None)
    keys = order if order else sorted(keyset)
    parts = []
    for k in keys:
        if k in p:
            parts.append(k + kv_sep + str(p[k]))
    s = sep.join(parts)
    s = (APPSECRET + s) if secret_pos == 'prepend' else (s + APPSECRET)
    h = md5(s)
    sign = h.upper() if case == 'upper' else h
    p['sign'] = sign
    body = call(p)
    count += 1
    if '签名错误' not in body:
        print('FOUND:', include_biz, order, repr(sep), repr(kv_sep), secret_pos, case)
        print(body[:300])
        break
    if count % 40 == 0:
        print('tried', count)
else:
    print('NO MATCH after', count)
