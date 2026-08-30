# -*- coding: utf-8 -*-
import os, hashlib, json, time, urllib.request, urllib.parse

APPKEY = os.environ.get("JKY_APP_KEY", "")
APPSECRET = os.environ.get("JKY_APP_SECRET", "")
GATEWAY = "https://open.jackyun.com/open/openapi/do"
def md5(s): return hashlib.md5(s.encode('utf-8')).hexdigest()

def call(method, bizcontent, ts_send, ts_sign):
    p = {'method': method, 'appkey': APPKEY, 'version': '1.0', 'contenttype': 'json',
         'timestamp': ts_send, 'bizcontent': json.dumps(bizcontent, ensure_ascii=False)}
    parts = ['method' + method, 'appkey' + APPKEY, 'version1.0', 'contenttypejson',
             'timestamp' + ts_sign, 'bizcontent' + json.dumps(bizcontent, ensure_ascii=False)]
    p['sign'] = md5(''.join(parts) + APPSECRET).upper()
    body = urllib.parse.urlencode(p).encode('utf-8')
    req = urllib.request.Request(GATEWAY, data=body, headers={'Content-Type': 'application/x-www-form-urlencoded;charset=UTF8'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 'EXC:' + str(e)[:120]

ts_full = time.strftime('%Y-%m-%d %H:%M:%S')
ts_min = ts_full[:16]
print('发送时间戳:', ts_full, '| 签名用:', ts_min)
r = call('acs.bill.create', {}, ts_full, ts_min)
print(r[:400])
