# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/登录权限系统/app.py"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("        if not sess: self._json({'error': '未登录'}, 401); return\n        role = sess['r']", "        if not sess: self._json({'error': '未登录'}, 401); return\n        role = sess['r']\n        if p == '/api/change-password':\n            try:\n                body = json.loads(self._read_body().decode('utf-8'))\n                oldp = body.get('old', ''); newp = body.get('new', '')\n                if len(newp) < 8: self._json({'error': '新密码至少 8 位'}, 400); return\n                us = USERS.get(sess['u'])\n                if not us or h(oldp + us['salt']) != us['hash']:\n                    self._json({'error': '原密码错误'}, 401); return\n                us['salt'] = secrets.token_hex(8); us['hash'] = h(newp + us['salt']); us['changed'] = datetime.now().isoformat(timespec='seconds')\n                write_json(os.path.join(BASE, 'users.json'), USERS)\n                self._json({'ok': True, 'msg': '密码已修改'})\n            except Exception as e:\n                self._json({'error': str(e)}, 400)\n            return", 1, '改密接口')
ok = True
for old, new, expect, name in REPS:
    n = src.count(old)
    if n != expect:
        print("MISS/COUNT[%s]: expected %d, got %d" % (name, expect, n))
        ok = False
    else:
        src = src.replace(old, new)
        print("ok  [%s]" % name)
io.open(P, 'w', encoding='utf-8').write(src)
print('PART9 done, ok =', ok)