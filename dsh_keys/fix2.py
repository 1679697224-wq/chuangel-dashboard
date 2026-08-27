import io
P='/Users/lili/Desktop/deepseek harness/登录权限系统/app.py'
src=io.open(P,encoding='utf-8',newline='').read()
LF=chr(10); BS=chr(92)
old1 = "partition(b'" + LF + LF + "')"
new1 = "partition(b'" + BS + 'r' + BS + 'n' + BS + 'r' + BS + 'n' + "')"
n1 = src.count(old1)
src = src.replace(old1, new1)
old2 = "content.rstrip(b'" + LF + "')"
new2 = "content.rstrip(b'" + BS + 'r' + BS + 'n' + "')"
n2 = src.count(old2)
src = src.replace(old2, new2)
io.open(P,'w',encoding='utf-8',newline='').write(src)
print('partition 修复:', n1, ' rstrip 修复:', n2)
# 再确认没有遗留裸换行字符串
import re
bad = re.findall(r"b'\n[^']*'\n", src[:2000])
print('遗留可疑:', len(bad))