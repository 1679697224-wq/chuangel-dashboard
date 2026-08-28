# -*- coding: utf-8 -*-
"""传天羽经营看板 · 登录权限系统（纯标准库，无第三方依赖）
运行：python app.py  (端口 8003，看板已内置 fetch /api/data 自动加载)
角色：boss老板 / finance财务 / hr人事 / aprAPR负责人 / apple苹果电商负责人 / shure舒尔负责人
"""
import os, json, hmac, hashlib, time, base64, secrets, re, io, zipfile, mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, 'static')
DATA_DIR = os.path.join(BASE, 'data')
UPLOAD_DIR = os.path.join(DATA_DIR, 'upload')
SECRET_FILE = os.path.join(BASE, 'secret.key')
if os.path.exists(SECRET_FILE):
    SECRET = open(SECRET_FILE, 'rb').read()
else:
    SECRET = secrets.token_bytes(32)
    open(SECRET_FILE, 'wb').write(SECRET)
for d in (DATA_DIR, UPLOAD_DIR):
    os.makedirs(d, exist_ok=True)

USERS = json.load(open(os.path.join(BASE, 'users.json'), encoding='utf-8'))

ROLE_META = {
  'boss':    {'name': '老板',          'sections': ['简报', '经营', '管理', '重点事项', '风险控制'], 'upload': []},
  'finance': {'name': '财务',          'sections': ['简报-费用', '简报-利润', '库存资金'], 'upload': ['fees', 'profit']},
  'hr':      {'name': '人事',          'sections': ['管理'], 'upload': []},
  'apr':     {'name': 'APR负责人',     'sections': ['经营-APR'], 'upload': ['apr_flow_conv', 'apr_targets']},
  'apple':   {'name': '苹果电商负责人','sections': ['经营-Apple电商'], 'upload': ['ae_flow']},
  'shure':   {'name': '舒尔负责人',    'sections': ['经营-Shure电商'], 'upload': ['sh_flow', 'sh_jd_daily']},
}

def h(s): return hashlib.sha256(s.encode()).hexdigest()
def sign_token(payload):
    raw = json.dumps(payload, sort_keys=True).encode()
    return base64.urlsafe_b64encode(raw).decode() + '.' + hmac.new(SECRET, raw, hashlib.sha256).hexdigest()[:16]
def verify_token(tok):
    try:
        b64, sig = tok.split('.')
        raw = base64.urlsafe_b64decode(b64.encode() + b'==')
        if hmac.new(SECRET, raw, hashlib.sha256).hexdigest()[:16] != sig: return None
        return json.loads(raw)
    except Exception:
        return None

