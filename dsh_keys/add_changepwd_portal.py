# -*- coding: utf-8 -*-
import io
P = "/Users/lili/Desktop/deepseek harness/登录权限系统/static/portal.html"
src = io.open(P, encoding='utf-8').read()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
R("<div class=\"u\" id=\"userInfo\"></div>", "<div class=\"u\" id=\"userInfo\"></div><a href=\"javascript:changePwd()\" style=\"color:#9fe3c8;font-size:12.5px;margin-left:14px\">修改密码</a>", 1, '改密入口')
R("document.getElementById('userInfo').textContent = ROLE.name + '（' + ROLE.username + '） · ' + ROLE.role;", "document.getElementById('userInfo').textContent = ROLE.name + '（' + ROLE.username + '） · ' + ROLE.role;\nfunction changePwd(){\n  var o = prompt('请输入原密码');\n  if(!o) return;\n  var n = prompt('请输入新密码（至少 8 位）');\n  if(!n || n.length < 8){ alert('新密码至少 8 位'); return; }\n  fetch('/api/change-password', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({old:o, new:n})})\n    .then(function(res){ return res.json().then(function(d){ return {ok: res.ok, d: d}; }); })\n    .then(function(r){ alert(r.ok ? '密码已修改 ✓' : (r.d.error || '修改失败')); })\n    .catch(function(){ alert('网络错误'); });\n}", 1, '改密函数')
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
print('PART10 done, ok =', ok)