# -*- coding: utf-8 -*-
import hashlib, json, time, urllib.request, urllib.parse, datetime

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

biz = '{}'
now = datetime.datetime.now()
ts_full = now.strftime('%Y-%m-%d %H:%M:%S')
candidates = {
    'full': ts_full,
    'minutes': ts_full[:16],
    'date': ts_full[:10],
    'full_utc': (now - datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
    'min_utc': (now - datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M'),
    'full_utc8': (now + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
    'ms': ts_full + '.000',
    'nosep': now.strftime('%Y%m%d%H%M%S'),
}
print('本机时间:', ts_full, '| 时间偏移:', time.strftime('%z'))
for name, tss in candidates.items():
    parts = ['methodacs.bill.create', 'appkey' + APPKEY, 'version1.0', 'contenttypejson', 'timestamp' + tss, 'bizcontent' + biz]
    sign = md5(''.join(parts) + APPSECRET).upper()
    r = call(sign, biz, ts_full)
    tag = 'SIGN-ERR' if '签名错误' in r else ('TS-ERR' if '时间戳' in r else '>>>CHECK<<<')
    print(f'{name:12s} 签名用[{tss}] -> {tag} {r[:90]}')
    if tag == '>>>CHECK<<<':
        print(r[:400])
        break