def read_json(p, default):
    if not os.path.exists(p): return default
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return default
def write_json(p, obj):
    tmp = p + '.tmp'
    json.dump(obj, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.replace(tmp, p)

def get_upload(role):
    return read_json(os.path.join(DATA_DIR, role + '.json'), {})
def set_upload(role, obj):
    write_json(os.path.join(DATA_DIR, role + '.json'), obj)

def merge_live_data():
    d = {'apr': {'traffic_updated': False}, 'ecom': {}, 'targets': {}}
    u_apr = get_upload('apr')
    u_apple = get_upload('apple')
    u_shure = get_upload('shure')
    stores = {}
    for st, v in (u_apr.get('flow_conv') or {}).items():
        stores[st] = {'traffic': v.get('flow'), 'conv': v.get('conv')}
    if stores: d['apr']['stores'] = stores
    ae = {}
    for st, v in (u_apple.get('stores') or {}).items():
        ae[st] = {'uv': v.get('uv'), 'cvr': v.get('cvr'), 'refund': v.get('refund')}
    if ae: d['ecom']['ae'] = ae
    sh = {}
    for st, v in (u_shure.get('stores') or {}).items():
        sh[st] = {'uv': v.get('uv'), 'cvr': v.get('cvr'), 'sales': v.get('sales'), 'aov': v.get('aov')}
    if sh: d['ecom']['sh'] = sh
    return d

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def excel_serial(v):
    try:
        return (datetime(1899, 12, 30) + timedelta(days=float(v))).strftime('%Y-%m-%d')
    except Exception:
        return ''
def parse_xlsx(data):
    z = zipfile.ZipFile(io.BytesIO(data))
    ss = []
    try:
        sst = ET.fromstring(z.read('xl/sharedStrings.xml'))
        ss = [''.join(t.text or '' for t in si.findall('.//m:t', NS)) for si in sst.findall('m:si', NS)]
    except KeyError:
        pass
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    relmap = {rel.get('Id'): ('xl/' + rel.get('Target') if not rel.get('Target').startswith('/') else rel.get('Target')[1:]) for rel in rels}
    sheet0 = wb.find('m:sheets/m:sheet', NS)
    rid = sheet0.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
    root = ET.fromstring(z.read(relmap.get(rid, '')))
    rows = []
    for row in root.findall('.//m:row', NS):
        cells = []
        for c in row.findall('m:c', NS):
            t = c.get('t'); v = c.find('m:v', NS); isel = c.find('m:is', NS)
            if t == 's' and v is not None: val = ss[int(v.text)]
            elif v is not None: val = v.text
            elif isel is not None: val = ''.join(x.text or '' for x in isel.findall('.//m:t', NS))
            else: val = ''
            cells.append(str(val).strip())
        if any(cells): rows.append(cells)
    return rows

def summarize_daily(rows, date_col, sales_col, uv_col, orders_col):
    aug = {'sales': 0.0, 'uv': 0, 'orders': 0}
    for r in rows[2:]:
        if len(r) <= max(date_col, sales_col, uv_col, orders_col): continue
        d = excel_serial(r[date_col])
        if not d.startswith('2026-08'): continue
        def f(i):
            try: return float(r[i])
            except Exception: return 0.0
        aug['sales'] += f(sales_col); aug['uv'] += int(f(uv_col)); aug['orders'] += int(f(orders_col))
    return aug

def handle_upload_excel(role, filename, data):
    rows = parse_xlsx(data)
    if not rows: raise ValueError('无法解析 Excel（空文件）')
    if '天猫' in filename or '反馈表' in filename:
        day = {}
        for r in rows[2:]:
            for dc, sc, oc, uc in ((1, 2, 4, 11), (0, 1, 3, 10)):
                if len(r) <= max(dc, sc, oc, uc):
                    continue
                d = excel_serial(r[dc])
                if not (d.startswith('2026-08') and d[8:10] <= '27'):
                    continue
                def f(i):
                    try: return float(r[i])
                    except Exception: return 0.0
                day[d] = (f(sc), f(oc), int(f(uc)))
                break
        if not day:
            raise ValueError('未找到 8/1-27 数据（模板格式有变？）')
        sales = sum(v[0] for v in day.values())
        orders = sum(v[1] for v in day.values())
        uv = sum(v[2] for v in day.values())
        cur = get_upload('shure')
        stores = dict(cur.get('stores') or {})
        st = {'uv': uv, 'orders': orders}
        if uv: st['cvr'] = round(orders / uv * 100, 2)
        stores['天猫旗舰店'] = st
        cur['stores'] = stores
        cur['last_upload'] = datetime.now().isoformat(timespec='seconds')
        set_upload('shure', cur)
        return '天猫舒尔：8/1-27 平台口径销售 %.2f 万 / uv %d / 单 %d（看板销售以吉客云为准）' % (sales/10000, uv, orders)
    if '京东' in filename:
        for r in rows[3:]:
            hit = [i for i, x in enumerate(r) if x == '汇总']
            if hit:
                v = r[hit[0]+1:]
                if len(v) <= 9: raise ValueError('京东日报汇总行字段不足')
                vals = {'sales': float(v[0]), 'conv': float(v[1])*100, 'orders': float(v[2]), 'aov': float(v[3]), 'pv': float(v[8]), 'uv': float(v[9])}
                cur = get_upload('shure')
                stores = dict(cur.get('stores') or {})
                stores['京东旗舰店'] = {'uv': int(vals['uv']), 'sales': round(vals['sales'], 2), 'conv': round(vals['conv'], 2), 'aov': round(vals['aov'], 2), 'orders': int(vals['orders'])}
                cur['stores'] = stores
                cur['last_upload'] = datetime.now().isoformat(timespec='seconds')
                set_upload('shure', cur)
                return '京东舒尔：8月销售 %.2f 万 / uv %d / 单 %d' % (vals['sales']/10000, vals['uv'], vals['orders'])
    raise ValueError('未识别模板：文件名需含“天猫/反馈表”或“京东”')

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *a): pass
    def _send(self, code, body, ctype='text/html; charset=utf-8', extra=None):
        if isinstance(body, str): body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)
    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False), 'application/json; charset=utf-8')
    def _session(self):
        c = self.headers.get('Cookie', '')
        m = re.search(r'sess=([^;]+)', c)
        return verify_token(m.group(1)) if m else None
    def _read_body(self):
        ln = int(self.headers.get('Content-Length', 0) or 0)
        return self.rfile.read(ln) if ln else b''
    def _read_multipart(self, body, boundary):
        parts = {}
        for chunk in body.split(('--' + boundary).encode()):
            if b'Content-Disposition' not in chunk: continue
            head, _, content = chunk.partition(b'\r\n\r\n')
            m = re.search(rb'name="([^"]+)"', head)
            if not m: continue
            name = m.group(1).decode()
            fm = re.search(rb'filename="([^"]+)"', head)
            parts[name] = (fm.group(1).decode() if fm else None, content.rstrip(b'\r\n'))
        return parts
    def do_GET(self):
        u = urlparse(self.path); p = u.path; q = parse_qs(u.query)
        sess = self._session()
        if p in ('/', '/login.html'):
            if sess:
                self._redirect('/portal.html')
            else:
                self._send(200, open(os.path.join(STATIC, 'login.html'), encoding='utf-8').read())
        elif p == '/portal.html':
            if not sess: self._redirect('/'); return
            html = open(os.path.join(STATIC, 'portal.html'), encoding='utf-8').read()
            html = html.replace('__ROLE__', json.dumps({'username': sess['u'], 'role': sess['r'], 'name': USERS[sess['u']]['name'], 'meta': ROLE_META[sess['r']]}, ensure_ascii=False))
            self._send(200, html)
        elif p == '/board':
            role = (q.get('role') or ['boss'])[0]
            if not sess or sess['r'] != role:
                self._redirect('/'); return
            fname = 'shure-dashboard-v6.html' if role == 'shure' else 'boss-dashboard-v6.html'
            dash = open(os.path.join(BASE, fname), encoding='utf-8').read()
            dash = dash.replace('loadLiveData();', 'loadLiveData(); window.__ROLE__=' + json.dumps(role, ensure_ascii=False) + '; filterByRole(window.__ROLE__);')
            self._send(200, dash)
        elif p == '/api/me':
            if not sess: self._json({'error': '未登录'}, 401); return
            self._json({'username': sess['u'], 'role': sess['r'], 'name': USERS[sess['u']]['name'], 'meta': ROLE_META[sess['r']]})
        elif p == '/api/data':
            self._send(200, json.dumps(merge_live_data(), ensure_ascii=False), 'application/json; charset=utf-8', {'Access-Control-Allow-Origin': '*'})
        elif p == '/api/board-data':
            self._json({'uploaded': {r: get_upload(r) for r in ROLE_META}, 'merged': merge_live_data()})
        elif p == '/api/logout':
            self._send(200, '<script>document.cookie="sess=;Max-Age=0;path=/";location.href="/";</script>')
        else:
            f = os.path.join(STATIC, p.lstrip('/'))
            if os.path.isfile(f):
                ct = mimetypes.guess_type(f)[0] or 'application/octet-stream'
                self._send(200, open(f, 'rb').read(), ct)
            else:
                self._send(404, 'not found')
    def _redirect(self, loc):
        self.send_response(302); self.send_header('Location', loc); self.send_header('Content-Length', '0'); self.end_headers()
    def do_POST(self):
        u = urlparse(self.path); p = u.path
        sess = self._session()
        if p == '/api/login':
            try:
                body = json.loads(self._read_body().decode('utf-8'))
                uname = body.get('username', '').strip(); pwd = body.get('password', '')
                us = USERS.get(uname)
                if not us or h(pwd + us['salt']) != us['hash']:
                    self._json({'error': '账号或密码错误'}, 401); return
                tok = sign_token({'u': uname, 'r': us['role'], 'ts': int(time.time())})
                self._send(200, json.dumps({'ok': True, 'role': us['role'], 'name': us['name']}, ensure_ascii=False), 'application/json; charset=utf-8',
                           {'Set-Cookie': 'sess=%s; Path=/; HttpOnly; Max-Age=43200' % tok})
            except Exception as e:
                self._json({'error': '请求错误: %s' % e}, 400)
            return
        if not sess: self._json({'error': '未登录'}, 401); return
        role = sess['r']
        if p == '/api/change-password':
            try:
                body = json.loads(self._read_body().decode('utf-8'))
                oldp = body.get('old', ''); newp = body.get('new', '')
                if len(newp) < 8: self._json({'error': '新密码至少 8 位'}, 400); return
                us = USERS.get(sess['u'])
                if not us or h(oldp + us['salt']) != us['hash']:
                    self._json({'error': '原密码错误'}, 401); return
                us['salt'] = secrets.token_hex(8); us['hash'] = h(newp + us['salt']); us['changed'] = datetime.now().isoformat(timespec='seconds')
                write_json(os.path.join(BASE, 'users.json'), USERS)
                self._json({'ok': True, 'msg': '密码已修改'})
            except Exception as e:
                self._json({'error': str(e)}, 400)
            return
        if p == '/api/upload':
            try:
                body = json.loads(self._read_body().decode('utf-8'))
                data = body.get('data', {})
                cur = get_upload(role)
                def deep_merge(a, b):
                    for k, v in b.items():
                        if isinstance(v, dict) and isinstance(a.get(k), dict):
                            deep_merge(a[k], v)
                        else:
                            a[k] = v
                deep_merge(cur, data)
                cur['last_upload'] = datetime.now().isoformat(timespec='seconds')
                cur['uploader'] = sess['u']
                set_upload(role, cur)
                self._json({'ok': True, 'saved': cur})
            except Exception as e:
                self._json({'error': str(e)}, 400)
            return
        if p == '/api/upload-excel':
            try:
                ct = self.headers.get('Content-Type', '')
                m = re.search(r'boundary=([^;]+)', ct)
                if not m: self._json({'error': '需要 multipart'}, 400); return
                parts = self._read_multipart(self._read_body(), m.group(1).strip('"'))
                fn, data = parts.get('file', (None, None))
                if not data: self._json({'error': '缺少文件'}, 400); return
                msg = handle_upload_excel(role, fn or 'file.xlsx', data)
                self._json({'ok': True, 'msg': msg})
            except Exception as e:
                self._json({'error': str(e)}, 400)
            return
        self._json({'error': '未知接口'}, 404)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8003))
    print('登录系统启动 http://0.0.0.0:%d' % port)
    ThreadingHTTPServer(('0.0.0.0', port), Handler).serve_forever()
