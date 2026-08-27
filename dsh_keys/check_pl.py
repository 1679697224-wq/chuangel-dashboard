import io, re
src = io.open('/Users/lili/Desktop/deepseek harness/老板确认看板/boss-dashboard-v6.html', encoding='utf-8').read()
# 找出使用 pl 但未定义 const pl 的函数
funcs = re.split(r'(?=function )', src)
for f in funcs[1:]:
    m = re.match(r'function (\w+)', f)
    if not m: continue
    name = m.group(1)
    if "'+pl+'" in f or "' + pl + '" in f or '${pl}' in f or "'（'+pl+'）'" in f:
        has_pl = 'const pl = PERIOD_LABEL' in f or 'const pl=' in f
        if not has_pl:
            print('WARN 使用pl未定义:', name)
print('检查完成')