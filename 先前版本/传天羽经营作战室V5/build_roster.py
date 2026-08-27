#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析花名册 → roster.json（仅非敏感字段，供销售员详情展示）"""
import json, os
from datetime import datetime, timedelta
import xlrd

SRC = os.path.expanduser("~/Desktop/江苏传天羽网络股份有限公司在职员工20260811.xls")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "roster.json")

def d2s(v):
    if isinstance(v, (int, float)) and v > 10000:
        try:
            return (datetime(1899, 12, 30) + timedelta(days=int(v))).strftime("%Y-%m-%d")
        except Exception:
            return ""
    return str(v).strip()[:10] if v else ""

wb = xlrd.open_workbook(SRC)
ws = wb.sheet_by_index(0)

def clean_rank(pos):
    """从花名册职位提取标准职级：店员/店长/代理店长/Coach讲师"""
    p = str(pos or "").lower()
    if "店长" in p:
        return "代理店长" if "代理" in p else "店长"
    if "代理" in p:
        return "代理店长"
    if "coach" in p or "讲师" in p or "私教" in p:
        return "Coach讲师"
    if "店员" in p:
        return "店员"
    return str(pos or "店员").strip()[:10] or "店员"

roster = {}
for i in range(1, ws.nrows):
    r = [ws.cell_value(i, j) for j in range(ws.ncols)]
    name = str(r[1] or "").strip()
    if not name:
        continue
    pos = str(r[12] or "").strip()
    roster[name] = {
        "name": name,
        "store": str(r[7] or "").strip(),       # 4级部门 = 门店
        "pos": pos,
        "rank": clean_rank(pos),
        "store_apple_id": str(r[13] or "").strip(),
        "hire_date": d2s(r[18]),
        "tenure": str(r[19] or "").strip(),
        "emp_type": str(r[22] or "").strip(),
        "emp_status": str(r[23] or "").strip(),
        "probation": str(r[24] or "").strip(),
        "regular_date": d2s(r[25]),
        "level": str(r[26] or "").strip(),
        "age": str(r[32] or "").strip(),
        "gender": str(r[33] or "").strip(),
        "first_work": d2s(r[41]),
        "work_years": str(r[42] or "").strip(),
        "edu": str(r[51] or "").strip(),
        "school": str(r[52] or "").strip(),
        "grad_date": d2s(r[53]),
        "major": str(r[54] or "").strip(),
        "contract_co": str(r[59] or "").strip(),
        "contract_type": str(r[60] or "").strip(),
        "contract_term": str(r[67] or "").strip(),
    }

with open(OUT, "w") as f:
    json.dump(roster, f, ensure_ascii=False, indent=1)

print("roster.json 生成:", len(roster), "人")
# 验证TOP5
for n in ["王畅", "鲁健", "袁兆行", "田国伟", "蒋玉玄"]:
    p = roster.get(n)
    if p:
        print(f"✅ {n}: {p['store']} | {p['edu']} {p['school']} {p['major']} | 入职{p['hire_date']} | 工龄{p['work_years']}")
    else:
        print(f"❌ {n}: 花名册未找到")
