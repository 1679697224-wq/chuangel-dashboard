import io, re
html = io.open('/tmp/dom_apr2.html', encoding='utf-8').read()
print('section-block 数:', html.count('section-block'))
print('shell 内是否有 门店经营对比:', '门店经营对比' in html)
print('shell 内是否有 月度目标达成:', '月度目标达成' in html)
# 看 section-block 附近的文本
i = html.find('section-block')
print('第一个 section-block 上下文:', html[i-80:i+120].replace('\n',' ')[:200])
# 是否有 alert-strip 渲染
print('alert-strip:', html.count('alert-strip'))
# 检查是否存在 JS 错误痕迹（dump 里 script 源码 vs 渲染）
print('goalCard:', 'goal-card' in html)