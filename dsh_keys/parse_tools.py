import json
for path, label in [('/tmp/sub.json', '== 已订阅工具（appKey 90871460）=='), ('/tmp/tl1.json', '== 公开工具目录 ==')]:
    d = json.load(open(path, encoding='utf-8'))
    rows = d['result']['data']
    print(label, '数量:', len(rows))
    for r in rows:
        print(f"  {r.get('toolNameCn',''):<16} | {r.get('mcpToolMethod') or r.get('methodName',''):<40} | {r.get('toolName','')}")
    print()
