import io, re
html = io.open('/tmp/dom_inv.html', encoding='utf-8').read()
print('库龄结构渲染:', '库龄结构' in html)
print('高库龄预警:', '高库龄预警' in html)
print('周转17.9:', '17.9' in html)
print('pie3d放大:', 'width:290px' in html)
print('无错码monthlyNote明文:', '<span style="color' not in html.replace('<span style="color:#9aa8b8;font-size:11px">仅月度口径',''))
print('综合费率vs预算项:', '综合费率 vs 预算' in html)