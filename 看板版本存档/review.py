# -*- coding: utf-8 -*-
"""最终复审：校验 index.html 引用的数据路径与函数都在位。"""
import re, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
html = (ROOT / "传天羽经营看板V6" / "templates" / "index.html").read_text(encoding="utf-8")
data = json.loads((ROOT / "传天羽经营看板V6" / "data.json").read_text(encoding="utf-8"))
METHODS = {"slice", "filter", "length", "map", "join", "forEach", "sort", "reduce", "indexOf", "includes", "concat", "push", "shift", "reverse", "flatMap", "find", "textContent", "padStart", "trim", "toFixed", "slice(0"}

errors = []

# 1) 函数引用
funcs = set(re.findall(r"function\s+([a-zA-Z_$][\w$]*)", html))
onclick = set(re.findall(r"onclick=\"([a-zA-Z_$][\w$]*)\(", html))
for f in sorted(onclick):
    if f not in funcs:
        errors.append(f"onclick 引用了未定义函数: {f}")

# 2) 数据路径：链上只要有一个前缀存在即视为有效（方法后缀忽略）
paths = set()
for m in re.finditer(r"\bd\.([a-zA-Z_$][\w$]*(?:\.[a-zA-Z_$][\w$]*)*)", html):
    parts = [p for p in m.group(1).split(".") if p not in METHODS and not p.startswith("slice")]
    paths.add(".".join(parts))
def resolve_prefix(chain):
    node = data
    for part in chain.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return False
    return True
for p in sorted(paths):
    if not resolve_prefix(p):
        errors.append(f"数据路径不存在: d.{p}")

# 3) 列分组 + salespersons
for plate, key in (("apr", "apr"), ("apple", "apple_ec"), ("shure", "shure_ec")):
    cols = data["columns"].get(plate)
    if not cols:
        errors.append(f"columns 缺少板块: {plate}"); continue
    for g in ("sales", "inventory", "analysis", "kpi", "process", "fees", "profit", "other"):
        if g not in cols:
            errors.append(f"columns.{plate} 缺少分组: {g}")
    for store in data.get(key, {}).get("stores", []):
        if not store.get("salespersons"):
            errors.append(f"{plate} 门店缺少 salespersons: {store.get('name')}")

for key in ("product_mix", "product_insight", "mgmt_tiles", "items", "risks"):
    if key not in data:
        errors.append(f"data 缺少: {key}")
if not data["inventory"]["cover_warning"]:
    errors.append("inventory.cover_warning 为空")
if not data["ppp"]:
    errors.append("ppp 为空")

print("checked data paths:", len(paths), "| handlers:", sorted(onclick))
if errors:
    print("ERRORS:")
    for e in errors: print(" -", e)
else:
    print("ALL CHECKS PASSED")
