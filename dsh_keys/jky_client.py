# -*- coding: utf-8 -*-
"""吉客云(JackYun) API 客户端 - 签名算法用真实网关验证"""
import hashlib, json, time, urllib.request, urllib.parse

APPKEY = "90871460"
APPSECRET = "4e0ca84911ab48aeb2cccad89587222f"
GATEWAY = "https://open.jackyun.com/open/openapi/do"

def md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def sign_v1(params, secret):
    """聚水潭风格：按 key 排序，key+value 拼接，末尾加 secret，MD5 大写"""
    s = ''.join(k + str(params[k]) for k in sorted(params))
    return md5(s + secret).upper()

def sign_v2(params, secret):
    """同 V1 但小写"""
    return md5(''.join(k + str(params[k]) for k in sorted(params)) + secret)

def sign_v3(params, secret):
    """不排序，按固定顺序拼接（method,appkey,version,contenttype,timestamp,bizcontent）"""
    order = ['method', 'appkey', 'version', 'contenttype', 'timestamp', 'bizcontent']
    s = ''.join(k + str(params[k]) for k in order if k in params)
    return md5(s + secret).upper()

def call(method, bizcontent, signer, extra_params=None):
    params = {
        'method': method,
        'appkey': APPKEY,
        'version': '1.0',
        'contenttype': 'json',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'bizcontent': json.dumps(bizcontent, ensure_ascii=False),
    }
    if extra_params:
        params.update(extra_params)
    params['sign'] = signer(params, APPSECRET)
    body = urllib.parse.urlencode(params).encode('utf-8')
    req = urllib.request.Request(GATEWAY, data=body, headers={'Content-Type': 'application/x-www-form-urlencoded;charset=UTF8'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode('utf-8', 'replace')[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:500]
    except Exception as e:
        return -1, str(e)[:300]

if __name__ == '__main__':
    # 用一个简单方法测试：货品档案详情查询（来自 qliang 文档）
    test = {'method': 'erp.vend.create', 'biz': {}}
    for name, fn in [('V1排序大写', sign_v1), ('V2排序小写', sign_v2), ('V3固定序大写', sign_v3)]:
        code, body = call('erp.vend.create', {}, fn)
        print(f'--- {name}: HTTP {code}')
        print(body[:400])
