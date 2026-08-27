# -*- coding: utf-8 -*-
"""吉客云 API 客户端（签名已验证）"""
import hashlib, json, time, urllib.request, urllib.parse

APPKEY = "90871460"
APPSECRET = "4e0ca84911ab48aeb2cccad89587222f"
GATEWAY = "https://open.jackyun.com/open/openapi/do"

def md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def call(method, bizcontent):
    params = {
        'method': method,
        'appkey': APPKEY,
        'version': '1.0',
        'contenttype': 'json',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'bizcontent': json.dumps(bizcontent, ensure_ascii=False),
    }
    # 签名：bizcontent 不参与；固定顺序 method,appkey,version,contenttype,timestamp + secret；MD5 大写
    s = ''.join(k + str(params[k]) for k in ['method', 'appkey', 'version', 'contenttype', 'timestamp'])
    params['sign'] = md5(s + APPSECRET).upper()
    body = urllib.parse.urlencode(params).encode('utf-8')
    req = urllib.request.Request(GATEWAY, data=body, headers={'Content-Type': 'application/x-www-form-urlencoded;charset=UTF8'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 'EXC:' + str(e)[:200]

if __name__ == '__main__':
    print(call('acs.bill.create', {}))
