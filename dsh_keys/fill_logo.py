# -*- coding: utf-8 -*-
import io, base64
P = "/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html"
src = io.open(P, encoding="utf-8").read()
b64 = base64.b64encode(open("/Users/lili/Desktop/deepseek harness/dsh_keys/logo_cty.png", 'rb').read()).decode()
REPS = []
def R(old, new, expect=1, name=""):
    REPS.append((old, new, expect, name))
print('logo base64 len:', len(b64))
R(".chart-area{padding:20px 22px 34px;height:260px;display:flex;align-items:flex-end;gap:15px;position:relative;background:linear-gradient(180deg,transparent 0 92%,#e4eaf1 92%)}", ".chart-area{padding:20px 22px 34px;height:260px;display:flex;align-items:flex-end;gap:15px;position:relative;background:transparent}", 1, '图表基线阴影')
R("<link rel=\"icon\" href=\"data:,\" />", "<link rel=\"icon\" href=\"data:image/png;base64," + b64 + "\" />", 1, 'favicon')
R(".brand .b-logo{display:flex;align-items:center;gap:11px}", "", 1, '删除b-logo flex')
R(".brand .b-mark{width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,#2f69c2,#173e70);display:grid;place-items:center;font-size:20px;font-weight:900;letter-spacing:.5px;box-shadow:0 6px 16px rgba(0,0,0,.25)}", ".b-logo-img{display:block;width:100%;height:auto;max-height:64px;object-fit:contain;margin:2px 0 10px}", 1, 'brand CSS logo')
R(".brand .b-name{font-size:19px;font-weight:800;letter-spacing:1px}", "", 1, '删除b-name')
R(".brand .b-name small{display:block;font-size:10.5px;color:#94aac2;letter-spacing:2.4px;font-weight:700;margin-top:3px}", "", 1, '删除b-name small')
R("      <div class=\"b-logo\"><span class=\"b-mark\">C</span><span class=\"b-name\">传天羽<small>CHUANGEL · BOSS VIEW</small></span></div>", "      <img class=\"b-logo-img\" src=\"data:image/png;base64," + b64 + "\" alt=\"传天羽 Chuangel\">", 1, 'brand 标记')
ok = True
for old, new, expect, name in REPS:
    n = src.count(old)
    if n != expect:
        print("MISS/COUNT[%s]: expected %d, got %d" % (name, expect, n))
        ok = False
    else:
        src = src.replace(old, new)
        print("ok  [%s]" % name)
io.open(P, "w", encoding="utf-8").write(src)
print(); print('LOGO+阴影 done, ok =', ok)