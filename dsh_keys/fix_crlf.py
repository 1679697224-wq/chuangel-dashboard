import io
P='/Users/lili/Desktop/deepseek harness/登录权限系统/app.py'
src=io.open(P,encoding='utf-8').read()
CR=chr(13); LF=chr(10); BS=chr(92)
old1 = "partition(b'" + CR + LF + CR + LF + "')"
new1 = "partition(b'" + BS + 'r' + BS + 'n' + BS + 'r' + BS + 'n' + "')"
src = src.replace(old1, new1)
old2 = "content.rstrip(b'" + CR + LF + "')"
new2 = "content.rstrip(b'" + BS + 'r' + BS + 'n' + "')"
src = src.replace(old2, new2)
io.open(P,'w',encoding='utf-8').write(src)
print('fixed ok, partition 出现:', src.count('partition(b\\r\\n\\r\\n)'), ' rstrip 出现:', src.count('rstrip(b\\r\\n)'))