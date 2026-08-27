# -*- coding: utf-8 -*-
"""传天羽经营看板 V6 · 版本快照存档
用法: python3 archive_version.py <版本标签> [备注]
把 传天羽经营看板V6 的当前源码打包成 zip 存入本目录，并登记到 版本清单.md。
"""
import sys, zipfile, json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # workspace root
SRC = ROOT / "传天羽经营看板V6"
DST = ROOT / "看板版本存档"

label = sys.argv[1] if len(sys.argv) > 1 else "未命名版本"
note = sys.argv[2] if len(sys.argv) > 2 else ""
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
fname = f"传天羽经营看板V6_{stamp}_{label}.zip"
DST.mkdir(exist_ok=True)

exclude_dirs = {"deploy"}
with zipfile.ZipFile(DST / fname, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(SRC.rglob("*")):
        if p.is_dir() or any(part in exclude_dirs for part in p.relative_to(SRC).parts):
            continue
        z.write(p, p.relative_to(SRC))

manifest = DST / "版本清单.md"
entries = []
if manifest.exists():
    entries = manifest.read_text(encoding="utf-8").splitlines()
    entries.append("")
entries.append(f"- {stamp} | {label} | {fname} | {note}")
manifest.write_text("\n".join(entries) + "\n", encoding="utf-8")

print("saved:", DST / fname)
print("manifest entries:", len(entries))
