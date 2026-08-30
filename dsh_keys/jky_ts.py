# -*- coding: utf-8 -*-
import os, hashlib, json, time, urllib.request, urllib.parse

APPKEY = os.environ.get("JKY_APP_KEY", "")
APPSECRET = os.environ.get("JKY_APP_SECRET", "")
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

formats = [
    '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S.%f',
    '%Y%m%d%H%M%S', '%Y%m%d%H%M', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M',
    '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S+08:00',
]
now = time.localtime()
for fmt in formats:
    ts = time.strftime(fmt, now)
    if '%f' in fmt:
        ts = ts + '000'
    biz = '{}'
    parts = ['methodacs.bill.create', 'appkey' + APPKEY, 'version1.0', 'contenttypejson', 'timestamp' + ts, 'bizcontent' + biz]
    sign = md5(''.join(parts) + APPSECRET).upper()
    r = call(sign, biz, ts)
    short = r[:130].replace('\n', ' ')
    print(fmt, '=>', short)
    if '签名错误' not in r and '时间戳格式错误' not in r:
        print('<<<< WINNER:', fmt)
        print(r[:400])
        break
